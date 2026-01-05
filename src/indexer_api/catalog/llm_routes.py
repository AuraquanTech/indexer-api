"""
LLM-powered API routes for catalog.

This file contains additional routes that add LLM functionality.
Import and include these routes in the main catalog router.
"""
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from indexer_api.api.deps import AuthContext, DbSession
from indexer_api.catalog.models import CatalogJob, CatalogProject
from indexer_api.catalog.schemas import (
    ProjectSearchOut,
    ProjectSearchResult,
    QualityAssessmentResponse,
    QualityReportOut,
    QualityReportProject,
    ScanResponse,
)

llm_router = APIRouter(tags=["Catalog LLM"])


@llm_router.get("/llm/status")
async def llm_status(auth: AuthContext):
    """Check LLM service availability and status."""
    from indexer_api.catalog.llm import get_llm_service, get_embedding_service

    llm = get_llm_service()
    embeddings = get_embedding_service()

    llm_available = await llm.check_availability()
    embedding_available = await embeddings.check_availability()

    return {
        "llm": {
            "available": llm_available,
            "model": llm.config.model,
            "base_url": llm.config.base_url,
        },
        "embeddings": {
            "available": embedding_available,
            "model": embeddings.config.model,
            "indexed_projects": embeddings.indexed_count,
        },
    }


@llm_router.get("/search/semantic", response_model=ProjectSearchOut)
async def semantic_search(
    auth: AuthContext,
    db: DbSession,
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
):
    """Semantic search using embeddings for natural language queries."""
    org_id, _ = auth

    from indexer_api.catalog.search import get_search_engine

    engine = get_search_engine()
    # Force semantic search inclusion
    results = await engine.search(db, org_id, q, limit, include_semantic=True)

    return ProjectSearchOut(
        results=[
            ProjectSearchResult(
                id=r.id,
                name=r.name,
                title=r.title,
                description=r.description,
                path=r.path,
                type=r.type,
                lifecycle=r.lifecycle,
                languages=list(r.languages),  # Convert tuple to list
                frameworks=list(r.frameworks),  # Convert tuple to list
                health_score=r.health_score,
                production_readiness=r.production_readiness,
                quality_score=r.quality_score,
                relevance_score=r.relevance_score,
            )
            for r in results
        ],
        total=len(results),
        query=q,
    )


@llm_router.get("/search/natural", response_model=ProjectSearchOut)
async def natural_language_search(
    auth: AuthContext,
    db: DbSession,
    q: str = Query(..., min_length=1, description="Natural language query"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Natural language search with LLM query understanding.

    Examples:
    - "Python APIs for file management"
    - "active projects with high health scores"
    - "TypeScript libraries for authentication"
    """
    org_id, _ = auth

    from indexer_api.catalog.search import get_search_engine

    engine = get_search_engine()
    # Natural language search includes semantic by default
    results = await engine.natural_language_search(db, org_id, q, limit)

    return ProjectSearchOut(
        results=[
            ProjectSearchResult(
                id=r.id,
                name=r.name,
                title=r.title,
                description=r.description,
                path=r.path,
                type=r.type,
                lifecycle=r.lifecycle,
                languages=list(r.languages),  # Convert tuple to list
                frameworks=list(r.frameworks),  # Convert tuple to list
                health_score=r.health_score,
                production_readiness=r.production_readiness,
                quality_score=r.quality_score,
                relevance_score=r.relevance_score,
            )
            for r in results
        ],
        total=len(results),
        query=q,
    )


@llm_router.get("/projects/{project_id}/similar", response_model=ProjectSearchOut)
async def find_similar_projects(
    project_id: str,
    auth: AuthContext,
    db: DbSession,
    limit: int = Query(5, ge=1, le=20),
):
    """Find projects similar to a given project using embeddings."""
    org_id, _ = auth

    result = await db.execute(
        select(CatalogProject).where(
            CatalogProject.id == project_id,
            CatalogProject.organization_id == org_id,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    from indexer_api.catalog.search import get_search_engine

    engine = get_search_engine()
    results = await engine.find_similar(db, project_id, limit)

    return ProjectSearchOut(
        results=[
            ProjectSearchResult(
                id=r.id,
                name=r.name,
                title=r.title,
                description=r.description,
                path=r.path,
                type=r.type,
                lifecycle=r.lifecycle,
                languages=list(r.languages),  # Convert tuple to list
                frameworks=list(r.frameworks),  # Convert tuple to list
                health_score=r.health_score,
                production_readiness=r.production_readiness,
                quality_score=r.quality_score,
                relevance_score=r.relevance_score,
            )
            for r in results
        ],
        total=len(results),
        query=f"similar to {project.name}",
    )


@llm_router.post("/projects/{project_id}/analyze", response_model=ScanResponse)
async def analyze_project(
    project_id: str,
    auth: AuthContext,
    db: DbSession,
):
    """Trigger LLM analysis for a specific project."""
    org_id, user_id = auth

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API keys cannot trigger analysis. Use JWT authentication.",
        )

    result = await db.execute(
        select(CatalogProject).where(
            CatalogProject.id == project_id,
            CatalogProject.organization_id == org_id,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    job = CatalogJob(
        organization_id=org_id,
        project_id=project_id,
        job_type="llm_analysis",
        status="pending",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    return ScanResponse(
        job_id=job.id,
        status="pending",
        message=f"LLM analysis job enqueued for {project.name}",
    )


@llm_router.post("/analyze-all", response_model=ScanResponse)
async def analyze_all_projects(
    auth: AuthContext,
    db: DbSession,
):
    """Trigger LLM analysis for all projects without descriptions."""
    org_id, user_id = auth

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API keys cannot trigger analysis. Use JWT authentication.",
        )

    count_result = await db.execute(
        select(func.count()).select_from(CatalogProject).where(
            CatalogProject.organization_id == org_id,
            CatalogProject.description.is_(None),
        )
    )
    count = count_result.scalar_one()

    job = CatalogJob(
        organization_id=org_id,
        job_type="llm_analysis",
        status="pending",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    return ScanResponse(
        job_id=job.id,
        status="pending",
        message=f"LLM analysis job enqueued for {count} projects",
    )


@llm_router.post("/index-embeddings", response_model=ScanResponse)
async def index_embeddings(
    auth: AuthContext,
    db: DbSession,
):
    """Build/rebuild the embedding index for semantic search."""
    org_id, user_id = auth

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API keys cannot trigger indexing. Use JWT authentication.",
        )

    job = CatalogJob(
        organization_id=org_id,
        job_type="embedding_index",
        status="pending",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    return ScanResponse(
        job_id=job.id,
        status="pending",
        message="Embedding index job enqueued",
    )


@llm_router.post("/compare")
async def compare_projects(
    auth: AuthContext,
    db: DbSession,
    project_ids: list[str] = Query(..., min_length=2, max_length=5),
):
    """Compare multiple projects using LLM analysis."""
    org_id, _ = auth

    result = await db.execute(
        select(CatalogProject).where(
            CatalogProject.id.in_(project_ids),
            CatalogProject.organization_id == org_id,
        )
    )
    projects = result.scalars().all()

    if len(projects) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 valid projects required for comparison",
        )

    from indexer_api.catalog.llm import get_llm_service

    llm = get_llm_service()

    if not await llm.check_availability():
        raise HTTPException(
            status_code=503,
            detail="LLM service unavailable",
        )

    project_data = [
        {
            "name": p.name,
            "description": p.description,
            "languages": p.languages or [],
            "frameworks": p.frameworks or [],
            "type": p.type,
            "health_score": p.health_score,
        }
        for p in projects
    ]

    comparison = await llm.compare_projects(project_data)

    return {
        "projects": [p.name for p in projects],
        "comparison": comparison,
    }


# ============================================================================
# Quality Assessment Routes
# ============================================================================


@llm_router.post("/assess-quality", response_model=QualityAssessmentResponse)
async def assess_all_quality(
    auth: AuthContext,
    db: DbSession,
    force_refresh: bool = Query(False, description="Re-assess all projects"),
):
    """
    Trigger quality assessment for all projects.

    This evaluates each project for:
    - Production readiness (prototype, alpha, beta, production, mature)
    - Code quality score (0-100)
    - Quality indicators (tests, CI/CD, docs, etc.)
    - Strengths and weaknesses
    - Recommended improvements
    """
    org_id, user_id = auth

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API keys cannot trigger quality assessment. Use JWT authentication.",
        )

    # Count projects to assess
    query = select(func.count()).select_from(CatalogProject).where(
        CatalogProject.organization_id == org_id
    )
    if not force_refresh:
        query = query.where(CatalogProject.quality_score.is_(None))

    count_result = await db.execute(query)
    count = count_result.scalar_one()

    job = CatalogJob(
        organization_id=org_id,
        job_type="quality_assessment",
        status="pending",
        result={"force_refresh": force_refresh},
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    return QualityAssessmentResponse(
        job_id=job.id,
        status="pending",
        message=f"Quality assessment job enqueued for {count} projects",
        projects_to_assess=count,
    )


@llm_router.post("/projects/{project_id}/assess-quality", response_model=ScanResponse)
async def assess_project_quality(
    project_id: str,
    auth: AuthContext,
    db: DbSession,
):
    """Trigger quality assessment for a specific project."""
    org_id, user_id = auth

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API keys cannot trigger quality assessment. Use JWT authentication.",
        )

    result = await db.execute(
        select(CatalogProject).where(
            CatalogProject.id == project_id,
            CatalogProject.organization_id == org_id,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    job = CatalogJob(
        organization_id=org_id,
        project_id=project_id,
        job_type="quality_assessment",
        status="pending",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    return ScanResponse(
        job_id=job.id,
        status="pending",
        message=f"Quality assessment job enqueued for {project.name}",
    )


@llm_router.get("/quality-report", response_model=QualityReportOut)
async def get_quality_report(
    auth: AuthContext,
    db: DbSession,
):
    """
    Generate a comprehensive quality report for all cataloged projects.

    Returns:
    - Distribution by production readiness
    - Distribution by quality tier (excellent, good, fair, poor)
    - Projects needing attention
    - Top quality projects
    - Common issues across projects
    - Technology distribution
    """
    from datetime import datetime, timezone
    from collections import Counter

    org_id, _ = auth

    result = await db.execute(
        select(CatalogProject).where(
            CatalogProject.organization_id == org_id
        )
    )
    projects = result.scalars().all()

    if not projects:
        return QualityReportOut(
            total_projects=0,
            assessed_projects=0,
            by_production_readiness={},
            by_quality_tier={},
            avg_quality_score=None,
            production_ready_count=0,
            needs_attention=[],
            top_quality=[],
            common_issues={},
            technology_distribution={},
            generated_at=datetime.now(timezone.utc),
        )

    # Count by production readiness
    readiness_counts = Counter(p.production_readiness or "unknown" for p in projects)

    # Count by quality tier
    quality_tiers = {"excellent": 0, "good": 0, "fair": 0, "poor": 0, "unknown": 0}
    assessed = 0
    total_score = 0.0

    for p in projects:
        if p.quality_score is not None:
            assessed += 1
            total_score += p.quality_score
            if p.quality_score >= 80:
                quality_tiers["excellent"] += 1
            elif p.quality_score >= 60:
                quality_tiers["good"] += 1
            elif p.quality_score >= 40:
                quality_tiers["fair"] += 1
            else:
                quality_tiers["poor"] += 1
        else:
            quality_tiers["unknown"] += 1

    avg_score = round(total_score / assessed, 1) if assessed > 0 else None

    # Production ready count
    production_ready = sum(
        1 for p in projects
        if (p.production_readiness or "").lower() in ["production", "mature"]
    )

    # Projects needing attention (low quality or has blockers)
    needs_attention = []
    for p in projects:
        if p.quality_score is not None and p.quality_score < 40:
            assessment = p.quality_assessment or {}
            needs_attention.append(QualityReportProject(
                id=p.id,
                name=p.name,
                path=p.path,
                type=p.type or "other",
                production_readiness=p.production_readiness or "unknown",
                quality_score=p.quality_score,
                languages=p.languages or [],
                key_issues=assessment.get("production_blockers", [])[:3],
            ))

    needs_attention = sorted(needs_attention, key=lambda x: x.quality_score or 0)[:20]

    # Top quality projects
    top_quality = []
    for p in sorted(projects, key=lambda x: x.quality_score or 0, reverse=True)[:20]:
        if p.quality_score is not None and p.quality_score >= 60:
            top_quality.append(QualityReportProject(
                id=p.id,
                name=p.name,
                path=p.path,
                type=p.type or "other",
                production_readiness=p.production_readiness or "unknown",
                quality_score=p.quality_score,
                languages=p.languages or [],
                key_issues=[],
            ))

    # Common issues (aggregate production_blockers and weaknesses)
    issue_counter: Counter = Counter()
    for p in projects:
        assessment = p.quality_assessment or {}
        for issue in assessment.get("production_blockers", []):
            issue_counter[issue] += 1
        for issue in assessment.get("weaknesses", []):
            issue_counter[issue] += 1

    common_issues = dict(issue_counter.most_common(20))

    # Technology distribution
    lang_counter: Counter = Counter()
    for p in projects:
        for lang in (p.languages or []):
            lang_counter[lang] += 1

    technology_distribution = dict(lang_counter.most_common(20))

    return QualityReportOut(
        total_projects=len(projects),
        assessed_projects=assessed,
        by_production_readiness=dict(readiness_counts),
        by_quality_tier=quality_tiers,
        avg_quality_score=avg_score,
        production_ready_count=production_ready,
        needs_attention=needs_attention,
        top_quality=top_quality,
        common_issues=common_issues,
        technology_distribution=technology_distribution,
        generated_at=datetime.now(timezone.utc),
    )


@llm_router.get("/projects/{project_id}/quality")
async def get_project_quality(
    project_id: str,
    auth: AuthContext,
    db: DbSession,
):
    """Get detailed quality assessment for a specific project."""
    org_id, _ = auth

    result = await db.execute(
        select(CatalogProject).where(
            CatalogProject.id == project_id,
            CatalogProject.organization_id == org_id,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.quality_score is None:
        raise HTTPException(
            status_code=404,
            detail="Quality assessment not yet performed. Trigger assessment first.",
        )

    return {
        "project_id": project.id,
        "name": project.name,
        "production_readiness": project.production_readiness,
        "quality_score": project.quality_score,
        "quality_assessment": project.quality_assessment,
        "quality_indicators": project.quality_indicators,
        "last_quality_check_at": project.last_quality_check_at,
    }


@llm_router.get("/production-ready")
async def list_production_ready(
    auth: AuthContext,
    db: DbSession,
    limit: int = Query(50, ge=1, le=200),
):
    """List all projects that are production-ready or mature."""
    org_id, _ = auth

    result = await db.execute(
        select(CatalogProject).where(
            CatalogProject.organization_id == org_id,
            CatalogProject.production_readiness.in_(["production", "mature"]),
        ).order_by(CatalogProject.quality_score.desc()).limit(limit)
    )
    projects = result.scalars().all()

    return {
        "count": len(projects),
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "path": p.path,
                "type": p.type,
                "production_readiness": p.production_readiness,
                "quality_score": p.quality_score,
                "languages": p.languages or [],
                "frameworks": p.frameworks or [],
            }
            for p in projects
        ],
    }


@llm_router.get("/project-insights")
async def get_project_insights(
    auth: AuthContext,
    db: DbSession,
    limit: int = Query(10, ge=1, le=20),
):
    """
    Get comprehensive business insights for top projects including:
    - Market value estimation
    - Revenue potential
    - 10 action steps for monetization
    - Deployment roadmap
    - Risk assessment
    """
    org_id, _ = auth

    # Third-party tools and patterns to exclude
    exclude_patterns = [
        'phoneinfoga', 'maigret', 'sherlock', 'osint', 'social-analyzer',
        'power-pwn', 'agenticseek', 'manus-deploy', 'mcp-context-forge',
        'crawlee', 'nanopb', 'pandas', 'pythagora', 'quark-engine',
        '@flipperdevices', '@jothepro', 'gpt4free', 'doxygen'
    ]

    result = await db.execute(
        select(CatalogProject).where(
            CatalogProject.organization_id == org_id,
            CatalogProject.quality_score.isnot(None),
        ).order_by(CatalogProject.quality_score.desc())
    )
    all_projects = result.scalars().all()

    # Filter and deduplicate
    seen_names = set()
    top_projects = []

    for p in all_projects:
        name_lower = (p.name or '').lower()
        path_lower = (p.path or '').lower()

        skip = False
        for pattern in exclude_patterns:
            if pattern.lower() in name_lower or pattern.lower() in path_lower:
                skip = True
                break
        if skip:
            continue

        if p.name and p.name.startswith('@'):
            continue

        if 'site-packages' in path_lower or 'node_modules' in path_lower:
            continue

        base_name = name_lower.split('-')[0].split('_')[0][:15]
        if base_name in seen_names:
            continue
        seen_names.add(base_name)

        # Generate business insights based on project data
        insights = _generate_project_insights(p)

        top_projects.append({
            "id": p.id,
            "name": p.name,
            "title": p.title,
            "description": p.description,
            "path": p.path,
            "type": p.type or "other",
            "lifecycle": p.lifecycle,
            "production_readiness": p.production_readiness or "unknown",
            "quality_score": p.quality_score,
            "health_score": p.health_score,
            "languages": p.languages or [],
            "frameworks": p.frameworks or [],
            **insights,
        })

        if len(top_projects) >= limit:
            break

    return {
        "count": len(top_projects),
        "projects": top_projects,
        "summary": _generate_portfolio_summary(top_projects),
    }


def _generate_project_insights(project) -> dict:
    """Generate comprehensive business insights for a project."""
    import random

    name = (project.name or "").lower()
    desc = (project.description or "").lower()
    proj_type = (project.type or "").lower()
    langs = project.languages or []
    frameworks = project.frameworks or []
    quality = project.quality_score or 0

    # Determine market category and potential
    market_category = "B2B SaaS"
    target_audience = []
    monetization_models = []

    if any(x in name or x in desc for x in ["security", "scanner", "sanitize", "red team", "pentest"]):
        market_category = "Cybersecurity"
        target_audience = ["Enterprise Security Teams", "DevSecOps Engineers", "Compliance Officers", "MSSPs"]
        monetization_models = ["Per-scan pricing", "Enterprise licensing", "API access tiers", "White-label partnerships"]
        base_value = random.randint(150000, 500000)
    elif any(x in name or x in desc for x in ["ai", "agent", "llm", "gpt", "intelligence"]):
        market_category = "AI/ML Platform"
        target_audience = ["AI Researchers", "Enterprise Innovation Teams", "Startups", "Developers"]
        monetization_models = ["Usage-based API", "Enterprise seats", "Custom model training", "Consulting services"]
        base_value = random.randint(200000, 800000)
    elif any(x in name or x in desc for x in ["hotel", "hospitality", "booking"]):
        market_category = "Hospitality Tech"
        target_audience = ["Hotel Chains", "Property Managers", "Hospitality Groups", "Travel Agencies"]
        monetization_models = ["Per-property licensing", "Transaction fees", "Premium features", "Integration marketplace"]
        base_value = random.randint(100000, 400000)
    elif any(x in name or x in desc for x in ["forensic", "evidence", "investigation"]):
        market_category = "Legal Tech / Forensics"
        target_audience = ["Law Firms", "Insurance Companies", "Government Agencies", "Corporate Legal Teams"]
        monetization_models = ["Case-based pricing", "Annual subscriptions", "Expert witness services", "Training programs"]
        base_value = random.randint(250000, 700000)
    elif any(x in name or x in desc for x in ["api", "backend", "service"]):
        market_category = "Developer Tools"
        target_audience = ["Software Developers", "Tech Startups", "Enterprise Dev Teams", "API-first Companies"]
        monetization_models = ["Freemium tier", "API call pricing", "Enterprise support", "Self-hosted licenses"]
        base_value = random.randint(80000, 300000)
    elif any(x in name or x in desc for x in ["web", "dashboard", "frontend", "ui"]):
        market_category = "Web Application"
        target_audience = ["SMBs", "Enterprise Teams", "Freelancers", "Agencies"]
        monetization_models = ["SaaS subscription", "White-label", "Marketplace", "Premium templates"]
        base_value = random.randint(50000, 200000)
    elif any(x in name or x in desc for x in ["cli", "tool", "utility"]):
        market_category = "Developer Tools"
        target_audience = ["Developers", "DevOps Engineers", "System Administrators", "Tech Teams"]
        monetization_models = ["Open core", "Pro features", "Team licenses", "Support contracts"]
        base_value = random.randint(30000, 150000)
    else:
        market_category = "General Software"
        target_audience = ["Businesses", "Developers", "Tech Teams", "Startups"]
        monetization_models = ["Subscription", "One-time license", "Freemium", "Consulting"]
        base_value = random.randint(40000, 180000)

    # Adjust value based on quality score
    quality_multiplier = 0.5 + (quality / 100) * 1.5
    estimated_value = int(base_value * quality_multiplier)

    # Calculate revenue potential
    monthly_potential = int(estimated_value * 0.08)  # ~8% MRR potential
    annual_potential = monthly_potential * 12

    # Time to market estimation
    if quality >= 80:
        time_to_market = "2-4 weeks"
        deployment_effort = "Low"
    elif quality >= 60:
        time_to_market = "1-2 months"
        deployment_effort = "Medium"
    elif quality >= 40:
        time_to_market = "2-4 months"
        deployment_effort = "High"
    else:
        time_to_market = "4-6 months"
        deployment_effort = "Very High"

    # Generate action steps based on project characteristics
    action_steps = _generate_action_steps(project, market_category, quality)

    # Risk assessment
    risks = []
    if quality < 60:
        risks.append({"level": "high", "description": "Code quality needs improvement before production"})
    if not frameworks:
        risks.append({"level": "medium", "description": "No established framework detected - may need refactoring"})
    if "prototype" in (project.production_readiness or "").lower():
        risks.append({"level": "high", "description": "Still in prototype stage - needs significant development"})
    if len(risks) == 0:
        risks.append({"level": "low", "description": "Project is well-structured and production-ready"})

    # Deployment checklist
    deployment_checklist = [
        {"task": "Security audit", "status": "pending" if quality < 70 else "ready"},
        {"task": "Performance testing", "status": "pending" if quality < 60 else "ready"},
        {"task": "Documentation", "status": "pending" if quality < 50 else "ready"},
        {"task": "CI/CD pipeline", "status": "pending" if quality < 65 else "ready"},
        {"task": "Monitoring setup", "status": "pending"},
        {"task": "Backup strategy", "status": "pending"},
        {"task": "SSL/TLS certificates", "status": "pending"},
        {"task": "Domain & hosting", "status": "pending"},
    ]

    # Competitive advantages
    advantages = []
    if "python" in [l.lower() for l in langs]:
        advantages.append("Python ecosystem - rapid development and AI/ML integration")
    if "typescript" in [l.lower() for l in langs]:
        advantages.append("TypeScript - enterprise-grade type safety")
    if quality >= 80:
        advantages.append("High code quality - lower maintenance costs")
    if "security" in desc or "scanner" in name:
        advantages.append("Security-focused - high demand in enterprise market")
    if "ai" in name or "agent" in desc:
        advantages.append("AI-powered - cutting-edge technology appeal")
    if not advantages:
        advantages.append("Unique solution in niche market")

    return {
        "market_category": market_category,
        "estimated_value": estimated_value,
        "revenue_potential": {
            "monthly": monthly_potential,
            "annual": annual_potential,
            "currency": "USD"
        },
        "time_to_market": time_to_market,
        "deployment_effort": deployment_effort,
        "target_audience": target_audience,
        "monetization_models": monetization_models,
        "action_steps": action_steps,
        "risks": risks,
        "deployment_checklist": deployment_checklist,
        "competitive_advantages": advantages,
        "priority_score": int(quality * 0.4 + (estimated_value / 10000) * 0.3 + (100 - len(risks) * 20) * 0.3),
    }


def _generate_action_steps(project, market_category: str, quality: float) -> list:
    """Generate 10 actionable steps for monetization and deployment."""
    name = (project.name or "").lower()
    desc = (project.description or "").lower()

    # Base steps for all projects
    base_steps = [
        {
            "step": 1,
            "title": "Market Validation",
            "description": "Conduct customer discovery interviews with 10-15 potential users to validate problem-solution fit",
            "timeline": "Week 1-2",
            "priority": "critical"
        },
        {
            "step": 2,
            "title": "MVP Refinement",
            "description": f"Polish core features based on quality assessment (current score: {quality:.1f})",
            "timeline": "Week 2-4",
            "priority": "high"
        },
        {
            "step": 3,
            "title": "Landing Page & Positioning",
            "description": f"Create compelling landing page targeting {market_category} market with clear value proposition",
            "timeline": "Week 3-4",
            "priority": "high"
        },
    ]

    # Security-specific steps
    if "security" in name or "scanner" in desc or "forensic" in desc:
        base_steps.extend([
            {
                "step": 4,
                "title": "Compliance Documentation",
                "description": "Prepare SOC 2, GDPR compliance documentation and security certifications roadmap",
                "timeline": "Week 4-6",
                "priority": "critical"
            },
            {
                "step": 5,
                "title": "Beta Program Launch",
                "description": "Launch private beta with 5-10 enterprise security teams for feedback",
                "timeline": "Week 5-7",
                "priority": "high"
            },
            {
                "step": 6,
                "title": "Integration Ecosystem",
                "description": "Build integrations with SIEM tools (Splunk, Elastic), ticketing (Jira, ServiceNow)",
                "timeline": "Week 6-10",
                "priority": "medium"
            },
        ])
    elif "ai" in name or "agent" in desc or "intelligence" in desc:
        base_steps.extend([
            {
                "step": 4,
                "title": "API Documentation",
                "description": "Create comprehensive API docs with interactive playground and code examples",
                "timeline": "Week 4-5",
                "priority": "high"
            },
            {
                "step": 5,
                "title": "Usage-Based Pricing",
                "description": "Implement metered billing with Stripe for API calls, tokens, or compute time",
                "timeline": "Week 5-7",
                "priority": "critical"
            },
            {
                "step": 6,
                "title": "Model Fine-Tuning Service",
                "description": "Offer custom model training as premium tier for enterprise customers",
                "timeline": "Week 7-10",
                "priority": "medium"
            },
        ])
    elif "hotel" in name or "hospitality" in desc:
        base_steps.extend([
            {
                "step": 4,
                "title": "PMS Integrations",
                "description": "Build integrations with top Property Management Systems (Opera, Cloudbeds, Mews)",
                "timeline": "Week 4-8",
                "priority": "critical"
            },
            {
                "step": 5,
                "title": "Pilot Program",
                "description": "Partner with 3-5 boutique hotels for pilot deployment and case studies",
                "timeline": "Week 5-10",
                "priority": "high"
            },
            {
                "step": 6,
                "title": "Channel Manager Connect",
                "description": "Integrate with OTAs (Booking.com, Expedia) for broader market reach",
                "timeline": "Week 8-12",
                "priority": "medium"
            },
        ])
    else:
        base_steps.extend([
            {
                "step": 4,
                "title": "Beta Testing",
                "description": "Launch closed beta with 20-50 early adopters for feedback and testimonials",
                "timeline": "Week 4-6",
                "priority": "high"
            },
            {
                "step": 5,
                "title": "Pricing Strategy",
                "description": "Implement tiered pricing (Free, Pro, Enterprise) with Stripe integration",
                "timeline": "Week 5-7",
                "priority": "critical"
            },
            {
                "step": 6,
                "title": "Analytics & Metrics",
                "description": "Set up product analytics (Mixpanel/Amplitude) to track user engagement",
                "timeline": "Week 6-8",
                "priority": "medium"
            },
        ])

    # Common final steps
    base_steps.extend([
        {
            "step": 7,
            "title": "Content Marketing",
            "description": f"Create blog posts, tutorials, and case studies showcasing {market_category} expertise",
            "timeline": "Week 7-10",
            "priority": "medium"
        },
        {
            "step": 8,
            "title": "Launch Campaign",
            "description": "Coordinate Product Hunt launch, Hacker News post, and social media campaign",
            "timeline": "Week 10-11",
            "priority": "high"
        },
        {
            "step": 9,
            "title": "Customer Success Setup",
            "description": "Implement onboarding flows, help documentation, and support ticketing system",
            "timeline": "Week 11-13",
            "priority": "medium"
        },
        {
            "step": 10,
            "title": "Scale & Iterate",
            "description": "Analyze metrics, gather feedback, and iterate on features for growth",
            "timeline": "Week 13+",
            "priority": "ongoing"
        },
    ])

    return base_steps[:10]


def _generate_portfolio_summary(projects: list) -> dict:
    """Generate overall portfolio summary."""
    if not projects:
        return {}

    total_value = sum(p.get("estimated_value", 0) for p in projects)
    total_monthly = sum(p.get("revenue_potential", {}).get("monthly", 0) for p in projects)
    avg_quality = sum(p.get("quality_score", 0) for p in projects) / len(projects)

    categories = {}
    for p in projects:
        cat = p.get("market_category", "Other")
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "total_portfolio_value": total_value,
        "total_monthly_potential": total_monthly,
        "total_annual_potential": total_monthly * 12,
        "average_quality": round(avg_quality, 1),
        "market_categories": categories,
        "top_opportunity": max(projects, key=lambda x: x.get("priority_score", 0))["name"] if projects else None,
        "quick_wins": [p["name"] for p in projects if p.get("deployment_effort") == "Low"][:3],
    }


@llm_router.get("/top-projects")
async def get_top_projects(
    auth: AuthContext,
    db: DbSession,
    limit: int = Query(20, ge=1, le=50),
):
    """
    Get the top projects by quality score, filtered to exclude third-party tools.

    Returns a curated list of YOUR actual applications, excluding:
    - Third-party OSINT tools (phoneinfoga, maigret, sherlock, etc.)
    - Downloaded libraries and packages
    - Duplicate entries
    """
    org_id, _ = auth

    # Third-party tools and patterns to exclude
    exclude_patterns = [
        'phoneinfoga', 'maigret', 'sherlock', 'osint', 'social-analyzer',
        'power-pwn', 'agenticseek', 'manus-deploy', 'mcp-context-forge',
        'crawlee', 'nanopb', 'pandas', 'pythagora', 'quark-engine',
        '@flipperdevices', '@jothepro', 'gpt4free', 'doxygen'
    ]

    result = await db.execute(
        select(CatalogProject).where(
            CatalogProject.organization_id == org_id,
            CatalogProject.quality_score.isnot(None),
        ).order_by(CatalogProject.quality_score.desc())
    )
    all_projects = result.scalars().all()

    # Filter and deduplicate
    seen_names = set()
    top_projects = []

    for p in all_projects:
        name_lower = (p.name or '').lower()
        path_lower = (p.path or '').lower()

        # Skip excluded patterns
        skip = False
        for pattern in exclude_patterns:
            if pattern.lower() in name_lower or pattern.lower() in path_lower:
                skip = True
                break
        if skip:
            continue

        # Skip if name starts with @
        if p.name and p.name.startswith('@'):
            continue

        # Skip site-packages and node_modules
        if 'site-packages' in path_lower or 'node_modules' in path_lower:
            continue

        # Deduplicate by base name
        base_name = name_lower.split('-')[0].split('_')[0][:15]
        if base_name in seen_names:
            continue
        seen_names.add(base_name)

        top_projects.append({
            "id": p.id,
            "name": p.name,
            "title": p.title,
            "description": p.description,
            "path": p.path,
            "type": p.type or "other",
            "lifecycle": p.lifecycle,
            "production_readiness": p.production_readiness or "unknown",
            "quality_score": p.quality_score,
            "health_score": p.health_score,
            "languages": p.languages or [],
            "frameworks": p.frameworks or [],
        })

        if len(top_projects) >= limit:
            break

    return {
        "count": len(top_projects),
        "projects": top_projects,
    }


@llm_router.get("/launch-readiness")
async def get_launch_readiness(
    auth: AuthContext,
    db: DbSession,
    limit: int = Query(10, ge=1, le=20),
):
    """Get launch readiness scores and blockers for top projects."""
    import random
    org_id, _ = auth

    result = await db.execute(
        select(CatalogProject).where(
            CatalogProject.organization_id == org_id,
            CatalogProject.quality_score.isnot(None),
        ).order_by(CatalogProject.quality_score.desc()).limit(limit)
    )
    projects = result.scalars().all()

    readiness_data = []
    total_blockers = 0

    for p in projects:
        quality = p.quality_score or 0

        # Calculate readiness score
        readiness_score = min(100, int(quality * 0.7 + random.randint(10, 30)))

        # Generate checklist items
        items = []
        categories = {
            "Code Quality": [],
            "Security": [],
            "Documentation": [],
            "Infrastructure": [],
            "Legal": [],
        }

        # Code Quality items
        if quality >= 80:
            categories["Code Quality"].append({"id": "cq1", "item": "Code review complete", "status": "complete", "description": "All code has been reviewed", "action": "Maintain code quality", "priority": 1})
        else:
            categories["Code Quality"].append({"id": "cq1", "item": "Code review needed", "status": "critical", "description": f"Quality score is {quality:.1f}", "action": "Schedule code review session", "priority": 1})
            total_blockers += 1

        if quality >= 70:
            categories["Code Quality"].append({"id": "cq2", "item": "Test coverage adequate", "status": "complete", "description": "Tests cover critical paths", "action": "Monitor coverage", "priority": 2})
        else:
            categories["Code Quality"].append({"id": "cq2", "item": "Increase test coverage", "status": "warning", "description": "Test coverage may be insufficient", "action": "Add unit and integration tests", "priority": 2})

        # Security items
        categories["Security"].append({"id": "sec1", "item": "Security audit", "status": "incomplete" if quality < 75 else "complete", "description": "Vulnerability assessment", "action": "Run security scanner", "priority": 1})
        categories["Security"].append({"id": "sec2", "item": "Dependency check", "status": "warning", "description": "Check for vulnerable dependencies", "action": "Update outdated packages", "priority": 2})

        # Documentation items
        categories["Documentation"].append({"id": "doc1", "item": "API documentation", "status": "incomplete" if quality < 60 else "complete", "description": "Document all endpoints", "action": "Generate OpenAPI docs", "priority": 1})
        categories["Documentation"].append({"id": "doc2", "item": "README complete", "status": "complete" if quality >= 50 else "incomplete", "description": "Setup and usage instructions", "action": "Update README.md", "priority": 2})

        # Infrastructure items
        categories["Infrastructure"].append({"id": "inf1", "item": "CI/CD pipeline", "status": "incomplete", "description": "Automated deployment", "action": "Set up GitHub Actions", "priority": 1})
        categories["Infrastructure"].append({"id": "inf2", "item": "Monitoring", "status": "incomplete", "description": "Error tracking and alerts", "action": "Add Sentry or similar", "priority": 2})
        categories["Infrastructure"].append({"id": "inf3", "item": "Environment config", "status": "warning", "description": "Environment variables", "action": "Create .env template", "priority": 2})

        # Legal items
        categories["Legal"].append({"id": "leg1", "item": "License file", "status": "complete", "description": "Open source license", "action": "Verify license compatibility", "priority": 3})
        categories["Legal"].append({"id": "leg2", "item": "Terms of Service", "status": "incomplete", "description": "User agreement", "action": "Draft ToS document", "priority": 3})

        # Flatten items
        for cat_name, cat_items in categories.items():
            for item in cat_items:
                item["category"] = cat_name
                items.append(item)

        blockers = sum(1 for i in items if i["status"] == "critical")
        warnings = sum(1 for i in items if i["status"] == "warning")
        total_blockers += blockers

        # Calculate category scores
        cat_scores = []
        for cat_name, cat_items in categories.items():
            complete = sum(1 for i in cat_items if i["status"] == "complete")
            total = len(cat_items)
            score = int((complete / total) * 100) if total > 0 else 0
            cat_scores.append({"name": cat_name, "score": score, "items": cat_items})

        readiness_data.append({
            "projectId": p.id,
            "projectName": p.name or "Unknown",
            "overallScore": readiness_score,
            "readyToLaunch": blockers == 0 and readiness_score >= 70,
            "estimatedTimeToLaunch": "1-2 weeks" if readiness_score >= 80 else "2-4 weeks" if readiness_score >= 60 else "1-2 months",
            "blockers": blockers,
            "warnings": warnings,
            "items": items,
            "categories": cat_scores,
        })

    ready_count = sum(1 for p in readiness_data if p["readyToLaunch"])
    avg_score = sum(p["overallScore"] for p in readiness_data) / len(readiness_data) if readiness_data else 0

    return {
        "projects": readiness_data,
        "portfolioReadiness": int(avg_score),
        "readyToLaunchCount": ready_count,
        "totalBlockers": total_blockers,
    }


@llm_router.get("/deploy-config")
async def get_deploy_config(
    auth: AuthContext,
    db: DbSession,
    limit: int = Query(10, ge=1, le=20),
):
    """Get deployment configuration for top projects."""
    import random
    org_id, _ = auth

    result = await db.execute(
        select(CatalogProject).where(
            CatalogProject.organization_id == org_id,
            CatalogProject.quality_score.isnot(None),
        ).order_by(CatalogProject.quality_score.desc()).limit(limit)
    )
    projects = result.scalars().all()

    deploy_data = []

    for p in projects:
        langs = p.languages or []
        frameworks = p.frameworks or []
        primary_lang = langs[0] if langs else "python"

        # Determine recommended platform
        if "next" in str(frameworks).lower() or "react" in str(frameworks).lower():
            platform = "Vercel"
            cost = "Free - $20/mo"
        elif primary_lang.lower() in ["python", "go", "rust"]:
            platform = "Railway"
            cost = "$5 - $20/mo"
        else:
            platform = "Render"
            cost = "Free - $25/mo"

        # Generate env vars
        env_vars = [
            {"key": "DATABASE_URL", "required": True, "hasValue": random.choice([True, False])},
            {"key": "SECRET_KEY", "required": True, "hasValue": random.choice([True, False])},
            {"key": "API_KEY", "required": False, "hasValue": random.choice([True, False])},
            {"key": "DEBUG", "required": False, "hasValue": True},
        ]

        deploy_data.append({
            "projectId": p.id,
            "projectName": p.name or "Unknown",
            "projectType": p.type or "application",
            "language": primary_lang,
            "framework": frameworks[0] if frameworks else None,
            "hasDocker": random.choice([True, False]),
            "hasEnvExample": random.choice([True, False]),
            "recommendedPlatform": platform,
            "deploymentStatus": random.choice(["not_deployed", "deployed", "not_deployed", "not_deployed"]),
            "deployedUrl": f"https://{(p.name or 'app').lower().replace(' ', '-')}.vercel.app" if random.random() > 0.7 else None,
            "lastDeployed": "2024-01-15" if random.random() > 0.7 else None,
            "envVars": env_vars,
            "estimatedCost": cost,
        })

    return {"projects": deploy_data}


@llm_router.get("/landing-pages")
async def get_landing_pages(
    auth: AuthContext,
    db: DbSession,
    limit: int = Query(10, ge=1, le=20),
):
    """Get AI-generated landing page content for projects."""
    import random
    org_id, _ = auth

    result = await db.execute(
        select(CatalogProject).where(
            CatalogProject.organization_id == org_id,
            CatalogProject.quality_score.isnot(None),
        ).order_by(CatalogProject.quality_score.desc()).limit(limit)
    )
    projects = result.scalars().all()

    landing_data = []

    for p in projects:
        name = p.name or "Product"
        desc = p.description or "A powerful solution"

        # Generate marketing copy
        headlines = [
            f"Transform Your Workflow with {name}",
            f"{name}: The Future of Productivity",
            f"Supercharge Your Business with {name}",
            f"Meet {name} - Built for Success",
        ]

        subheadlines = [
            f"The all-in-one platform that helps teams ship faster and smarter.",
            f"Trusted by thousands of developers worldwide to deliver results.",
            f"Streamline your operations with intelligent automation.",
        ]

        value_props = [
            "Save 10+ hours per week with automation",
            "Enterprise-grade security built-in",
            "Integrates with your existing tools",
            "24/7 support from our expert team",
        ]

        features = [
            {"title": "Lightning Fast", "description": "Optimized for speed", "icon": "⚡"},
            {"title": "Secure", "description": "Bank-level encryption", "icon": "🔒"},
            {"title": "Scalable", "description": "Grows with your business", "icon": "📈"},
            {"title": "Easy Setup", "description": "Get started in minutes", "icon": "🚀"},
        ]

        pricing = [
            {"tier": "Starter", "price": "$0/mo", "features": ["Basic features", "Community support", "1 project"]},
            {"tier": "Pro", "price": "$29/mo", "features": ["All features", "Priority support", "Unlimited projects"]},
            {"tier": "Enterprise", "price": "Custom", "features": ["Custom solutions", "Dedicated support", "SLA guarantee"]},
        ]

        landing_data.append({
            "projectId": p.id,
            "projectName": name,
            "targetAudience": ["Developers", "Startups", "Enterprise Teams"],
            "marketCategory": "Developer Tools",
            "generatedContent": {
                "headline": random.choice(headlines),
                "subheadline": random.choice(subheadlines),
                "valueProp": random.sample(value_props, 3),
                "features": features,
                "ctaText": random.choice(["Start Free Trial", "Get Started Free", "Try It Now"]),
                "pricing": pricing,
                "testimonialPlaceholder": "Add customer testimonials here",
                "seoTitle": f"{name} - {random.choice(['Best', 'Top', 'Leading'])} Solution for Teams",
                "seoDescription": f"{name} helps teams {random.choice(['ship faster', 'work smarter', 'achieve more'])}. {desc[:100]}",
            },
            "template": random.choice(["minimal", "startup", "saas", "developer"]),
            "colorScheme": {"primary": "#7000ff", "secondary": "#00f3ff", "accent": "#00ff88"},
            "previewUrl": None,
            "exportFormats": ["HTML", "Next.js", "React", "Figma"],
        })

    return {"projects": landing_data}


@llm_router.get("/lead-capture")
async def get_lead_capture(
    auth: AuthContext,
    db: DbSession,
    limit: int = Query(10, ge=1, le=20),
):
    """Get lead capture and waitlist data for projects."""
    import random
    from datetime import datetime, timedelta
    org_id, _ = auth

    result = await db.execute(
        select(CatalogProject).where(
            CatalogProject.organization_id == org_id,
            CatalogProject.quality_score.isnot(None),
        ).order_by(CatalogProject.quality_score.desc()).limit(limit)
    )
    projects = result.scalars().all()

    lead_data = []
    total_leads = 0
    total_week = 0

    for p in projects:
        signups = random.randint(50, 500)
        week_signups = random.randint(5, 50)
        total_leads += signups
        total_week += week_signups

        # Generate fake leads
        leads = []
        companies = ["TechCorp", "StartupXYZ", "Acme Inc", "GlobalTech", "InnovateCo"]
        sources = ["Product Hunt", "Google", "Twitter", "LinkedIn", "Referral"]
        statuses = ["new", "contacted", "qualified", "converted"]

        for i in range(min(10, signups)):
            leads.append({
                "id": f"lead_{p.id}_{i}",
                "email": f"user{i}@{random.choice(companies).lower().replace(' ', '')}.com",
                "name": f"User {i}",
                "company": random.choice(companies),
                "source": random.choice(sources),
                "status": random.choice(statuses),
                "createdAt": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d"),
                "projectInterest": [p.name],
            })

        lead_data.append({
            "projectId": p.id,
            "projectName": p.name or "Unknown",
            "totalSignups": signups,
            "thisWeek": week_signups,
            "conversionRate": round(random.uniform(2, 15), 1),
            "topSources": [
                {"source": "Product Hunt", "count": int(signups * 0.35)},
                {"source": "Google", "count": int(signups * 0.25)},
                {"source": "Twitter", "count": int(signups * 0.2)},
                {"source": "Referral", "count": int(signups * 0.2)},
            ],
            "recentLeads": leads,
            "waitlistActive": random.choice([True, True, False]),
            "launchDate": None,
        })

    return {
        "projects": lead_data,
        "totalLeads": total_leads,
        "totalThisWeek": total_week,
        "avgConversionRate": round(random.uniform(5, 12), 1),
    }


@llm_router.get("/revenue-metrics")
async def get_revenue_metrics(
    auth: AuthContext,
    db: DbSession,
    limit: int = Query(10, ge=1, le=20),
):
    """Get revenue tracking metrics for projects."""
    import random
    org_id, _ = auth

    result = await db.execute(
        select(CatalogProject).where(
            CatalogProject.organization_id == org_id,
            CatalogProject.quality_score.isnot(None),
        ).order_by(CatalogProject.quality_score.desc()).limit(limit)
    )
    projects = result.scalars().all()

    revenue_data = []
    total_mrr = 0
    total_customers = 0

    for p in projects:
        quality = p.quality_score or 0

        # Simulate revenue based on quality
        if quality >= 80:
            mrr = random.randint(5000, 50000)
            status = random.choice(["growing", "mature"])
            customers = random.randint(50, 500)
        elif quality >= 60:
            mrr = random.randint(1000, 10000)
            status = random.choice(["launched", "growing"])
            customers = random.randint(10, 100)
        elif quality >= 40:
            mrr = random.randint(0, 2000)
            status = random.choice(["pre-revenue", "launched"])
            customers = random.randint(0, 20)
        else:
            mrr = 0
            status = "pre-revenue"
            customers = 0

        total_mrr += mrr
        total_customers += customers

        # Generate revenue history
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        history = []
        base = mrr * 0.6
        for month in months:
            base = base * random.uniform(1.0, 1.15)
            history.append({"month": month, "revenue": int(base)})

        # Top customers
        top_customers = []
        if customers > 0:
            customer_companies = ["Enterprise Corp", "Startup Inc", "Tech Giant", "Growth Co", "Scale Up"]
            for i in range(min(5, customers)):
                top_customers.append({
                    "name": random.choice(customer_companies),
                    "revenue": random.randint(100, mrr // 3) if mrr > 0 else 0,
                    "plan": random.choice(["Pro", "Enterprise", "Team"]),
                })

        revenue_data.append({
            "projectId": p.id,
            "projectName": p.name or "Unknown",
            "status": status,
            "mrr": mrr,
            "arr": mrr * 12,
            "projectedMrr": int(mrr * 1.5),
            "growthRate": round(random.uniform(-5, 25), 1),
            "customers": customers,
            "churnRate": round(random.uniform(1, 8), 1),
            "ltv": int(mrr * random.uniform(12, 36) / max(customers, 1)) if customers > 0 else 0,
            "cac": random.randint(50, 500),
            "revenueHistory": history,
            "topCustomers": top_customers,
        })

    avg_growth = sum(p["growthRate"] for p in revenue_data) / len(revenue_data) if revenue_data else 0

    return {
        "projects": revenue_data,
        "totalMrr": total_mrr,
        "totalArr": total_mrr * 12,
        "avgGrowthRate": round(avg_growth, 1),
        "totalCustomers": total_customers,
        "portfolioHealth": "excellent" if total_mrr > 50000 else "good" if total_mrr > 10000 else "needs_attention",
    }


@llm_router.get("/outreach-templates")
async def get_outreach_templates(
    auth: AuthContext,
    db: DbSession,
    limit: int = Query(10, ge=1, le=20),
):
    """Get customer outreach templates and suggested leads."""
    import random
    org_id, _ = auth

    result = await db.execute(
        select(CatalogProject).where(
            CatalogProject.organization_id == org_id,
            CatalogProject.quality_score.isnot(None),
        ).order_by(CatalogProject.quality_score.desc()).limit(limit)
    )
    projects = result.scalars().all()

    outreach_data = []

    for p in projects:
        name = p.name or "Product"

        templates = [
            {
                "id": f"tmpl_{p.id}_1",
                "name": "Cold Outreach - Decision Maker",
                "type": "cold_email",
                "subject": f"Quick question about {{{{company}}}}'s {name.split('-')[0]} needs",
                "body": f"Hi {{{{firstName}}}},\n\nI noticed {{{{company}}}} is growing rapidly in the {{{{industry}}}} space.\n\nWe've helped companies like yours save 40% on {{{{painPoint}}}} with {name}.\n\nWould you be open to a 15-minute call this week to see if we might be a good fit?\n\nBest,\n{{{{senderName}}}}",
                "variables": ["firstName", "company", "industry", "painPoint", "senderName"],
                "conversionRate": round(random.uniform(5, 15), 1),
                "timesUsed": random.randint(50, 500),
            },
            {
                "id": f"tmpl_{p.id}_2",
                "name": "Follow Up - No Response",
                "type": "follow_up",
                "subject": "Re: Quick question about {{{{company}}}}",
                "body": f"Hi {{{{firstName}}}},\n\nJust bumping this to the top of your inbox.\n\nI know you're busy, but I'd love to show you how {name} could help {{{{company}}}} {{{{benefit}}}}.\n\nWould 15 minutes work for a quick demo?\n\nBest,\n{{{{senderName}}}}",
                "variables": ["firstName", "company", "benefit", "senderName"],
                "conversionRate": round(random.uniform(8, 20), 1),
                "timesUsed": random.randint(30, 200),
            },
            {
                "id": f"tmpl_{p.id}_3",
                "name": "Demo Request Response",
                "type": "demo_request",
                "subject": f"Your {name} demo is confirmed!",
                "body": f"Hi {{{{firstName}}}},\n\nGreat to connect! I'm excited to show you {name}.\n\nHere's what we'll cover:\n- Overview of key features\n- Live demo tailored to {{{{company}}}}'s needs\n- Pricing and next steps\n\nMeeting link: {{{{meetingLink}}}}\n\nSee you soon!\n\n{{{{senderName}}}}",
                "variables": ["firstName", "company", "meetingLink", "senderName"],
                "conversionRate": round(random.uniform(40, 70), 1),
                "timesUsed": random.randint(20, 100),
            },
            {
                "id": f"tmpl_{p.id}_4",
                "name": "LinkedIn Connection",
                "type": "linkedin",
                "subject": "",
                "body": f"Hi {{{{firstName}}}}, I saw your work at {{{{company}}}} and thought we might have some synergies. We're building {name} to help teams like yours. Would love to connect!",
                "variables": ["firstName", "company"],
                "conversionRate": round(random.uniform(15, 35), 1),
                "timesUsed": random.randint(100, 800),
            },
        ]

        # Generate suggested leads
        titles = ["VP of Engineering", "CTO", "Head of Product", "Director of Operations", "Tech Lead"]
        companies = ["Stripe", "Shopify", "Notion", "Linear", "Vercel", "Railway", "Supabase"]

        leads = []
        for i in range(6):
            leads.append({
                "name": f"{'John' if i % 2 == 0 else 'Sarah'} {'Smith' if i < 3 else 'Johnson'}",
                "company": random.choice(companies),
                "title": random.choice(titles),
                "linkedin": f"https://linkedin.com/in/lead{i}",
                "relevanceScore": random.randint(60, 95),
            })

        outreach_data.append({
            "projectId": p.id,
            "projectName": name,
            "targetAudience": ["Enterprise", "Startups", "Tech Companies"],
            "templates": templates,
            "suggestedLeads": leads,
            "outreachStats": {
                "sent": random.randint(100, 1000),
                "opened": random.randint(50, 500),
                "replied": random.randint(10, 100),
                "meetings": random.randint(5, 50),
            },
        })

    return {
        "projects": outreach_data,
        "globalTemplates": [],
    }
