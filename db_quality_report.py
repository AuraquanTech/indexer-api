"""Direct DB quality report."""
import sqlite3
from collections import Counter

db_path = r"C:\Users\ayrto\indexer-api\indexer.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Total projects
cur.execute("SELECT COUNT(*) FROM catalog_projects")
total = cur.fetchone()[0]

# Assessed projects
cur.execute("SELECT COUNT(*) FROM catalog_projects WHERE quality_score IS NOT NULL")
assessed = cur.fetchone()[0]

# Avg quality score
cur.execute("SELECT AVG(quality_score) FROM catalog_projects WHERE quality_score IS NOT NULL")
avg_score = cur.fetchone()[0]

# Production ready count
cur.execute("SELECT COUNT(*) FROM catalog_projects WHERE production_readiness IN ('production', 'mature')")
prod_ready = cur.fetchone()[0]

# By production readiness
cur.execute("SELECT production_readiness, COUNT(*) FROM catalog_projects GROUP BY production_readiness ORDER BY COUNT(*) DESC")
by_readiness = dict(cur.fetchall())

# By quality tier
cur.execute("""
    SELECT
        CASE
            WHEN quality_score >= 80 THEN 'excellent'
            WHEN quality_score >= 60 THEN 'good'
            WHEN quality_score >= 40 THEN 'fair'
            WHEN quality_score IS NOT NULL THEN 'poor'
            ELSE 'unknown'
        END as tier,
        COUNT(*)
    FROM catalog_projects
    GROUP BY tier
""")
by_tier = dict(cur.fetchall())

# Top quality projects
cur.execute("""
    SELECT name, production_readiness, quality_score
    FROM catalog_projects
    WHERE quality_score IS NOT NULL
    ORDER BY quality_score DESC
    LIMIT 5
""")
top_quality = cur.fetchall()

print("=" * 50)
print("QUALITY ASSESSMENT STATUS")
print("=" * 50)
print(f"\nProgress: {assessed}/{total} ({100*assessed//total}%)")
print(f"Avg Quality Score: {avg_score:.1f}/100" if avg_score else "Avg Quality Score: N/A")
print(f"Production Ready: {prod_ready}")

print(f"\nBy Production Readiness:")
for level, count in by_readiness.items():
    print(f"  {level or 'unknown'}: {count}")

print(f"\nBy Quality Tier:")
for tier, count in by_tier.items():
    print(f"  {tier}: {count}")

print(f"\nTop 5 Quality Projects:")
for name, readiness, score in top_quality:
    print(f"  {name}: {score:.1f} ({readiness})")

conn.close()
