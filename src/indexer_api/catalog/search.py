"""
Catalog search with FTS5 and semantic search.

Provides hybrid search combining keyword (FTS5) and semantic (embeddings) search
with Reciprocal Rank Fusion (RRF) for result merging.

This module is designed with production-grade reliability:
- Thread-safe singleton pattern for global search engine
- Automatic semantic search enablement when embeddings are available
- Case-insensitive filtering for all natural language queries
- Graceful degradation when services are unavailable
"""
from __future__ import annotations

import asyncio
import os
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from indexer_api.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class SearchResult:
    """
    An immutable search result with relevance score.

    Using frozen=True for hashability and immutability.
    Using slots=True for memory efficiency.
    """
    id: str
    name: str
    title: Optional[str]
    description: Optional[str]
    path: str
    type: str
    lifecycle: str
    languages: Tuple[str, ...]  # Immutable tuple instead of list
    frameworks: Tuple[str, ...]  # Immutable tuple instead of list
    health_score: Optional[float]
    production_readiness: str
    quality_score: Optional[float]
    relevance_score: float

    @classmethod
    def from_project(
        cls,
        project: Any,
        relevance_score: float = 1.0,
    ) -> "SearchResult":
        """Create SearchResult from a CatalogProject model."""
        return cls(
            id=project.id,
            name=project.name,
            title=project.title,
            description=project.description,
            path=project.path,
            type=project.type or "other",
            lifecycle=project.lifecycle or "active",
            languages=tuple(project.languages or []),
            frameworks=tuple(project.frameworks or []),
            health_score=project.health_score,
            production_readiness=getattr(project, 'production_readiness', None) or "unknown",
            quality_score=getattr(project, 'quality_score', None),
            relevance_score=relevance_score,
        )


class CatalogSearch:
    """
    Hybrid search engine for the project catalog.

    Combines FTS5 keyword search with semantic (embedding) search,
    using Reciprocal Rank Fusion (RRF) to merge results.

    Features:
    - Automatic semantic search enablement when embeddings are available
    - Case-insensitive filtering for natural language queries
    - Graceful fallback to LIKE search when FTS5 is unavailable
    - Thread-safe operations
    """

    # RRF constant - standard value from literature
    RRF_K: int = 60

    def __init__(
        self,
        semantic_weight: float = 0.4,
        fts_weight: float = 0.6,
        auto_enable_semantic: bool = True,
    ):
        """
        Initialize the search engine.

        Args:
            semantic_weight: Weight for semantic results in RRF (0.0-1.0)
            fts_weight: Weight for FTS results in RRF (0.0-1.0)
            auto_enable_semantic: Automatically enable semantic search when available
        """
        if not 0.0 <= semantic_weight <= 1.0:
            raise ValueError("semantic_weight must be between 0.0 and 1.0")
        if not 0.0 <= fts_weight <= 1.0:
            raise ValueError("fts_weight must be between 0.0 and 1.0")

        self._semantic_weight = semantic_weight
        self._fts_weight = fts_weight
        self._auto_enable_semantic = auto_enable_semantic
        self._semantic_available: Optional[bool] = None
        self._lock = threading.Lock()

    @property
    def semantic_weight(self) -> float:
        """Weight for semantic search results."""
        return self._semantic_weight

    @property
    def fts_weight(self) -> float:
        """Weight for FTS search results."""
        return self._fts_weight

    async def _is_semantic_available(self) -> bool:
        """
        Check if semantic search is available.

        Caches the result after first check for performance.
        """
        if self._semantic_available is not None:
            return self._semantic_available

        if not self._auto_enable_semantic:
            self._semantic_available = False
            return False

        try:
            from indexer_api.catalog.llm import get_embedding_service
            embeddings = get_embedding_service()
            self._semantic_available = await embeddings.check_availability()
        except Exception as e:
            logger.debug("semantic_availability_check_failed", error=str(e))
            self._semantic_available = False

        return self._semantic_available

    def reset_semantic_cache(self) -> None:
        """Reset the semantic availability cache to force re-check."""
        with self._lock:
            self._semantic_available = None

    async def search(
        self,
        db: AsyncSession,
        org_id: str,
        query: str,
        limit: int = 20,
        include_semantic: bool = True,
    ) -> List[SearchResult]:
        """
        Search the catalog using hybrid search.

        Combines FTS and semantic search results using RRF.
        Falls back gracefully if any component is unavailable.

        Args:
            db: Database session
            org_id: Organization ID to filter by
            query: Search query string
            limit: Maximum results to return
            include_semantic: Whether to include semantic search

        Returns:
            List of SearchResult objects sorted by relevance
        """
        if not query or not query.strip():
            return []

        query = query.strip()

        # Always run FTS search
        fts_results = await self._fts_search(db, org_id, query, limit * 2)

        # Try semantic search if enabled and available
        semantic_results: List[SearchResult] = []
        if include_semantic and await self._is_semantic_available():
            try:
                semantic_results = await self._semantic_search(
                    db, org_id, query, limit * 2
                )
            except Exception as e:
                logger.warning("semantic_search_failed", error=str(e))
                # Continue with FTS-only

        # Merge results using RRF
        if semantic_results:
            return self._rrf_merge(fts_results, semantic_results, limit)
        else:
            return fts_results[:limit]

    async def _fts_search(
        self,
        db: AsyncSession,
        org_id: str,
        query: str,
        limit: int,
    ) -> List[SearchResult]:
        """
        Full-text search using FTS5.

        Falls back to LIKE-based search if FTS5 is unavailable.
        """
        try:
            # FTS5 query with BM25 scoring
            sql = text("""
                SELECT
                    p.id, p.name, p.title, p.description, p.path,
                    p.type, p.lifecycle, p.languages, p.frameworks,
                    p.health_score,
                    bm25(catalog_projects_fts) as score
                FROM catalog_projects_fts fts
                JOIN catalog_projects p ON p.id = fts.rowid
                WHERE catalog_projects_fts MATCH :query
                  AND p.organization_id = :org_id
                ORDER BY score
                LIMIT :limit
            """)

            result = await db.execute(
                sql,
                {"query": query, "org_id": org_id, "limit": limit},
            )
            rows = result.fetchall()

            return [
                SearchResult(
                    id=row.id,
                    name=row.name,
                    title=row.title,
                    description=row.description,
                    path=row.path,
                    type=row.type or "other",
                    lifecycle=row.lifecycle or "active",
                    languages=tuple(row.languages or []),
                    frameworks=tuple(row.frameworks or []),
                    health_score=row.health_score,
                    relevance_score=abs(row.score) if row.score else 1.0,
                )
                for row in rows
            ]

        except Exception as e:
            logger.debug("fts5_unavailable", error=str(e))
            return await self._like_search(db, org_id, query, limit)

    async def _like_search(
        self,
        db: AsyncSession,
        org_id: str,
        query: str,
        limit: int,
    ) -> List[SearchResult]:
        """
        Fallback LIKE-based search when FTS5 is unavailable.

        Uses case-insensitive matching on name, title, description, and path.
        """
        search_term = f"%{query}%"

        sql = text("""
            SELECT
                id, name, title, description, path,
                type, lifecycle, languages, frameworks,
                health_score
            FROM catalog_projects
            WHERE organization_id = :org_id
              AND (
                name LIKE :term COLLATE NOCASE
                OR title LIKE :term COLLATE NOCASE
                OR description LIKE :term COLLATE NOCASE
                OR path LIKE :term COLLATE NOCASE
              )
            LIMIT :limit
        """)

        result = await db.execute(
            sql,
            {"org_id": org_id, "term": search_term, "limit": limit},
        )
        rows = result.fetchall()

        return [
            SearchResult(
                id=row.id,
                name=row.name,
                title=row.title,
                description=row.description,
                path=row.path,
                type=row.type or "other",
                lifecycle=row.lifecycle or "active",
                languages=tuple(row.languages or []),
                frameworks=tuple(row.frameworks or []),
                health_score=row.health_score,
                relevance_score=1.0,
            )
            for row in rows
        ]

    async def _semantic_search(
        self,
        db: AsyncSession,
        org_id: str,
        query: str,
        limit: int,
        use_query_expansion: bool = True,
    ) -> List[SearchResult]:
        """
        Semantic search using embeddings.

        Finds projects with similar semantic meaning to the query.
        Uses query expansion for better recall.
        """
        from indexer_api.catalog.llm import get_embedding_service, get_llm_service
        from indexer_api.catalog.models import CatalogProject

        embeddings = get_embedding_service()

        # Optionally expand query for better semantic matching
        search_query = query
        if use_query_expansion:
            try:
                llm = get_llm_service()
                if await llm.check_availability():
                    expanded = await llm.expand_query(query)
                    if expanded and expanded != query:
                        search_query = expanded
                        logger.debug("query_expanded", original=query, expanded=expanded)
            except Exception as e:
                logger.debug("query_expansion_failed", error=str(e))

        # Search for similar projects (lower min_score since we filter later)
        results = await embeddings.search_similar(
            query=search_query,
            limit=limit,
            org_id=org_id,
            min_score=0.2,  # Lower threshold for initial retrieval
        )

        if not results:
            return []

        # Fetch full project data from database
        project_ids = [r[0] for r in results]
        scores = {r[0]: r[1] for r in results}

        result = await db.execute(
            select(CatalogProject).where(
                CatalogProject.id.in_(project_ids),
                CatalogProject.organization_id == org_id,
            )
        )
        projects = {p.id: p for p in result.scalars().all()}

        # Build results in relevance order
        search_results = []
        for project_id in project_ids:
            if project_id in projects:
                p = projects[project_id]
                search_results.append(SearchResult.from_project(
                    p,
                    relevance_score=scores.get(project_id, 0.0),
                ))

        return search_results

    async def natural_language_search(
        self,
        db: AsyncSession,
        org_id: str,
        query: str,
        limit: int = 20,
    ) -> List[SearchResult]:
        """
        Search using natural language query understanding.

        Uses LLM to parse the query into structured filters,
        then combines with hybrid search.

        Features:
        - Case-insensitive filtering
        - Partial type matching (e.g., "web" matches "web", "web_app")
        - Progressive filter relaxation if too few results
        - Graceful fallback to pure semantic search

        Args:
            db: Database session
            org_id: Organization ID
            query: Natural language query (e.g., "Python web frameworks")
            limit: Maximum results

        Returns:
            Search results with relevance scores
        """
        from indexer_api.catalog.llm import get_llm_service

        llm = get_llm_service()

        # Parse the query with LLM
        parsed = await llm.understand_query(query)

        # Build search query from keywords
        keywords = parsed.get("keywords", [])
        search_query = " ".join(keywords) if keywords else query

        # Run hybrid search with extra results for filtering
        results = await self.search(db, org_id, search_query, limit * 5)

        # If no results from hybrid search, try pure semantic
        if not results:
            logger.debug("nlu_fallback_semantic", query=query)
            results = await self._semantic_search(db, org_id, query, limit * 3)

        if not results:
            return []

        # Extract filters from NLU response
        filters = parsed.get("filters", {})

        # Pre-process filter values for case-insensitive matching
        filter_languages: Set[str] = {
            lang.lower() for lang in (filters.get("languages") or [])
        }
        filter_frameworks: Set[str] = {
            fw.lower() for fw in (filters.get("frameworks") or [])
        }
        filter_type: Optional[str] = (
            filters.get("type", "").lower() if filters.get("type") else None
        )
        filter_lifecycle: Optional[str] = (
            filters.get("lifecycle", "").lower() if filters.get("lifecycle") else None
        )
        min_health: Optional[float] = filters.get("min_health_score")

        # Try strict filtering first
        filtered_results = self._apply_filters(
            results=results,
            filter_languages=filter_languages,
            filter_frameworks=filter_frameworks,
            filter_type=filter_type,
            filter_lifecycle=filter_lifecycle,
            min_health=min_health,
            partial_type_match=True,  # Allow "web" to match "web_app"
            limit=limit,
        )

        # If too few results, relax type filter
        if len(filtered_results) < min(limit // 2, 3) and filter_type:
            logger.debug("nlu_relaxing_type_filter", query=query, filter_type=filter_type)
            filtered_results = self._apply_filters(
                results=results,
                filter_languages=filter_languages,
                filter_frameworks=filter_frameworks,
                filter_type=None,  # Remove type filter
                filter_lifecycle=filter_lifecycle,
                min_health=min_health,
                partial_type_match=True,
                limit=limit,
            )

        # If still too few, keep only language filter
        if len(filtered_results) < min(limit // 2, 3) and (filter_languages or filter_frameworks):
            logger.debug("nlu_relaxing_all_filters", query=query)
            filtered_results = self._apply_filters(
                results=results,
                filter_languages=filter_languages,
                filter_frameworks=None,
                filter_type=None,
                filter_lifecycle=None,
                min_health=None,
                partial_type_match=True,
                limit=limit,
            )

        # Last resort: return unfiltered results (semantic/hybrid is still relevant)
        if len(filtered_results) < min(limit // 2, 3):
            logger.debug("nlu_using_unfiltered", query=query)
            return results[:limit]

        return filtered_results

    def _apply_filters(
        self,
        results: List[SearchResult],
        filter_languages: Optional[Set[str]],
        filter_frameworks: Optional[Set[str]],
        filter_type: Optional[str],
        filter_lifecycle: Optional[str],
        min_health: Optional[float],
        partial_type_match: bool = False,
        limit: int = 20,
    ) -> List[SearchResult]:
        """
        Apply filters to search results.

        Args:
            results: Search results to filter
            filter_languages: Set of language names (lowercase)
            filter_frameworks: Set of framework names (lowercase)
            filter_type: Project type to match (lowercase)
            filter_lifecycle: Lifecycle state to match (lowercase)
            min_health: Minimum health score
            partial_type_match: If True, "web" matches "web_app"
            limit: Maximum results to return

        Returns:
            Filtered results
        """
        filtered: List[SearchResult] = []

        for result in results:
            # Filter by language (case-insensitive)
            if filter_languages:
                result_languages = {lang.lower() for lang in result.languages}
                if not filter_languages.intersection(result_languages):
                    continue

            # Filter by framework (case-insensitive)
            if filter_frameworks:
                result_frameworks = {fw.lower() for fw in result.frameworks}
                if not filter_frameworks.intersection(result_frameworks):
                    continue

            # Filter by type (case-insensitive, with partial matching option)
            if filter_type:
                result_type = result.type.lower()
                if partial_type_match:
                    # "web" matches "web", "web_app", "web-app"
                    if not (filter_type in result_type or result_type in filter_type):
                        continue
                elif result_type != filter_type:
                    continue

            # Filter by lifecycle (case-insensitive)
            if filter_lifecycle and result.lifecycle.lower() != filter_lifecycle:
                continue

            # Filter by minimum health score
            if min_health is not None:
                if result.health_score is None or result.health_score < min_health:
                    continue

            filtered.append(result)

            if len(filtered) >= limit:
                break

        return filtered

    async def find_similar(
        self,
        db: AsyncSession,
        project_id: str,
        limit: int = 5,
    ) -> List[SearchResult]:
        """
        Find projects similar to a given project.

        Uses embedding similarity to find related projects.

        Args:
            db: Database session
            project_id: ID of the reference project
            limit: Maximum similar projects to return

        Returns:
            List of similar projects (excluding the reference project)
        """
        from indexer_api.catalog.llm import get_embedding_service
        from indexer_api.catalog.models import CatalogProject

        embeddings = get_embedding_service()

        # Get similar projects from embedding store
        results = await embeddings.find_related(project_id, limit + 1)  # +1 to exclude self

        if not results:
            return []

        # Filter out the source project and fetch details
        project_ids = [r[0] for r in results if r[0] != project_id][:limit]
        scores = {r[0]: r[1] for r in results}

        if not project_ids:
            return []

        result = await db.execute(
            select(CatalogProject).where(CatalogProject.id.in_(project_ids))
        )
        projects = {p.id: p for p in result.scalars().all()}

        # Build results in similarity order
        search_results = []
        for pid in project_ids:
            if pid in projects:
                search_results.append(SearchResult.from_project(
                    projects[pid],
                    relevance_score=scores.get(pid, 0.0),
                ))

        return search_results

    def _rrf_merge(
        self,
        fts_results: List[SearchResult],
        semantic_results: List[SearchResult],
        limit: int,
    ) -> List[SearchResult]:
        """
        Merge results using Reciprocal Rank Fusion (RRF).

        RRF score = sum(weight_i / (k + rank_i)) for each result list

        This is a proven method for combining ranked lists from
        different retrieval systems.

        Args:
            fts_results: Results from FTS search
            semantic_results: Results from semantic search
            limit: Maximum results to return

        Returns:
            Merged and re-ranked results
        """
        # Accumulate RRF scores by project ID
        scores: Dict[str, Tuple[float, SearchResult]] = {}

        # Score FTS results
        for rank, result in enumerate(fts_results):
            rrf_score = self._fts_weight / (self.RRF_K + rank + 1)
            if result.id in scores:
                old_score, old_result = scores[result.id]
                scores[result.id] = (old_score + rrf_score, old_result)
            else:
                scores[result.id] = (rrf_score, result)

        # Score semantic results
        for rank, result in enumerate(semantic_results):
            rrf_score = self._semantic_weight / (self.RRF_K + rank + 1)
            if result.id in scores:
                old_score, old_result = scores[result.id]
                scores[result.id] = (old_score + rrf_score, old_result)
            else:
                scores[result.id] = (rrf_score, result)

        # Sort by combined RRF score (descending)
        sorted_items = sorted(
            scores.values(),
            key=lambda x: x[0],
            reverse=True,
        )

        # Return top results with updated relevance scores
        return [
            SearchResult(
                id=result.id,
                name=result.name,
                title=result.title,
                description=result.description,
                path=result.path,
                type=result.type,
                lifecycle=result.lifecycle,
                languages=result.languages,
                frameworks=result.frameworks,
                health_score=result.health_score,
                relevance_score=score,
            )
            for score, result in sorted_items[:limit]
        ]


# Thread-safe singleton implementation
_search_engine: Optional[CatalogSearch] = None
_search_lock = threading.Lock()


def get_search_engine() -> CatalogSearch:
    """
    Get the global search engine instance.

    Thread-safe singleton pattern. Semantic search is automatically
    enabled when the embedding service is available.

    Returns:
        Global CatalogSearch instance
    """
    global _search_engine

    if _search_engine is not None:
        return _search_engine

    with _search_lock:
        # Double-check after acquiring lock
        if _search_engine is not None:
            return _search_engine

        # Read weights from environment
        semantic_weight = float(os.environ.get("CATALOG_SEMANTIC_WEIGHT", "0.4"))
        fts_weight = float(os.environ.get("CATALOG_FTS_WEIGHT", "0.6"))
        auto_enable = os.environ.get("CATALOG_SEMANTIC_AUTO", "true").lower() != "false"

        _search_engine = CatalogSearch(
            semantic_weight=semantic_weight,
            fts_weight=fts_weight,
            auto_enable_semantic=auto_enable,
        )

        logger.info(
            "search_engine_initialized",
            semantic_weight=semantic_weight,
            fts_weight=fts_weight,
            auto_enable_semantic=auto_enable,
        )

        return _search_engine


def reset_search_engine() -> None:
    """
    Reset the global search engine instance.

    Useful for testing or when configuration changes.
    """
    global _search_engine

    with _search_lock:
        _search_engine = None
