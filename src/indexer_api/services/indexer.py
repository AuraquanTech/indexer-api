"""
Core indexing service - wraps the file system indexing logic.
This is the heart of the application, connecting the API to the indexing engines.
"""
import asyncio
import fnmatch
import hashlib
import mimetypes
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from indexer_api.core.config import settings
from indexer_api.core.logging import get_logger
from indexer_api.db.models import (
    FileIndex,
    IndexedFile,
    IndexJob,
    JobStatus,
    JobType,
    Organization,
)
from indexer_api.schemas.index import (
    FileIndexCreate,
    FileIndexStats,
    IndexedFileSearch,
    IndexJobProgress,
)

logger = get_logger(__name__)


class IndexerService:
    """Service for file indexing operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._executor = ThreadPoolExecutor(max_workers=settings.max_concurrent_jobs)

    # ========================================================================
    # Index CRUD
    # ========================================================================

    async def create_index(
        self,
        org_id: str,
        index_data: FileIndexCreate,
    ) -> FileIndex:
        """Create a new file index."""
        # Validate root path - prevent path traversal attacks
        root_path = Path(index_data.root_path).resolve()

        # Block sensitive system paths
        blocked_paths = [
            Path("C:/Windows").resolve(),
            Path("C:/Program Files").resolve(),
            Path("C:/Program Files (x86)").resolve(),
            Path("/etc").resolve(),
            Path("/root").resolve(),
            Path("/var").resolve(),
            Path("/usr").resolve(),
        ]

        for blocked in blocked_paths:
            try:
                if root_path == blocked or blocked in root_path.parents:
                    raise ValueError(f"Access denied: Cannot index system path {root_path}")
            except (ValueError, OSError):
                pass  # Path doesn't exist or can't be resolved

        if not root_path.exists():
            raise ValueError(f"Path does not exist: {root_path}")

        if not root_path.is_dir():
            raise ValueError(f"Path is not a directory: {root_path}")

        # Check org limits
        org = await self._get_org(org_id)
        current_count = await self._count_indexes(org_id)

        if current_count >= org.max_indexes:
            raise ValueError(
                f"Organization limit reached: {org.max_indexes} indexes allowed"
            )

        # Create index
        index = FileIndex(
            organization_id=org_id,
            name=index_data.name,
            description=index_data.description,
            root_path=index_data.root_path,
            include_patterns=index_data.include_patterns,
            exclude_patterns=index_data.exclude_patterns,
            max_depth=index_data.max_depth,
            compute_hashes=index_data.compute_hashes,
        )
        self.db.add(index)
        await self.db.flush()

        logger.info("created_index", index_id=index.id, name=index.name, org_id=org_id)
        return index

    async def get_index(self, org_id: str, index_id: str) -> FileIndex | None:
        """Get an index by ID."""
        result = await self.db.execute(
            select(FileIndex)
            .where(FileIndex.id == index_id)
            .where(FileIndex.organization_id == org_id)
        )
        return result.scalar_one_or_none()

    async def list_indexes(self, org_id: str) -> list[FileIndex]:
        """List all indexes for an organization."""
        result = await self.db.execute(
            select(FileIndex)
            .where(FileIndex.organization_id == org_id)
            .where(FileIndex.is_active == True)
            .order_by(FileIndex.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_index(self, org_id: str, index_id: str) -> bool:
        """Delete an index and all its files."""
        index = await self.get_index(org_id, index_id)
        if not index:
            return False

        # Cascade delete handled by DB
        await self.db.delete(index)
        await self.db.flush()

        logger.info("deleted_index", index_id=index_id)
        return True

    # ========================================================================
    # Indexing Jobs
    # ========================================================================

    async def start_index_job(
        self,
        org_id: str,
        index_id: str,
        user_id: str,
        job_type: JobType = JobType.FULL_SCAN,
    ) -> IndexJob:
        """Start a new indexing job."""
        index = await self.get_index(org_id, index_id)
        if not index:
            raise ValueError("Index not found")

        # Create job record
        job = IndexJob(
            index_id=index_id,
            created_by_id=user_id,
            job_type=job_type,
            status=JobStatus.PENDING,
        )
        self.db.add(job)
        await self.db.flush()

        logger.info("created_job", job_id=job.id, index_id=index_id, job_type=job_type)
        return job

    async def run_index_job(self, job_id: str) -> None:
        """
        Execute an indexing job. This is the main indexing logic.
        Called by the background worker.
        """
        # Get job and index
        result = await self.db.execute(
            select(IndexJob).where(IndexJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        result = await self.db.execute(
            select(FileIndex).where(FileIndex.id == job.index_id)
        )
        index = result.scalar_one_or_none()
        if not index:
            raise ValueError(f"Index {job.index_id} not found")

        # Update job status
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        await self.db.flush()

        try:
            # Clear existing files if full scan
            if job.job_type == JobType.FULL_SCAN:
                await self.db.execute(
                    delete(IndexedFile).where(IndexedFile.index_id == index.id)
                )

            # CRITICAL: Commit and release async session before sync operations
            # This prevents SQLite "database is locked" errors
            await self.db.commit()

            # Run the indexing in a thread pool (uses its own sync session)
            loop = asyncio.get_event_loop()
            file_count, dir_count, total_size = await loop.run_in_executor(
                self._executor,
                self._index_directory_sync,
                index,
                job,
            )

            # Re-fetch objects after sync operations (they may be stale)
            await self.db.refresh(index)
            await self.db.refresh(job)

            # Update index stats
            index.total_files = file_count
            index.total_directories = dir_count
            index.total_size_bytes = total_size
            index.last_indexed_at = datetime.now(timezone.utc)

            # Complete job
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            job.progress_percent = 100.0

            await self.db.flush()
            logger.info(
                "job_completed",
                job_id=job_id,
                files=file_count,
                directories=dir_count,
                size_bytes=total_size,
            )

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            await self.db.flush()

            logger.error("job_failed", job_id=job_id, error=str(e))
            raise

    def _index_directory_sync(
        self,
        index: FileIndex,
        job: IndexJob,
    ) -> tuple[int, int, int]:
        """
        Synchronous directory indexing.
        Uses os.scandir for efficiency (similar to Windows API approach).
        """
        root_path = Path(index.root_path)
        if not root_path.exists():
            raise ValueError(f"Path does not exist: {root_path}")

        files_to_add: list[IndexedFile] = []
        file_count = 0
        dir_count = 0
        total_size = 0

        def should_include(path: Path) -> bool:
            """Check if path matches include/exclude patterns."""
            path_str = str(path)

            # Check excludes first
            for pattern in index.exclude_patterns:
                if fnmatch.fnmatch(path_str, pattern):
                    return False
                if fnmatch.fnmatch(path.name, pattern):
                    return False

            # Check includes
            if index.include_patterns and index.include_patterns != ["*"]:
                for pattern in index.include_patterns:
                    if fnmatch.fnmatch(path_str, pattern):
                        return True
                    if fnmatch.fnmatch(path.name, pattern):
                        return True
                return False

            return True

        def scan_dir(path: Path, depth: int = 0) -> None:
            """Recursively scan directory."""
            nonlocal file_count, dir_count, total_size

            if index.max_depth and depth > index.max_depth:
                return

            try:
                with os.scandir(path) as entries:
                    for entry in entries:
                        try:
                            entry_path = Path(entry.path)

                            if not should_include(entry_path):
                                continue

                            stat = entry.stat(follow_symlinks=False)

                            if entry.is_dir(follow_symlinks=False):
                                dir_count += 1
                                # Recurse into directory
                                scan_dir(entry_path, depth + 1)
                            else:
                                file_count += 1
                                total_size += stat.st_size

                                # Create file record
                                indexed_file = self._create_file_record(
                                    index_id=index.id,
                                    path=entry_path,
                                    stat=stat,
                                    depth=depth,
                                    compute_hashes=index.compute_hashes,
                                )
                                files_to_add.append(indexed_file)

                                # Batch insert every 1000 files
                                if len(files_to_add) >= settings.index_chunk_size:
                                    self._batch_insert_files(files_to_add)
                                    files_to_add.clear()

                        except (PermissionError, OSError) as e:
                            logger.warning(
                                "file_access_error",
                                path=str(entry.path),
                                error=str(e),
                            )
                            continue

            except (PermissionError, OSError) as e:
                logger.warning("dir_access_error", path=str(path), error=str(e))

        # Start scanning
        scan_dir(root_path)

        # Insert remaining files
        if files_to_add:
            self._batch_insert_files(files_to_add)

        return file_count, dir_count, total_size

    def _create_file_record(
        self,
        index_id: str,
        path: Path,
        stat: os.stat_result,
        depth: int,
        compute_hashes: bool,
    ) -> IndexedFile:
        """Create an IndexedFile record from path and stat."""
        # Compute hashes if requested
        md5_hash = None
        sha256_hash = None

        if compute_hashes and stat.st_size < settings.max_file_size_mb * 1024 * 1024:
            try:
                md5_hash, sha256_hash = self._compute_hashes(path)
            except Exception:
                pass

        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(path))

        return IndexedFile(
            index_id=index_id,
            path=str(path),
            filename=path.name,
            extension=path.suffix.lower() if path.suffix else None,
            size_bytes=stat.st_size,
            created_time=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
            modified_time=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            accessed_time=datetime.fromtimestamp(stat.st_atime, tz=timezone.utc),
            md5_hash=md5_hash,
            sha256_hash=sha256_hash,
            mime_type=mime_type,
            is_directory=False,
            depth=depth,
        )

    def _compute_hashes(self, path: Path) -> tuple[str, str]:
        """Compute MD5 and SHA256 hashes for a file."""
        md5 = hashlib.md5()
        sha256 = hashlib.sha256()

        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                md5.update(chunk)
                sha256.update(chunk)

        return md5.hexdigest(), sha256.hexdigest()

    def _batch_insert_files(self, files: list[IndexedFile]) -> None:
        """Batch insert files into the database using sync engine."""
        if not files:
            return

        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session

        # Convert async URL to sync URL
        sync_url = settings.database_url.replace("+aiosqlite", "").replace("+asyncpg", "+psycopg2")
        if "sqlite" in sync_url and "+aiosqlite" not in settings.database_url:
            sync_url = sync_url.replace("sqlite://", "sqlite:///")

        # Configure SQLite for concurrent access
        connect_args = {}
        if "sqlite" in sync_url:
            connect_args = {
                "timeout": 30,  # Wait up to 30 seconds for lock
                "check_same_thread": False,
            }

        engine = create_engine(
            sync_url,
            connect_args=connect_args,
            isolation_level="AUTOCOMMIT",  # Reduces lock contention
        )

        # Enable WAL mode for SQLite (better concurrency)
        if "sqlite" in sync_url:
            with engine.connect() as conn:
                conn.execute(__import__('sqlalchemy').text("PRAGMA journal_mode=WAL"))
                conn.execute(__import__('sqlalchemy').text("PRAGMA busy_timeout=30000"))

        # Convert ORM objects to dicts for bulk insert
        file_dicts = []
        for f in files:
            file_dicts.append({
                "id": f.id if f.id else str(__import__('uuid').uuid4()),
                "index_id": f.index_id,
                "path": f.path,
                "filename": f.filename,
                "extension": f.extension,
                "size_bytes": f.size_bytes,
                "created_time": f.created_time,
                "modified_time": f.modified_time,
                "accessed_time": f.accessed_time,
                "md5_hash": f.md5_hash,
                "sha256_hash": f.sha256_hash,
                "mime_type": f.mime_type,
                "is_directory": f.is_directory,
                "depth": f.depth,
                "indexed_at": datetime.now(timezone.utc),
            })

        from sqlalchemy import insert
        from indexer_api.db.models import IndexedFile as IndexedFileModel
        import time as time_module

        # Retry logic for SQLite locking (development only)
        max_retries = 5
        for attempt in range(max_retries):
            try:
                with Session(engine) as session:
                    session.execute(insert(IndexedFileModel), file_dicts)
                    session.commit()
                break  # Success
            except Exception as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    logger.warning(
                        "database_locked_retry",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                    )
                    time_module.sleep(1 + attempt)  # Exponential backoff
                else:
                    raise

        engine.dispose()

    # ========================================================================
    # File Search & Queries
    # ========================================================================

    async def search_files(
        self,
        org_id: str,
        index_id: str,
        search: IndexedFileSearch,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[IndexedFile], int]:
        """Search for files in an index."""
        # Build query
        query = (
            select(IndexedFile)
            .join(FileIndex)
            .where(FileIndex.organization_id == org_id)
            .where(IndexedFile.index_id == index_id)
        )

        # Apply filters
        if search.query:
            # Escape SQL wildcards to prevent injection
            escaped_query = (
                search.query
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            query = query.where(
                IndexedFile.filename.ilike(f"%{escaped_query}%", escape="\\")
                | IndexedFile.path.ilike(f"%{escaped_query}%", escape="\\")
            )

        if search.extension:
            query = query.where(IndexedFile.extension == search.extension.lower())

        if search.extensions:
            query = query.where(
                IndexedFile.extension.in_([e.lower() for e in search.extensions])
            )

        if search.min_size is not None:
            query = query.where(IndexedFile.size_bytes >= search.min_size)

        if search.max_size is not None:
            query = query.where(IndexedFile.size_bytes <= search.max_size)

        if search.min_quality_score is not None:
            query = query.where(IndexedFile.quality_score >= search.min_quality_score)

        if search.modified_after:
            query = query.where(IndexedFile.modified_time >= search.modified_after)

        if search.modified_before:
            query = query.where(IndexedFile.modified_time <= search.modified_before)

        if search.is_directory is not None:
            query = query.where(IndexedFile.is_directory == search.is_directory)

        if search.path_prefix:
            query = query.where(IndexedFile.path.startswith(search.path_prefix))

        # Count total
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Apply ordering
        order_column = getattr(IndexedFile, search.order_by)
        if search.order_desc:
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column)

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        files = list(result.scalars().all())

        return files, total

    async def find_duplicates(
        self,
        org_id: str,
        index_id: str,
    ) -> list[dict[str, Any]]:
        """Find duplicate files by MD5 hash."""
        query = (
            select(
                IndexedFile.md5_hash,
                func.count(IndexedFile.id).label("count"),
                func.sum(IndexedFile.size_bytes).label("total_size"),
            )
            .join(FileIndex)
            .where(FileIndex.organization_id == org_id)
            .where(IndexedFile.index_id == index_id)
            .where(IndexedFile.md5_hash.isnot(None))
            .group_by(IndexedFile.md5_hash)
            .having(func.count(IndexedFile.id) > 1)
            .order_by(func.sum(IndexedFile.size_bytes).desc())
        )

        result = await self.db.execute(query)
        duplicates = []

        for row in result.all():
            # Get the actual files for each duplicate group
            files_result = await self.db.execute(
                select(IndexedFile)
                .where(IndexedFile.index_id == index_id)
                .where(IndexedFile.md5_hash == row.md5_hash)
            )
            files = list(files_result.scalars().all())

            duplicates.append({
                "hash": row.md5_hash,
                "file_count": row.count,
                "total_size_bytes": row.total_size,
                "files": files,
            })

        return duplicates

    async def get_index_stats(self, org_id: str, index_id: str) -> FileIndexStats | None:
        """Get detailed statistics for an index."""
        index = await self.get_index(org_id, index_id)
        if not index:
            return None

        # Extension breakdown
        ext_result = await self.db.execute(
            select(IndexedFile.extension, func.count(IndexedFile.id))
            .where(IndexedFile.index_id == index_id)
            .where(IndexedFile.extension.isnot(None))
            .group_by(IndexedFile.extension)
            .order_by(func.count(IndexedFile.id).desc())
            .limit(20)
        )
        extensions = {row[0]: row[1] for row in ext_result.all()}

        # Size distribution
        size_ranges = [
            ("tiny", 0, 1024),  # < 1KB
            ("small", 1024, 1024 * 100),  # 1KB - 100KB
            ("medium", 1024 * 100, 1024 * 1024),  # 100KB - 1MB
            ("large", 1024 * 1024, 1024 * 1024 * 100),  # 1MB - 100MB
            ("huge", 1024 * 1024 * 100, None),  # > 100MB
        ]

        size_distribution = {}
        for name, min_size, max_size in size_ranges:
            query = select(func.count(IndexedFile.id)).where(
                IndexedFile.index_id == index_id,
                IndexedFile.size_bytes >= min_size,
            )
            if max_size:
                query = query.where(IndexedFile.size_bytes < max_size)

            result = await self.db.execute(query)
            size_distribution[name] = result.scalar() or 0

        # Largest file
        largest_result = await self.db.execute(
            select(IndexedFile)
            .where(IndexedFile.index_id == index_id)
            .order_by(IndexedFile.size_bytes.desc())
            .limit(1)
        )
        largest = largest_result.scalar_one_or_none()

        # Calculate average file size
        avg_size = index.total_size_bytes / max(index.total_files, 1)

        # Format size
        def format_size(size_bytes: int) -> str:
            for unit in ["B", "KB", "MB", "GB", "TB"]:
                if size_bytes < 1024:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024
            return f"{size_bytes:.1f} PB"

        return FileIndexStats(
            index_id=index.id,
            total_files=index.total_files,
            total_directories=index.total_directories,
            total_size_bytes=index.total_size_bytes,
            total_size_human=format_size(index.total_size_bytes),
            extensions_breakdown=extensions,
            size_distribution=size_distribution,
            last_indexed_at=index.last_indexed_at,
            avg_file_size=avg_size,
            largest_file={
                "path": largest.path,
                "size_bytes": largest.size_bytes,
                "filename": largest.filename,
            } if largest else None,
        )

    # ========================================================================
    # Helpers
    # ========================================================================

    async def _get_org(self, org_id: str) -> Organization:
        """Get organization or raise."""
        result = await self.db.execute(
            select(Organization).where(Organization.id == org_id)
        )
        org = result.scalar_one_or_none()
        if not org:
            raise ValueError("Organization not found")
        return org

    async def _count_indexes(self, org_id: str) -> int:
        """Count active indexes for an organization."""
        result = await self.db.execute(
            select(func.count(FileIndex.id))
            .where(FileIndex.organization_id == org_id)
            .where(FileIndex.is_active == True)
        )
        return result.scalar() or 0
