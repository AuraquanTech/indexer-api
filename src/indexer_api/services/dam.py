"""
Digital Asset Management (DAM) service.
Analyzes and categorizes media files with metadata extraction.
"""
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from indexer_api.core.config import settings
from indexer_api.db.models import AssetType, FileIndex, IndexedFile, IndexJob, JobStatus, JobType
from indexer_api.schemas.dam import (
    DAMAssetResponse,
    DAMMetadata,
    DAMSearch,
    DAMStats,
    ExifData,
    AudioMetadata,
    DocumentMetadata,
)

logger = structlog.get_logger()

# File extension mappings
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp", ".svg", ".ico", ".heic", ".heif", ".raw", ".cr2", ".nef", ".arw"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v", ".mpeg", ".mpg", ".3gp"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus", ".aiff"}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp"}


def classify_asset_type(extension: str | None) -> AssetType:
    """Classify file by extension into asset type."""
    if not extension:
        return AssetType.OTHER

    ext = extension.lower()
    if ext in IMAGE_EXTENSIONS:
        return AssetType.IMAGE
    elif ext in VIDEO_EXTENSIONS:
        return AssetType.VIDEO
    elif ext in AUDIO_EXTENSIONS:
        return AssetType.AUDIO
    elif ext in DOCUMENT_EXTENSIONS:
        return AssetType.DOCUMENT
    else:
        return AssetType.OTHER


class DAMService:
    """Service for Digital Asset Management operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_index(self, org_id: str, index_id: str, user_id: str) -> IndexJob:
        """Start a DAM analysis job for an index."""
        # Verify index exists and belongs to org
        result = await self.db.execute(
            select(FileIndex)
            .where(FileIndex.id == index_id)
            .where(FileIndex.organization_id == org_id)
        )
        index = result.scalar_one_or_none()
        if not index:
            raise ValueError("Index not found")

        # Count files to analyze (media files only)
        media_extensions = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS | DOCUMENT_EXTENSIONS
        result = await self.db.execute(
            select(func.count(IndexedFile.id))
            .where(IndexedFile.index_id == index_id)
            .where(IndexedFile.is_directory == False)
            .where(IndexedFile.extension.in_(media_extensions))
        )
        total_files = result.scalar() or 0

        # Create job
        job = IndexJob(
            index_id=index_id,
            created_by_id=user_id,
            job_type=JobType.DAM_ANALYSIS,
            status=JobStatus.PENDING,
            total_files=total_files,
        )
        self.db.add(job)
        await self.db.flush()
        await self.db.refresh(job)

        return job

    async def run_analysis_job(self, job_id: str) -> None:
        """Execute DAM analysis for all media files in an index."""
        # Fetch job
        result = await self.db.execute(select(IndexJob).where(IndexJob.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            logger.error("dam_job_not_found", job_id=job_id)
            return

        try:
            # Update job status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)
            await self.db.commit()

            # Get all media files
            media_extensions = list(IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS | DOCUMENT_EXTENSIONS)
            result = await self.db.execute(
                select(IndexedFile)
                .where(IndexedFile.index_id == job.index_id)
                .where(IndexedFile.is_directory == False)
                .where(IndexedFile.extension.in_(media_extensions))
            )
            files = result.scalars().all()

            processed = 0
            failed = 0

            for file in files:
                try:
                    dam_metadata = self._analyze_file(Path(file.path))
                    if dam_metadata:
                        # Update extra_metadata with DAM data
                        existing_meta = file.extra_metadata or {}
                        existing_meta["dam"] = dam_metadata
                        file.extra_metadata = existing_meta
                        file.mime_type = mimetypes.guess_type(file.path)[0]

                    processed += 1
                except Exception as e:
                    logger.warning("dam_file_analysis_error", file=file.path, error=str(e))
                    failed += 1

                # Update progress periodically
                if processed % 50 == 0:
                    job.processed_files = processed
                    job.failed_files = failed
                    job.progress_percent = (processed + failed) / job.total_files * 100 if job.total_files > 0 else 0
                    await self.db.commit()

            # Complete job
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            job.processed_files = processed
            job.failed_files = failed
            job.progress_percent = 100.0
            await self.db.commit()

            logger.info("dam_analysis_completed", job_id=job_id, processed=processed, failed=failed)

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            logger.error("dam_analysis_failed", job_id=job_id, error=str(e))

    def _analyze_file(self, path: Path) -> dict[str, Any] | None:
        """Analyze a single file and extract DAM metadata."""
        if not path.exists():
            return None

        ext = path.suffix.lower()
        asset_type = classify_asset_type(ext)

        metadata: dict[str, Any] = {
            "asset_type": asset_type.value,
            "format": ext.lstrip(".").upper() if ext else None,
        }

        try:
            if asset_type == AssetType.IMAGE:
                metadata.update(self._analyze_image(path))
            elif asset_type == AssetType.AUDIO:
                metadata.update(self._analyze_audio(path))
            elif asset_type == AssetType.DOCUMENT:
                metadata.update(self._analyze_document(path))
            # Video analysis requires ffprobe which may not be available
            elif asset_type == AssetType.VIDEO:
                metadata.update(self._analyze_video(path))
        except Exception as e:
            logger.debug("dam_metadata_extraction_error", path=str(path), error=str(e))

        return metadata

    def _analyze_image(self, path: Path) -> dict[str, Any]:
        """Extract metadata from image files."""
        result: dict[str, Any] = {}

        try:
            import exifread

            with open(path, "rb") as f:
                tags = exifread.process_file(f, details=False)

            if tags:
                exif_data: dict[str, Any] = {}

                # Camera info
                if "Image Make" in tags:
                    exif_data["camera_make"] = str(tags["Image Make"])
                if "Image Model" in tags:
                    exif_data["camera_model"] = str(tags["Image Model"])

                # Date taken
                for date_tag in ["EXIF DateTimeOriginal", "Image DateTime"]:
                    if date_tag in tags:
                        try:
                            date_str = str(tags[date_tag])
                            exif_data["date_taken"] = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S").isoformat()
                        except:
                            pass
                        break

                # Exposure settings
                if "EXIF ExposureTime" in tags:
                    exif_data["exposure_time"] = str(tags["EXIF ExposureTime"])
                if "EXIF FNumber" in tags:
                    try:
                        exif_data["f_number"] = float(tags["EXIF FNumber"].values[0])
                    except:
                        pass
                if "EXIF ISOSpeedRatings" in tags:
                    try:
                        exif_data["iso"] = int(str(tags["EXIF ISOSpeedRatings"]))
                    except:
                        pass

                # GPS coordinates
                if "GPS GPSLatitude" in tags and "GPS GPSLongitude" in tags:
                    try:
                        lat = self._convert_gps_coords(tags["GPS GPSLatitude"].values)
                        lon = self._convert_gps_coords(tags["GPS GPSLongitude"].values)
                        if "GPS GPSLatitudeRef" in tags and str(tags["GPS GPSLatitudeRef"]) == "S":
                            lat = -lat
                        if "GPS GPSLongitudeRef" in tags and str(tags["GPS GPSLongitudeRef"]) == "W":
                            lon = -lon
                        exif_data["gps_latitude"] = lat
                        exif_data["gps_longitude"] = lon
                    except:
                        pass

                # Image dimensions from EXIF
                if "EXIF ExifImageWidth" in tags:
                    try:
                        result["width"] = int(str(tags["EXIF ExifImageWidth"]))
                    except:
                        pass
                if "EXIF ExifImageLength" in tags:
                    try:
                        result["height"] = int(str(tags["EXIF ExifImageLength"]))
                    except:
                        pass

                if exif_data:
                    result["exif"] = exif_data

        except ImportError:
            logger.debug("exifread_not_available")
        except Exception as e:
            logger.debug("exif_extraction_error", path=str(path), error=str(e))

        return result

    def _convert_gps_coords(self, coords: list) -> float:
        """Convert GPS coordinates from EXIF format to decimal degrees."""
        d = float(coords[0])
        m = float(coords[1])
        s = float(coords[2])
        return d + (m / 60.0) + (s / 3600.0)

    def _analyze_audio(self, path: Path) -> dict[str, Any]:
        """Extract metadata from audio files."""
        result: dict[str, Any] = {}

        try:
            from tinytag import TinyTag

            tag = TinyTag.get(str(path))

            if tag.duration:
                result["duration_seconds"] = tag.duration
            if tag.bitrate:
                result["bitrate"] = int(tag.bitrate)
            if tag.samplerate:
                result["sample_rate"] = tag.samplerate
            if tag.channels:
                result["channels"] = tag.channels

            audio_meta: dict[str, Any] = {}
            if tag.title:
                audio_meta["title"] = tag.title
            if tag.artist:
                audio_meta["artist"] = tag.artist
            if tag.album:
                audio_meta["album"] = tag.album
            if tag.year:
                audio_meta["year"] = tag.year
            if tag.track:
                audio_meta["track"] = tag.track
            if tag.genre:
                audio_meta["genre"] = tag.genre

            if audio_meta:
                result["audio"] = audio_meta

        except ImportError:
            logger.debug("tinytag_not_available")
        except Exception as e:
            logger.debug("audio_metadata_error", path=str(path), error=str(e))

        return result

    def _analyze_document(self, path: Path) -> dict[str, Any]:
        """Extract metadata from PDF documents."""
        result: dict[str, Any] = {}

        if path.suffix.lower() != ".pdf":
            return result

        try:
            import pymupdf

            doc = pymupdf.open(str(path))
            result["page_count"] = len(doc)

            doc_meta: dict[str, Any] = {}
            metadata = doc.metadata
            if metadata:
                if metadata.get("title"):
                    doc_meta["title"] = metadata["title"]
                if metadata.get("author"):
                    doc_meta["author"] = metadata["author"]
                if metadata.get("subject"):
                    doc_meta["subject"] = metadata["subject"]
                if metadata.get("creator"):
                    doc_meta["creator"] = metadata["creator"]
                if metadata.get("producer"):
                    doc_meta["producer"] = metadata["producer"]

            if doc_meta:
                result["document"] = doc_meta

            doc.close()

        except ImportError:
            logger.debug("pymupdf_not_available")
        except Exception as e:
            logger.debug("pdf_metadata_error", path=str(path), error=str(e))

        return result

    def _analyze_video(self, path: Path) -> dict[str, Any]:
        """Extract metadata from video files (basic, no ffprobe required)."""
        # Video analysis requires ffprobe which may not be available
        # Return minimal metadata based on file inspection
        return {}

    async def search_assets(
        self,
        org_id: str,
        index_id: str,
        search: DAMSearch,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[IndexedFile], int]:
        """Search for DAM assets with filters."""
        # Verify index access
        result = await self.db.execute(
            select(FileIndex)
            .where(FileIndex.id == index_id)
            .where(FileIndex.organization_id == org_id)
        )
        if not result.scalar_one_or_none():
            raise ValueError("Index not found")

        # Build query
        query = (
            select(IndexedFile)
            .where(IndexedFile.index_id == index_id)
            .where(IndexedFile.is_directory == False)
        )

        # Filter by asset type(s)
        if search.asset_type:
            query = query.where(
                IndexedFile.extra_metadata["dam"]["asset_type"].as_string() == search.asset_type.value
            )
        elif search.asset_types:
            query = query.where(
                IndexedFile.extra_metadata["dam"]["asset_type"].as_string().in_(
                    [t.value for t in search.asset_types]
                )
            )

        # Filter by dimensions
        if search.min_width:
            query = query.where(
                IndexedFile.extra_metadata["dam"]["width"].as_integer() >= search.min_width
            )
        if search.max_width:
            query = query.where(
                IndexedFile.extra_metadata["dam"]["width"].as_integer() <= search.max_width
            )
        if search.min_height:
            query = query.where(
                IndexedFile.extra_metadata["dam"]["height"].as_integer() >= search.min_height
            )
        if search.max_height:
            query = query.where(
                IndexedFile.extra_metadata["dam"]["height"].as_integer() <= search.max_height
            )

        # Filter by duration
        if search.min_duration:
            query = query.where(
                IndexedFile.extra_metadata["dam"]["duration_seconds"].as_float() >= search.min_duration
            )
        if search.max_duration:
            query = query.where(
                IndexedFile.extra_metadata["dam"]["duration_seconds"].as_float() <= search.max_duration
            )

        # Filter by format
        if search.format:
            query = query.where(
                IndexedFile.extra_metadata["dam"]["format"].as_string() == search.format.upper()
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply ordering
        order_column = getattr(IndexedFile, search.order_by, IndexedFile.filename)
        if search.order_desc:
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column)

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        files = result.scalars().all()

        return list(files), total

    async def get_asset(self, org_id: str, index_id: str, file_id: str) -> IndexedFile | None:
        """Get a single asset with DAM metadata."""
        result = await self.db.execute(
            select(IndexedFile)
            .join(FileIndex)
            .where(IndexedFile.id == file_id)
            .where(IndexedFile.index_id == index_id)
            .where(FileIndex.organization_id == org_id)
        )
        return result.scalar_one_or_none()

    async def get_stats(self, org_id: str, index_id: str) -> DAMStats | None:
        """Get DAM statistics for an index."""
        # Verify index access
        result = await self.db.execute(
            select(FileIndex)
            .where(FileIndex.id == index_id)
            .where(FileIndex.organization_id == org_id)
        )
        index = result.scalar_one_or_none()
        if not index:
            return None

        # Count by asset type
        stats: dict[str, Any] = {
            "index_id": index_id,
            "total_assets": 0,
            "total_images": 0,
            "total_videos": 0,
            "total_audio": 0,
            "total_documents": 0,
            "total_other": 0,
            "total_size_bytes": 0,
            "size_by_type": {},
            "format_breakdown": {},
            "resolution_distribution": {},
        }

        # Get all files with DAM metadata
        result = await self.db.execute(
            select(IndexedFile)
            .where(IndexedFile.index_id == index_id)
            .where(IndexedFile.is_directory == False)
            .where(IndexedFile.extra_metadata.isnot(None))
        )
        files = result.scalars().all()

        for file in files:
            dam_data = file.extra_metadata.get("dam") if file.extra_metadata else None
            if not dam_data:
                continue

            asset_type = dam_data.get("asset_type", "other")
            stats["total_assets"] += 1
            stats["total_size_bytes"] += file.size_bytes

            # Count by type
            if asset_type == "image":
                stats["total_images"] += 1
            elif asset_type == "video":
                stats["total_videos"] += 1
            elif asset_type == "audio":
                stats["total_audio"] += 1
            elif asset_type == "document":
                stats["total_documents"] += 1
            else:
                stats["total_other"] += 1

            # Size by type
            stats["size_by_type"][asset_type] = stats["size_by_type"].get(asset_type, 0) + file.size_bytes

            # Format breakdown
            fmt = dam_data.get("format", "unknown")
            stats["format_breakdown"][fmt] = stats["format_breakdown"].get(fmt, 0) + 1

        # Human-readable size
        size_bytes = stats["total_size_bytes"]
        if size_bytes >= 1024 * 1024 * 1024:
            stats["total_size_human"] = f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
        elif size_bytes >= 1024 * 1024:
            stats["total_size_human"] = f"{size_bytes / (1024 * 1024):.2f} MB"
        elif size_bytes >= 1024:
            stats["total_size_human"] = f"{size_bytes / 1024:.2f} KB"
        else:
            stats["total_size_human"] = f"{size_bytes} B"

        return DAMStats(**stats)
