"""Check project types in database."""
import asyncio
from collections import Counter
from indexer_api.db.base import get_db_context
from indexer_api.catalog.models import CatalogProject
from sqlalchemy import select

async def check_types():
    async with get_db_context() as db:
        result = await db.execute(select(CatalogProject.type))
        types = [r[0] for r in result.fetchall()]

        type_counts = Counter(types)
        print("Project types in database:")
        for t, count in type_counts.most_common(20):
            print(f"  {t}: {count}")

        # Check how many have "web" related types
        web_count = sum(1 for t in types if t and "web" in t.lower())
        print(f"\nProjects with 'web' in type: {web_count}")

        # Check python + web combination
        result2 = await db.execute(
            select(CatalogProject.name, CatalogProject.type, CatalogProject.languages)
            .where(CatalogProject.languages.contains("python"))
            .limit(20)
        )
        print("\nSample Python projects:")
        for name, ptype, langs in result2.fetchall():
            print(f"  {name}: type={ptype}, langs={langs}")

if __name__ == "__main__":
    asyncio.run(check_types())
