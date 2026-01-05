"""
Job handlers for catalog operations.

Handles scan, refresh, health check, LLM analysis, and embedding index jobs.

This module is designed with production-grade reliability:
- Proper session handling with explicit commits
- Normalized data storage (lowercase languages/frameworks)
- Comprehensive error handling with detailed logging
- Atomic batch operations where possible
"""
from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from indexer_api.catalog.discovery import ProjectDiscovery, ProjectManifest
from indexer_api.catalog.models import CatalogJob, CatalogJobRun, CatalogProject
from indexer_api.core.logging import get_logger

logger = get_logger(__name__)


def _normalize_languages(languages: Optional[List[str]]) -> List[str]:
    """
    Normalize language names to lowercase for consistent filtering.

    Args:
        languages: List of language names (possibly mixed case)

    Returns:
        List of lowercase language names
    """
    if not languages:
        return []
    return [lang.lower().strip() for lang in languages if lang and lang.strip()]


def _normalize_frameworks(frameworks: Optional[List[str]]) -> List[str]:
    """
    Normalize framework names to lowercase for consistent filtering.

    Args:
        frameworks: List of framework names (possibly mixed case)

    Returns:
        List of lowercase framework names
    """
    if not frameworks:
        return []
    return [fw.lower().strip() for fw in frameworks if fw and fw.strip()]


class JobHandler:
    """Base class for job handlers."""

    async def execute(
        self,
        job: CatalogJob,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Execute the job and return result.

        Args:
            job: The job to execute
            db: Database session (caller is responsible for commit)

        Returns:
            Result dictionary with status and details
        """
        raise NotImplementedError


class ScanJobHandler(JobHandler):
    """
    Handler for filesystem scan jobs.

    Discovers projects in configured paths and creates/updates catalog entries.
    All language and framework names are normalized to lowercase.
    """

    def __init__(self, max_depth: int = 10):
        self.discovery = ProjectDiscovery(max_depth=max_depth)

    async def execute(
        self,
        job: CatalogJob,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Execute scan job."""
        import os

        paths = job.result.get("paths", []) if job.result else []
        max_depth = job.result.get("max_depth", 10) if job.result else 10

        if not paths:
            default_paths = os.environ.get("CATALOG_WATCH_PATHS", "").split(",")
            paths = [p.strip() for p in default_paths if p.strip()]

        if not paths:
            return {
                "status": "skipped",
                "reason": "no_paths_configured",
            }

        discovered = 0
        created = 0
        updated = 0
        errors: List[str] = []

        # Track names used in this batch to avoid duplicates
        used_names: Set[str] = set()

        # Load existing names for this organization
        existing_names_result = await db.execute(
            select(CatalogProject.name).where(
                CatalogProject.organization_id == job.organization_id
            )
        )
        for (name,) in existing_names_result.all():
            used_names.add(name)

        for path_str in paths:
            path = Path(path_str)
            if not path.exists():
                errors.append(f"Path not found: {path_str}")
                continue

            logger.info("scan_path_started", path=str(path))

            try:
                projects = self.discovery.discover(path)

                for project_path, manifest in projects:
                    discovered += 1

                    try:
                        # Check if project exists by path
                        existing = await db.execute(
                            select(CatalogProject).where(
                                CatalogProject.organization_id == job.organization_id,
                                CatalogProject.path == str(project_path),
                            )
                        )
                        project = existing.scalar_one_or_none()

                        if project:
                            # Update existing project
                            self._update_project(project, manifest)
                            updated += 1
                        else:
                            # Generate unique name if needed
                            unique_name = self._generate_unique_name(
                                manifest.name,
                                project_path,
                                used_names,
                            )
                            used_names.add(unique_name)

                            # Create new project with NORMALIZED data
                            project = CatalogProject(
                                organization_id=job.organization_id,
                                name=unique_name,
                                title=manifest.title,
                                description=manifest.description,
                                path=str(project_path),
                                languages=_normalize_languages(manifest.languages),
                                frameworks=_normalize_frameworks(manifest.frameworks),
                                license_spdx=manifest.license_spdx,
                                repository_url=manifest.repository_url,
                                tags=manifest.keywords,
                                last_synced_at=datetime.now(timezone.utc),
                            )
                            db.add(project)
                            created += 1

                    except Exception as e:
                        logger.error(
                            "scan_project_error",
                            path=str(project_path),
                            error=str(e),
                        )
                        errors.append(f"Project {project_path}: {e}")

                # Commit after each path to avoid holding locks too long
                await db.commit()

            except Exception as e:
                logger.error("scan_path_error", path=str(path), error=str(e))
                errors.append(f"Path {path}: {e}")
                # Rollback partial changes for this path
                await db.rollback()

        logger.info(
            "scan_completed",
            discovered=discovered,
            created=created,
            updated=updated,
            errors=len(errors),
        )

        return {
            "status": "completed",
            "discovered": discovered,
            "created": created,
            "updated": updated,
            "errors": errors[:10] if errors else None,
        }

    def _generate_unique_name(
        self,
        base_name: str,
        project_path: Path,
        used_names: Set[str],
    ) -> str:
        """
        Generate a unique project name.

        Uses parent directory name or path hash as suffix if needed.

        Args:
            base_name: Original project name
            project_path: Path to the project
            used_names: Set of already-used names

        Returns:
            A unique name not in used_names
        """
        if base_name not in used_names:
            return base_name

        # Try adding parent directory name
        parent = project_path.parent.name
        candidate = f"{base_name}-{parent}"
        if candidate not in used_names:
            return candidate

        # Try adding numeric suffix
        for suffix in range(2, 11):
            candidate = f"{base_name}-{parent}-{suffix}"
            if candidate not in used_names:
                return candidate

        # Fallback to path hash
        path_hash = hashlib.md5(str(project_path).encode()).hexdigest()[:6]
        return f"{base_name}-{path_hash}"

    def _update_project(
        self,
        project: CatalogProject,
        manifest: ProjectManifest,
    ) -> None:
        """
        Update project with manifest data.

        Normalizes languages and frameworks to lowercase.
        """
        if manifest.title:
            project.title = manifest.title
        if manifest.description:
            project.description = manifest.description
        if manifest.languages:
            project.languages = _normalize_languages(manifest.languages)
        if manifest.frameworks:
            project.frameworks = _normalize_frameworks(manifest.frameworks)
        if manifest.license_spdx:
            project.license_spdx = manifest.license_spdx
        if manifest.repository_url:
            project.repository_url = manifest.repository_url
        if manifest.keywords:
            project.tags = manifest.keywords
        project.last_synced_at = datetime.now(timezone.utc)


class RefreshJobHandler(JobHandler):
    """
    Handler for project refresh jobs.

    Re-scans a single project and updates its metadata.
    """

    def __init__(self):
        self.discovery = ProjectDiscovery()

    async def execute(
        self,
        job: CatalogJob,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Execute refresh job."""
        if not job.project_id:
            return {"status": "error", "reason": "no_project_id"}

        result = await db.execute(
            select(CatalogProject).where(CatalogProject.id == job.project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            return {"status": "error", "reason": "project_not_found"}

        path = Path(project.path)
        if not path.exists():
            return {"status": "error", "reason": "path_not_found"}

        manifest = self.discovery.detect_project(path)
        if not manifest:
            return {"status": "error", "reason": "not_a_project"}

        # Update project with NORMALIZED data
        if manifest.title:
            project.title = manifest.title
        if manifest.description:
            project.description = manifest.description
        if manifest.languages:
            project.languages = _normalize_languages(manifest.languages)
        if manifest.frameworks:
            project.frameworks = _normalize_frameworks(manifest.frameworks)
        if manifest.license_spdx:
            project.license_spdx = manifest.license_spdx
        if manifest.repository_url:
            project.repository_url = manifest.repository_url
        if manifest.keywords:
            project.tags = manifest.keywords

        project.last_synced_at = datetime.now(timezone.utc)
        project.health_score = self._calculate_health(project, path)

        await db.commit()

        logger.info(
            "refresh_completed",
            project=project.name,
            health_score=project.health_score,
        )

        return {
            "status": "completed",
            "project": project.name,
            "health_score": project.health_score,
        }

    def _calculate_health(self, project: CatalogProject, path: Path) -> float:
        """
        Calculate project health score (0-100).

        Evaluates:
        - README presence (15 pts)
        - License (10 pts)
        - Tests directory (15 pts)
        - CI config (10 pts)
        - Description (10 pts)
        - Recent activity (20 pts)
        - Languages/frameworks (10 pts)
        """
        score = 0.0
        max_score = 0.0

        # Has README (15 points)
        max_score += 15
        for readme in ["README.md", "README.rst", "README.txt", "README"]:
            if (path / readme).exists():
                score += 15
                break

        # Has license (10 points)
        max_score += 10
        if project.license_spdx or (path / "LICENSE").exists():
            score += 10

        # Has tests directory (15 points)
        max_score += 15
        if any((path / d).exists() for d in ["tests", "test", "spec", "__tests__"]):
            score += 15

        # Has CI config (10 points)
        max_score += 10
        ci_files = [".github/workflows", ".gitlab-ci.yml", "Jenkinsfile", ".circleci"]
        if any((path / f).exists() for f in ci_files):
            score += 10

        # Has description (10 points)
        max_score += 10
        if project.description:
            score += 10

        # Recent activity (20 points)
        max_score += 20
        git_dir = path / ".git"
        if git_dir.exists():
            try:
                import subprocess
                import time

                result = subprocess.run(
                    ["git", "log", "-1", "--format=%ct"],
                    cwd=path,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    last_commit = int(result.stdout.strip())
                    days_ago = (time.time() - last_commit) / 86400
                    if days_ago < 7:
                        score += 20
                    elif days_ago < 30:
                        score += 15
                    elif days_ago < 90:
                        score += 10
                    elif days_ago < 365:
                        score += 5
            except Exception:
                pass

        # Has languages/frameworks (10 points)
        max_score += 10
        if len(project.languages or []) >= 1:
            score += 5
        if len(project.frameworks or []) >= 1:
            score += 5

        return round((score / max_score) * 100, 1) if max_score > 0 else 0.0


class HealthCheckJobHandler(JobHandler):
    """
    Handler for periodic health check jobs.

    Re-calculates health scores for all projects.
    """

    async def execute(
        self,
        job: CatalogJob,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Execute health check job."""
        result = await db.execute(
            select(CatalogProject).where(
                CatalogProject.organization_id == job.organization_id
            )
        )
        projects = result.scalars().all()

        refresh_handler = RefreshJobHandler()
        updated = 0
        errors: List[str] = []

        for project in projects:
            path = Path(project.path)
            if not path.exists():
                continue

            try:
                project.health_score = refresh_handler._calculate_health(project, path)
                updated += 1
            except Exception as e:
                errors.append(f"{project.name}: {e}")

        await db.commit()

        return {
            "status": "completed",
            "updated": updated,
            "errors": errors[:10] if errors else None,
        }


class LLMAnalysisJobHandler(JobHandler):
    """
    Handler for LLM-powered project analysis.

    Uses LLM to:
    - Generate project summaries
    - Suggest tags
    - Detect frameworks
    - Assess complexity

    All data is normalized and properly committed to the database.
    """

    async def execute(
        self,
        job: CatalogJob,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Execute LLM analysis job."""
        from indexer_api.catalog.llm import get_embedding_service, get_llm_service

        llm = get_llm_service()
        embeddings = get_embedding_service()

        # Check LLM availability
        if not await llm.check_availability():
            return {
                "status": "error",
                "reason": "llm_unavailable",
                "message": "Ollama LLM service is not available",
            }

        # Get projects to analyze
        if job.project_id:
            result = await db.execute(
                select(CatalogProject).where(CatalogProject.id == job.project_id)
            )
            projects = [p for p in [result.scalar_one_or_none()] if p]
        else:
            # All projects in organization (not just ones without description)
            result = await db.execute(
                select(CatalogProject).where(
                    CatalogProject.organization_id == job.organization_id
                )
            )
            projects = list(result.scalars().all())

        analyzed = 0
        indexed = 0
        errors: List[str] = []

        for project in projects:
            path = Path(project.path)
            if not path.exists():
                continue

            try:
                # Read README if available
                readme_content = self._read_readme(path)

                # Get file list
                file_list = self._get_file_list(path)

                # Analyze with LLM
                analysis = await llm.analyze_project(
                    project_path=path,
                    readme_content=readme_content,
                    file_list=file_list,
                )

                if analysis:
                    # Update project with analysis results
                    if analysis.summary and not project.description:
                        project.description = analysis.summary

                    if analysis.suggested_tags:
                        existing_tags = project.tags or []
                        new_tags = list(set(existing_tags + analysis.suggested_tags))
                        project.tags = new_tags[:10]

                    if analysis.detected_type and project.type == "other":
                        project.type = analysis.detected_type

                    if analysis.detected_frameworks:
                        existing = project.frameworks or []
                        # Normalize new frameworks
                        new_frameworks = _normalize_frameworks(analysis.detected_frameworks)
                        project.frameworks = list(set(existing + new_frameworks))

                    # Store complexity in extra_metadata
                    extra = project.extra_metadata or {}
                    extra["complexity"] = analysis.complexity_assessment
                    extra["key_features"] = analysis.key_features
                    extra["improvement_suggestions"] = analysis.improvement_suggestions
                    project.extra_metadata = extra

                    # Commit project updates IMMEDIATELY
                    await db.commit()
                    analyzed += 1

                    logger.debug(
                        "llm_analysis_project_updated",
                        project=project.name,
                        has_description=bool(project.description),
                    )

                # Index for semantic search (use normalized data)
                if await embeddings.index_project(
                    project_id=project.id,
                    name=project.name,
                    description=project.description,
                    readme=readme_content,
                    tags=project.tags,
                    languages=project.languages,  # Already normalized from scan
                    frameworks=project.frameworks,  # Already normalized
                    org_id=job.organization_id,
                ):
                    indexed += 1

            except Exception as e:
                logger.error(
                    "llm_analysis_error",
                    project=project.name,
                    error=str(e),
                    exc_info=True,
                )
                errors.append(f"{project.name}: {e}")
                # Rollback any partial changes for this project
                await db.rollback()

        # Final commit for any remaining changes
        await db.commit()

        # Save embeddings to persistent storage
        embeddings.save()

        logger.info(
            "llm_analysis_completed",
            analyzed=analyzed,
            indexed=indexed,
            errors=len(errors),
        )

        return {
            "status": "completed",
            "analyzed": analyzed,
            "indexed": indexed,
            "errors": errors[:10] if errors else None,
        }

    def _read_readme(self, path: Path) -> Optional[str]:
        """Read README file if it exists."""
        for readme_name in ["README.md", "README.rst", "README.txt", "README"]:
            readme_path = path / readme_name
            if readme_path.exists():
                try:
                    return readme_path.read_text(encoding="utf-8", errors="ignore")[:5000]
                except Exception:
                    pass
        return None

    def _get_file_list(self, path: Path) -> List[str]:
        """Get list of files in project root."""
        try:
            return [
                item.name
                for item in path.iterdir()
                if not item.name.startswith(".")
            ]
        except Exception:
            return []


class EmbeddingIndexJobHandler(JobHandler):
    """
    Handler for building/rebuilding the embedding index.

    Indexes all projects for semantic search with normalized data.
    """

    async def execute(
        self,
        job: CatalogJob,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Execute embedding index job."""
        from indexer_api.catalog.llm import get_embedding_service

        embeddings = get_embedding_service()

        if not await embeddings.check_availability():
            return {
                "status": "error",
                "reason": "embedding_service_unavailable",
            }

        result = await db.execute(
            select(CatalogProject).where(
                CatalogProject.organization_id == job.organization_id
            )
        )
        projects = list(result.scalars().all())

        indexed = 0
        errors: List[str] = []

        for project in projects:
            try:
                # Read README for richer embedding
                readme_content = None
                path = Path(project.path)
                if path.exists():
                    for readme_name in ["README.md", "README.rst", "README.txt"]:
                        readme_path = path / readme_name
                        if readme_path.exists():
                            try:
                                readme_content = readme_path.read_text(
                                    encoding="utf-8", errors="ignore"
                                )[:2000]
                                break
                            except Exception:
                                pass

                # Index with normalized data (already normalized in DB)
                if await embeddings.index_project(
                    project_id=project.id,
                    name=project.name,
                    description=project.description,
                    readme=readme_content,
                    tags=project.tags,
                    languages=project.languages,
                    frameworks=project.frameworks,
                    org_id=job.organization_id,
                ):
                    indexed += 1

            except Exception as e:
                errors.append(f"{project.name}: {e}")

        # Persist index
        embeddings.save()

        logger.info(
            "embedding_index_completed",
            indexed=indexed,
            total=len(projects),
            errors=len(errors),
        )

        return {
            "status": "completed",
            "indexed": indexed,
            "total": len(projects),
            "errors": errors[:10] if errors else None,
        }


class QualityAssessmentJobHandler(JobHandler):
    """
    Handler for quality assessment jobs.

    Performs comprehensive quality assessment on projects:
    - Scans filesystem for quality indicators
    - Uses LLM to evaluate code quality and production readiness
    - Generates improvement recommendations
    """

    async def execute(
        self,
        job: CatalogJob,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Execute quality assessment job."""
        from indexer_api.catalog.llm import get_quality_service

        quality_service = get_quality_service()

        # Get projects to assess
        if job.project_id:
            result = await db.execute(
                select(CatalogProject).where(CatalogProject.id == job.project_id)
            )
            projects = [p for p in [result.scalar_one_or_none()] if p]
        else:
            # Get all projects (or only unassessed ones based on job config)
            force_refresh = (job.result or {}).get("force_refresh", False)
            query = select(CatalogProject).where(
                CatalogProject.organization_id == job.organization_id
            )
            if not force_refresh:
                # Only assess projects that haven't been assessed
                query = query.where(
                    CatalogProject.quality_score == None  # noqa: E711
                )
            result = await db.execute(query)
            projects = list(result.scalars().all())

        assessed = 0
        errors: List[str] = []

        for project in projects:
            path = Path(project.path)
            if not path.exists():
                continue

            try:
                # Read README if available
                readme_content = self._read_readme(path)
                file_list = self._get_file_list(path)

                # Perform quality assessment
                assessment = await quality_service.assess_project(
                    project_path=path,
                    readme_content=readme_content,
                    file_list=file_list,
                    existing_description=project.description,
                    languages=project.languages,
                    frameworks=project.frameworks,
                )

                if assessment:
                    # Update project with quality data
                    project.production_readiness = assessment.production_readiness
                    project.quality_score = assessment.quality_score
                    project.quality_assessment = assessment.to_dict()

                    # Scan and store quality indicators
                    indicators = quality_service.scan_quality_indicators(path)
                    project.quality_indicators = indicators.to_dict()

                    project.last_quality_check_at = datetime.now(timezone.utc)

                    # Commit immediately for each project
                    await db.commit()
                    assessed += 1

                    # Update job result with progress
                    job.result = {
                        "status": "running",
                        "assessed": assessed,
                        "total": len(projects),
                    }
                    await db.commit()

                    logger.debug(
                        "quality_assessment_completed",
                        project=project.name,
                        readiness=assessment.production_readiness,
                        score=assessment.quality_score,
                    )

            except Exception as e:
                logger.error(
                    "quality_assessment_error",
                    project=project.name,
                    error=str(e),
                    exc_info=True,
                )
                errors.append(f"{project.name}: {e}")
                await db.rollback()

        logger.info(
            "quality_assessment_job_completed",
            assessed=assessed,
            total=len(projects),
            errors=len(errors),
        )

        return {
            "status": "completed",
            "assessed": assessed,
            "total": len(projects),
            "errors": errors[:10] if errors else None,
        }

    def _read_readme(self, path: Path) -> Optional[str]:
        """Read README file if it exists."""
        for readme_name in ["README.md", "README.rst", "README.txt", "README"]:
            readme_path = path / readme_name
            if readme_path.exists():
                try:
                    return readme_path.read_text(encoding="utf-8", errors="ignore")[:5000]
                except Exception:
                    pass
        return None

    def _get_file_list(self, path: Path) -> List[str]:
        """Get list of files in project root."""
        try:
            return [
                item.name
                for item in path.iterdir()
                if not item.name.startswith(".")
            ]
        except Exception:
            return []


# Job handler registry
JOB_HANDLERS: Dict[str, JobHandler] = {
    "scan": ScanJobHandler(),
    "refresh": RefreshJobHandler(),
    "health_check": HealthCheckJobHandler(),
    "llm_analysis": LLMAnalysisJobHandler(),
    "embedding_index": EmbeddingIndexJobHandler(),
    "quality_assessment": QualityAssessmentJobHandler(),
}


async def execute_job(job: CatalogJob, db: AsyncSession) -> Dict[str, Any]:
    """
    Execute a job using the appropriate handler.

    Args:
        job: The job to execute
        db: Database session

    Returns:
        Result dictionary from the job handler
    """
    handler = JOB_HANDLERS.get(job.job_type)
    if not handler:
        return {"status": "error", "reason": f"unknown_job_type: {job.job_type}"}

    return await handler.execute(job, db)
