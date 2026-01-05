"""Test NLU query understanding."""
import asyncio
import json
from indexer_api.catalog.llm import get_llm_service

async def test():
    llm = get_llm_service()

    queries = [
        "python web",
        "machine learning projects",
        "typescript api",
        "discord bot",
        "active python libraries",
    ]

    for query in queries:
        result = await llm.understand_query(query)
        print(f"\nQuery: '{query}'")
        print(f"Keywords: {result.get('keywords', [])}")
        print(f"Filters: {result.get('filters', {})}")
        print(f"Intent: {result.get('intent', 'unknown')}")

if __name__ == "__main__":
    asyncio.run(test())
