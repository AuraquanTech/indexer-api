"""
Code Discovery service.
Analyzes code files for language detection, complexity metrics, and MVP readiness.
"""
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from indexer_api.core.config import settings
from indexer_api.db.models import FileIndex, IndexedFile, IndexJob, JobStatus, JobType
from indexer_api.schemas.code import (
    CodeFileResponse,
    CodeMetadata,
    CodeSearch,
    DependencyInfo,
    LanguageStats,
    MVPCheckResult,
    MVPReadiness,
    ProjectDependencies,
    ProjectStats,
)

logger = structlog.get_logger()

# Code file extensions by language
LANGUAGE_EXTENSIONS: dict[str, list[str]] = {
    "python": [".py", ".pyw", ".pyx", ".pxd"],
    "javascript": [".js", ".mjs", ".cjs"],
    "typescript": [".ts", ".tsx"],
    "java": [".java"],
    "go": [".go"],
    "rust": [".rs"],
    "c": [".c", ".h"],
    "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"],
    "csharp": [".cs"],
    "ruby": [".rb"],
    "php": [".php"],
    "swift": [".swift"],
    "kotlin": [".kt", ".kts"],
    "scala": [".scala"],
    "r": [".r", ".R"],
    "shell": [".sh", ".bash", ".zsh"],
    "powershell": [".ps1", ".psm1"],
    "sql": [".sql"],
    "html": [".html", ".htm"],
    "css": [".css", ".scss", ".sass", ".less"],
    "yaml": [".yaml", ".yml"],
    "json": [".json"],
    "xml": [".xml"],
    "markdown": [".md", ".markdown"],
}

# Reverse mapping for extension to language
EXTENSION_TO_LANGUAGE: dict[str, str] = {}
for lang, exts in LANGUAGE_EXTENSIONS.items():
    for ext in exts:
        EXTENSION_TO_LANGUAGE[ext] = lang

# Python standard library modules (partial list)
PYTHON_STDLIB = {
    "os", "sys", "re", "json", "datetime", "collections", "itertools", "functools",
    "pathlib", "typing", "abc", "dataclasses", "enum", "io", "logging", "math",
    "random", "time", "threading", "multiprocessing", "subprocess", "socket",
    "http", "urllib", "email", "html", "xml", "sqlite3", "pickle", "copy",
    "hashlib", "hmac", "secrets", "tempfile", "shutil", "glob", "fnmatch",
    "argparse", "configparser", "csv", "struct", "codecs", "unicodedata",
    "string", "textwrap", "difflib", "unittest", "doctest", "pdb", "profile",
    "timeit", "trace", "gc", "inspect", "dis", "ast", "contextlib", "warnings",
    "traceback", "types", "operator", "weakref", "heapq", "bisect", "array",
    "queue", "asyncio", "concurrent", "ssl", "select", "selectors", "signal",
    "mmap", "ctypes", "platform", "sysconfig", "builtins", "importlib",
}


def detect_language_from_extension(extension: str | None) -> str | None:
    """Detect programming language from file extension."""
    if not extension:
        return None
    return EXTENSION_TO_LANGUAGE.get(extension.lower())


class CodeDiscoveryService:
    """Service for code analysis and discovery operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_index(self, org_id: str, index_id: str, user_id: str) -> IndexJob:
        """Start a code analysis job for an index."""
        # Verify index exists and belongs to org
        result = await self.db.execute(
            select(FileIndex)
            .where(FileIndex.id == index_id)
            .where(FileIndex.organization_id == org_id)
        )
        index = result.scalar_one_or_none()
        if not index:
            raise ValueError("Index not found")

        # Count code files to analyze
        code_extensions = []
        for exts in LANGUAGE_EXTENSIONS.values():
            code_extensions.extend(exts)

        result = await self.db.execute(
            select(func.count(IndexedFile.id))
            .where(IndexedFile.index_id == index_id)
            .where(IndexedFile.is_directory == False)
            .where(IndexedFile.extension.in_(code_extensions))
        )
        total_files = result.scalar() or 0

        # Create job
        job = IndexJob(
            index_id=index_id,
            created_by_id=user_id,
            job_type=JobType.CODE_ANALYSIS,
            status=JobStatus.PENDING,
            total_files=total_files,
        )
        self.db.add(job)
        await self.db.flush()
        await self.db.refresh(job)

        return job

    async def run_analysis_job(self, job_id: str) -> None:
        """Execute code analysis for all code files in an index."""
        # Fetch job
        result = await self.db.execute(select(IndexJob).where(IndexJob.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            logger.error("code_job_not_found", job_id=job_id)
            return

        try:
            # Update job status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)
            await self.db.commit()

            # Get all code files
            code_extensions = []
            for exts in LANGUAGE_EXTENSIONS.values():
                code_extensions.extend(exts)

            result = await self.db.execute(
                select(IndexedFile)
                .where(IndexedFile.index_id == job.index_id)
                .where(IndexedFile.is_directory == False)
                .where(IndexedFile.extension.in_(code_extensions))
            )
            files = result.scalars().all()

            processed = 0
            failed = 0

            for file in files:
                try:
                    # Skip files that are too large
                    if file.size_bytes > settings.code_max_file_size_kb * 1024:
                        continue

                    code_metadata = self._analyze_file(Path(file.path), file.extension)
                    if code_metadata:
                        # Update extra_metadata with code data
                        existing_meta = file.extra_metadata or {}
                        existing_meta["code"] = code_metadata
                        file.extra_metadata = existing_meta

                        # Update complexity score
                        if code_metadata.get("complexity"):
                            file.complexity_score = code_metadata["complexity"]

                    processed += 1
                except Exception as e:
                    logger.warning("code_file_analysis_error", file=file.path, error=str(e))
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

            logger.info("code_analysis_completed", job_id=job_id, processed=processed, failed=failed)

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            logger.error("code_analysis_failed", job_id=job_id, error=str(e))

    def _analyze_file(self, path: Path, extension: str | None) -> dict[str, Any] | None:
        """Analyze a single code file."""
        if not path.exists():
            return None

        language = detect_language_from_extension(extension)
        if not language:
            return None

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

        lines = content.split("\n")
        lines_total = len(lines)
        lines_blank = sum(1 for line in lines if not line.strip())
        lines_comment = 0
        lines_code = 0

        # Simple comment detection
        in_multiline = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Python comments
            if language == "python":
                if stripped.startswith("#"):
                    lines_comment += 1
                elif stripped.startswith('"""') or stripped.startswith("'''"):
                    in_multiline = not in_multiline
                    lines_comment += 1
                elif in_multiline:
                    lines_comment += 1
                else:
                    lines_code += 1

            # C-style comments
            elif language in ["javascript", "typescript", "java", "go", "rust", "c", "cpp", "csharp", "swift", "kotlin", "scala"]:
                if stripped.startswith("//"):
                    lines_comment += 1
                elif "/*" in stripped and "*/" in stripped:
                    lines_comment += 1
                elif "/*" in stripped:
                    in_multiline = True
                    lines_comment += 1
                elif "*/" in stripped:
                    in_multiline = False
                    lines_comment += 1
                elif in_multiline:
                    lines_comment += 1
                else:
                    lines_code += 1
            else:
                lines_code += 1

        # Extract imports
        imports = self._extract_imports(content, language)

        # Count functions and classes
        functions = 0
        classes = 0
        has_docstrings = False
        has_type_hints = False

        if language == "python":
            functions = len(re.findall(r"^\s*def\s+\w+", content, re.MULTILINE))
            classes = len(re.findall(r"^\s*class\s+\w+", content, re.MULTILINE))
            has_docstrings = bool(re.search(r'""".*?"""', content, re.DOTALL) or re.search(r"'''.*?'''", content, re.DOTALL))
            has_type_hints = bool(re.search(r"def\s+\w+\s*\([^)]*:\s*\w+", content) or re.search(r"->\s*\w+", content))

            # Try radon for complexity if available
            complexity = self._calculate_python_complexity(content)
        elif language in ["javascript", "typescript"]:
            functions = len(re.findall(r"\bfunction\s+\w+|const\s+\w+\s*=\s*(?:async\s*)?\(|=>\s*{", content))
            classes = len(re.findall(r"\bclass\s+\w+", content))
            has_type_hints = language == "typescript"
            complexity = None
        elif language == "java":
            functions = len(re.findall(r"(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+\w+\s*\([^)]*\)\s*{", content))
            classes = len(re.findall(r"\bclass\s+\w+", content))
            complexity = None
        elif language == "go":
            functions = len(re.findall(r"\bfunc\s+\w+", content))
            classes = len(re.findall(r"\btype\s+\w+\s+struct", content))
            complexity = None
        elif language == "rust":
            functions = len(re.findall(r"\bfn\s+\w+", content))
            classes = len(re.findall(r"\bstruct\s+\w+|\benum\s+\w+|\bimpl\s+\w+", content))
            complexity = None
        else:
            complexity = None

        metadata = {
            "language": language,
            "lines_total": lines_total,
            "lines_code": lines_code,
            "lines_comment": lines_comment,
            "lines_blank": lines_blank,
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "has_docstrings": has_docstrings,
            "has_type_hints": has_type_hints,
        }

        if complexity is not None:
            metadata["complexity"] = complexity

        return metadata

    def _extract_imports(self, content: str, language: str) -> list[str]:
        """Extract import statements from code."""
        imports = []

        if language == "python":
            # import x, from x import y
            for match in re.finditer(r"^\s*import\s+([\w.]+)", content, re.MULTILINE):
                imports.append(match.group(1).split(".")[0])
            for match in re.finditer(r"^\s*from\s+([\w.]+)\s+import", content, re.MULTILINE):
                imports.append(match.group(1).split(".")[0])

        elif language in ["javascript", "typescript"]:
            # import x from 'y', require('y')
            for match in re.finditer(r"(?:import.*from\s+['\"]|require\s*\(\s*['\"])([^'\"]+)", content):
                pkg = match.group(1)
                if not pkg.startswith("."):
                    imports.append(pkg.split("/")[0])

        elif language == "java":
            # import x.y.z
            for match in re.finditer(r"^\s*import\s+([\w.]+);", content, re.MULTILINE):
                imports.append(match.group(1).split(".")[0])

        elif language == "go":
            # import "x"
            for match in re.finditer(r'import\s+(?:\(\s*)?["\']([^"\']+)', content):
                imports.append(match.group(1).split("/")[-1])

        elif language == "rust":
            # use x::y
            for match in re.finditer(r"^\s*use\s+(\w+)::", content, re.MULTILINE):
                imports.append(match.group(1))

        return list(set(imports))

    def _calculate_python_complexity(self, content: str) -> float | None:
        """Calculate cyclomatic complexity for Python code using radon."""
        try:
            from radon.complexity import cc_visit

            results = cc_visit(content)
            if not results:
                return 0.0

            total_complexity = sum(block.complexity for block in results)
            return total_complexity / len(results)

        except ImportError:
            logger.debug("radon_not_available")
            return None
        except Exception as e:
            logger.debug("complexity_calculation_error", error=str(e))
            return None

    async def search_code(
        self,
        org_id: str,
        index_id: str,
        search: CodeSearch,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[IndexedFile], int]:
        """Search for code files with filters."""
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
            .where(IndexedFile.extra_metadata["code"].isnot(None))
        )

        # Filter by language
        if search.language:
            query = query.where(
                IndexedFile.extra_metadata["code"]["language"].as_string() == search.language
            )
        elif search.languages:
            query = query.where(
                IndexedFile.extra_metadata["code"]["language"].as_string().in_(search.languages)
            )

        # Filter by line count
        if search.min_lines:
            query = query.where(
                IndexedFile.extra_metadata["code"]["lines_total"].as_integer() >= search.min_lines
            )
        if search.max_lines:
            query = query.where(
                IndexedFile.extra_metadata["code"]["lines_total"].as_integer() <= search.max_lines
            )

        # Filter by complexity
        if search.min_complexity:
            query = query.where(
                IndexedFile.extra_metadata["code"]["complexity"].as_float() >= search.min_complexity
            )
        if search.max_complexity:
            query = query.where(
                IndexedFile.extra_metadata["code"]["complexity"].as_float() <= search.max_complexity
            )

        # Filter by path prefix
        if search.path_prefix:
            query = query.where(IndexedFile.path.startswith(search.path_prefix))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply ordering
        order_column = getattr(IndexedFile, search.order_by, IndexedFile.path)
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

    async def get_project_stats(self, org_id: str, index_id: str) -> ProjectStats | None:
        """Get aggregate code statistics for an index."""
        # Verify index access
        result = await self.db.execute(
            select(FileIndex)
            .where(FileIndex.id == index_id)
            .where(FileIndex.organization_id == org_id)
        )
        if not result.scalar_one_or_none():
            return None

        # Get all code files
        result = await self.db.execute(
            select(IndexedFile)
            .where(IndexedFile.index_id == index_id)
            .where(IndexedFile.is_directory == False)
            .where(IndexedFile.extra_metadata["code"].isnot(None))
        )
        files = result.scalars().all()

        if not files:
            return ProjectStats(
                index_id=index_id,
                total_code_files=0,
                total_lines=0,
                total_code_lines=0,
                total_comment_lines=0,
                total_blank_lines=0,
                total_size_bytes=0,
                languages=[],
                language_breakdown={},
                avg_file_size=0,
                largest_files=[],
                most_complex_files=[],
            )

        # Aggregate by language
        lang_stats: dict[str, dict[str, Any]] = {}
        total_lines = 0
        total_code_lines = 0
        total_comment_lines = 0
        total_blank_lines = 0
        total_size = 0
        complexities = []

        for file in files:
            if not file.extra_metadata:
                continue
            code = file.extra_metadata.get("code", {})
            if not code:
                continue
            lang = code.get("language", "unknown")

            if lang not in lang_stats:
                lang_stats[lang] = {
                    "file_count": 0,
                    "total_lines": 0,
                    "code_lines": 0,
                    "comment_lines": 0,
                    "blank_lines": 0,
                    "total_size_bytes": 0,
                    "complexities": [],
                    "total_functions": 0,
                    "total_classes": 0,
                }

            lang_stats[lang]["file_count"] += 1
            lang_stats[lang]["total_lines"] += code.get("lines_total", 0)
            lang_stats[lang]["code_lines"] += code.get("lines_code", 0)
            lang_stats[lang]["comment_lines"] += code.get("lines_comment", 0)
            lang_stats[lang]["blank_lines"] += code.get("lines_blank", 0)
            lang_stats[lang]["total_size_bytes"] += file.size_bytes
            lang_stats[lang]["total_functions"] += code.get("functions", 0)
            lang_stats[lang]["total_classes"] += code.get("classes", 0)

            if code.get("complexity") is not None:
                lang_stats[lang]["complexities"].append(code["complexity"])
                complexities.append(code["complexity"])

            total_lines += code.get("lines_total", 0)
            total_code_lines += code.get("lines_code", 0)
            total_comment_lines += code.get("lines_comment", 0)
            total_blank_lines += code.get("lines_blank", 0)
            total_size += file.size_bytes

        # Build language stats list
        languages = []
        language_breakdown = {}
        for lang, stats in lang_stats.items():
            avg_complexity = None
            if stats["complexities"]:
                avg_complexity = sum(stats["complexities"]) / len(stats["complexities"])

            languages.append(LanguageStats(
                language=lang,
                file_count=stats["file_count"],
                total_lines=stats["total_lines"],
                code_lines=stats["code_lines"],
                comment_lines=stats["comment_lines"],
                blank_lines=stats["blank_lines"],
                total_size_bytes=stats["total_size_bytes"],
                avg_complexity=avg_complexity,
                total_functions=stats["total_functions"],
                total_classes=stats["total_classes"],
            ))
            language_breakdown[lang] = stats["file_count"]

        # Sort languages by file count
        languages.sort(key=lambda x: x.file_count, reverse=True)

        # Get largest files (filter to those with valid metadata)
        files_with_meta = [f for f in files if f.extra_metadata and f.extra_metadata.get("code")]
        sorted_by_size = sorted(files_with_meta, key=lambda f: f.size_bytes, reverse=True)[:5]
        largest_files = [
            {"path": f.path, "size_bytes": f.size_bytes, "language": f.extra_metadata.get("code", {}).get("language")}
            for f in sorted_by_size
        ]

        # Get most complex files
        files_with_complexity = [f for f in files_with_meta if f.extra_metadata.get("code", {}).get("complexity") is not None]
        sorted_by_complexity = sorted(
            files_with_complexity,
            key=lambda f: f.extra_metadata.get("code", {}).get("complexity", 0),
            reverse=True
        )[:5]
        most_complex_files = [
            {"path": f.path, "complexity": f.extra_metadata.get("code", {}).get("complexity"), "language": f.extra_metadata.get("code", {}).get("language")}
            for f in sorted_by_complexity
        ]

        return ProjectStats(
            index_id=index_id,
            total_code_files=len(files),
            total_lines=total_lines,
            total_code_lines=total_code_lines,
            total_comment_lines=total_comment_lines,
            total_blank_lines=total_blank_lines,
            total_size_bytes=total_size,
            languages=languages,
            language_breakdown=language_breakdown,
            avg_complexity=sum(complexities) / len(complexities) if complexities else None,
            avg_file_size=total_size / len(files) if files else 0,
            largest_files=largest_files,
            most_complex_files=most_complex_files,
        )

    async def get_dependencies(self, org_id: str, index_id: str) -> ProjectDependencies | None:
        """Analyze and return project dependencies."""
        # Verify index access
        result = await self.db.execute(
            select(FileIndex)
            .where(FileIndex.id == index_id)
            .where(FileIndex.organization_id == org_id)
        )
        if not result.scalar_one_or_none():
            return None

        # Get all Python code files (focus on Python for now)
        result = await self.db.execute(
            select(IndexedFile)
            .where(IndexedFile.index_id == index_id)
            .where(IndexedFile.is_directory == False)
            .where(IndexedFile.extra_metadata["code"]["language"].as_string() == "python")
        )
        files = result.scalars().all()

        # Collect imports
        import_usage: dict[str, list[str]] = {}
        for file in files:
            code = file.extra_metadata.get("code", {})
            for imp in code.get("imports", []):
                if imp not in import_usage:
                    import_usage[imp] = []
                import_usage[imp].append(file.path)

        # Categorize imports
        stdlib_imports = []
        third_party_imports = []
        local_imports = []

        for imp, files_using in import_usage.items():
            dep = DependencyInfo(
                name=imp,
                import_count=len(files_using),
                files_using=files_using[:10],  # Limit to first 10
                is_stdlib=imp in PYTHON_STDLIB,
            )

            if imp in PYTHON_STDLIB:
                stdlib_imports.append(dep)
            elif imp.startswith("_") or "." in imp:
                local_imports.append(dep)
            else:
                third_party_imports.append(dep)

        # Sort by usage
        stdlib_imports.sort(key=lambda x: x.import_count, reverse=True)
        third_party_imports.sort(key=lambda x: x.import_count, reverse=True)
        local_imports.sort(key=lambda x: x.import_count, reverse=True)

        return ProjectDependencies(
            index_id=index_id,
            total_unique_imports=len(import_usage),
            stdlib_imports=stdlib_imports,
            third_party_imports=third_party_imports,
            local_imports=local_imports,
        )

    async def calculate_mvp_readiness(self, org_id: str, index_id: str) -> MVPReadiness | None:
        """Calculate MVP readiness score for a project."""
        # Verify index access
        result = await self.db.execute(
            select(FileIndex)
            .where(FileIndex.id == index_id)
            .where(FileIndex.organization_id == org_id)
        )
        index = result.scalar_one_or_none()
        if not index:
            return None

        # Get all files in index
        result = await self.db.execute(
            select(IndexedFile)
            .where(IndexedFile.index_id == index_id)
            .where(IndexedFile.is_directory == False)
        )
        files = result.scalars().all()

        # Build file name set for quick lookup
        filenames = {Path(f.path).name.lower() for f in files}
        file_paths = [f.path.lower() for f in files]

        # Check for project files
        has_readme = any(name.startswith("readme") for name in filenames)
        has_license = any(name.startswith("license") or name == "copying" for name in filenames)
        has_gitignore = ".gitignore" in filenames
        has_tests = any("test" in path or "tests" in path or "spec" in path for path in file_paths)
        has_ci = any(".github/workflows" in path or ".gitlab-ci" in path or "jenkinsfile" in path.lower() for path in file_paths)
        has_requirements = any(name in ["requirements.txt", "pyproject.toml", "setup.py", "package.json", "cargo.toml", "go.mod"] for name in filenames)
        has_setup_config = any(name in ["setup.py", "setup.cfg", "pyproject.toml", "package.json", "cargo.toml"] for name in filenames)

        # Get code files for quality metrics
        code_files = [f for f in files if f.extra_metadata and f.extra_metadata.get("code")]
        test_files = [f for f in code_files if "test" in f.path.lower() or "spec" in f.path.lower()]

        # Calculate ratios
        total_code_lines = sum(f.extra_metadata.get("code", {}).get("lines_code", 0) for f in code_files)
        total_comment_lines = sum(f.extra_metadata.get("code", {}).get("lines_comment", 0) for f in code_files)
        test_lines = sum(f.extra_metadata.get("code", {}).get("lines_code", 0) for f in test_files)

        documentation_ratio = total_comment_lines / total_code_lines if total_code_lines > 0 else 0
        test_ratio = test_lines / total_code_lines if total_code_lines > 0 else 0

        # Calculate average complexity
        complexities = [
            f.extra_metadata.get("code", {}).get("complexity")
            for f in code_files
            if f.extra_metadata.get("code", {}).get("complexity") is not None
        ]
        avg_complexity = sum(complexities) / len(complexities) if complexities else None

        # Calculate type hint ratio for Python
        python_files = [f for f in code_files if f.extra_metadata.get("code", {}).get("language") == "python"]
        type_hint_count = sum(1 for f in python_files if f.extra_metadata.get("code", {}).get("has_type_hints"))
        type_hint_ratio = type_hint_count / len(python_files) if python_files else 0

        # Calculate scores
        checks: list[MVPCheckResult] = []
        total_score = 0

        # Documentation (25 points)
        readme_check = MVPCheckResult(
            name="README",
            passed=has_readme,
            score=15 if has_readme else 0,
            max_score=15,
            description="Project has a README file",
            details="Found README" if has_readme else "Missing README file",
        )
        checks.append(readme_check)
        total_score += readme_check.score

        doc_ratio_check = MVPCheckResult(
            name="Documentation Ratio",
            passed=documentation_ratio >= 0.1,
            score=10 if documentation_ratio >= 0.1 else 5 if documentation_ratio >= 0.05 else 0,
            max_score=10,
            description="Code has adequate comments",
            details=f"Comment ratio: {documentation_ratio:.1%}",
        )
        checks.append(doc_ratio_check)
        total_score += doc_ratio_check.score

        # Testing (25 points)
        tests_check = MVPCheckResult(
            name="Has Tests",
            passed=has_tests,
            score=15 if has_tests else 0,
            max_score=15,
            description="Project has test files",
            details=f"Found {len(test_files)} test files" if has_tests else "No test files found",
        )
        checks.append(tests_check)
        total_score += tests_check.score

        test_ratio_check = MVPCheckResult(
            name="Test Coverage",
            passed=test_ratio >= 0.2,
            score=10 if test_ratio >= 0.2 else 5 if test_ratio >= 0.1 else 0,
            max_score=10,
            description="Test code ratio is adequate",
            details=f"Test ratio: {test_ratio:.1%}",
        )
        checks.append(test_ratio_check)
        total_score += test_ratio_check.score

        # Project Setup (20 points)
        license_check = MVPCheckResult(
            name="License",
            passed=has_license,
            score=5 if has_license else 0,
            max_score=5,
            description="Project has a license",
            details="License found" if has_license else "Missing license file",
        )
        checks.append(license_check)
        total_score += license_check.score

        gitignore_check = MVPCheckResult(
            name="Git Ignore",
            passed=has_gitignore,
            score=5 if has_gitignore else 0,
            max_score=5,
            description="Project has .gitignore",
            details=".gitignore found" if has_gitignore else "Missing .gitignore",
        )
        checks.append(gitignore_check)
        total_score += gitignore_check.score

        ci_check = MVPCheckResult(
            name="CI/CD",
            passed=has_ci,
            score=10 if has_ci else 0,
            max_score=10,
            description="Project has CI/CD configuration",
            details="CI config found" if has_ci else "No CI/CD configuration found",
        )
        checks.append(ci_check)
        total_score += ci_check.score

        # Code Quality (30 points)
        complexity_score = 0
        if avg_complexity is not None:
            if avg_complexity < 10:
                complexity_score = 15
            elif avg_complexity < 20:
                complexity_score = 10
            elif avg_complexity < 30:
                complexity_score = 5

        complexity_check = MVPCheckResult(
            name="Code Complexity",
            passed=avg_complexity is None or avg_complexity < 10,
            score=complexity_score,
            max_score=15,
            description="Code complexity is manageable",
            details=f"Avg complexity: {avg_complexity:.1f}" if avg_complexity else "Complexity not measured",
        )
        checks.append(complexity_check)
        total_score += complexity_check.score

        type_hints_check = MVPCheckResult(
            name="Type Hints",
            passed=type_hint_ratio >= 0.5,
            score=10 if type_hint_ratio >= 0.5 else 5 if type_hint_ratio >= 0.25 else 0,
            max_score=10,
            description="Python code uses type hints",
            details=f"Type hint ratio: {type_hint_ratio:.1%}" if python_files else "No Python files",
        )
        checks.append(type_hints_check)
        total_score += type_hints_check.score

        requirements_check = MVPCheckResult(
            name="Dependencies Defined",
            passed=has_requirements,
            score=5 if has_requirements else 0,
            max_score=5,
            description="Project has dependency definition",
            details="Dependencies file found" if has_requirements else "No dependency file found",
        )
        checks.append(requirements_check)
        total_score += requirements_check.score

        # Generate recommendations
        recommendations = []
        if not has_readme:
            recommendations.append("Add a README.md file to describe your project")
        if not has_license:
            recommendations.append("Add a LICENSE file to clarify usage rights")
        if not has_gitignore:
            recommendations.append("Add a .gitignore file to exclude build artifacts")
        if not has_tests:
            recommendations.append("Add unit tests to improve code reliability")
        if test_ratio < 0.2 and has_tests:
            recommendations.append("Increase test coverage to at least 20% of code")
        if not has_ci:
            recommendations.append("Set up CI/CD (GitHub Actions, GitLab CI, etc.)")
        if avg_complexity and avg_complexity >= 20:
            recommendations.append("Reduce code complexity by refactoring complex functions")
        if python_files and type_hint_ratio < 0.5:
            recommendations.append("Add type hints to Python code for better maintainability")
        if documentation_ratio < 0.1:
            recommendations.append("Add more code comments and documentation")

        # Calculate grade
        if total_score >= 90:
            grade = "A"
        elif total_score >= 80:
            grade = "B"
        elif total_score >= 70:
            grade = "C"
        elif total_score >= 60:
            grade = "D"
        else:
            grade = "F"

        return MVPReadiness(
            index_id=index_id,
            score=total_score,
            grade=grade,
            has_readme=has_readme,
            has_license=has_license,
            has_gitignore=has_gitignore,
            has_tests=has_tests,
            has_ci=has_ci,
            has_requirements=has_requirements,
            has_setup_config=has_setup_config,
            documentation_ratio=documentation_ratio,
            test_ratio=test_ratio,
            avg_complexity=avg_complexity,
            type_hint_ratio=type_hint_ratio,
            checks=checks,
            recommendations=recommendations,
        )
