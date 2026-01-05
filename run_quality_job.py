"""Run quality assessment job directly."""
import asyncio
import sys
sys.path.insert(0, r"C:\Users\ayrto\indexer-api\src")

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///C:/Users/ayrto/indexer-api/indexer.db"


async def run_quality_assessment():
    from indexer_api.catalog.models import CatalogProject, CatalogJob
    from indexer_api.catalog.job_handlers import QualityAssessmentJobHandler

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Count unassessed projects
        result = await db.execute(
            select(func.count()).select_from(CatalogProject).where(
                CatalogProject.quality_score == None
            )
        )
        unassessed = result.scalar_one()
        print(f"Projects to assess: {unassessed}")

        if unassessed == 0:
            print("All projects already assessed!")
            return

        # Get org_id from first project
        result = await db.execute(select(CatalogProject.organization_id).limit(1))
        org_id = result.scalar_one()

        # Create a fake job for the handler
        job = CatalogJob(
            id="manual-quality-run",
            organization_id=org_id,
            job_type="quality_assessment",
            status="running",
            result={"force_refresh": False},
        )

        handler = QualityAssessmentJobHandler()
        print(f"\nStarting quality assessment...")
        print("This will take a while. Progress updates every 10 projects.\n")

        result = await handler.execute(job, db)

        print(f"\n{'='*50}")
        print(f"COMPLETED")
        print(f"{'='*50}")
        print(f"Assessed: {result.get('assessed', 0)}")
        print(f"Total: {result.get('total', 0)}")
        if result.get('errors'):
            print(f"Errors: {len(result['errors'])}")


if __name__ == "__main__":
    asyncio.run(run_quality_assessment())
