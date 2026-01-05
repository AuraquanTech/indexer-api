"""Get quality report."""
import requests

BASE_URL = "http://127.0.0.1:8000"

# Login
r = requests.post(f"{BASE_URL}/api/v1/auth/login", data={"username": "test@example.com", "password": "Test1234"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get quality report
r = requests.get(f"{BASE_URL}/api/v1/catalog/quality-report", headers=headers)
if r.status_code == 200:
    report = r.json()
    print(f"=== Quality Report ===")
    print(f"Total projects: {report['total_projects']}")
    print(f"Assessed projects: {report['assessed_projects']}")
    print(f"Avg quality score: {report['avg_quality_score']}")
    print(f"Production ready: {report['production_ready_count']}")

    print(f"\nBy Production Readiness:")
    for level, count in sorted(report['by_production_readiness'].items(), key=lambda x: -x[1]):
        print(f"  {level}: {count}")

    print(f"\nBy Quality Tier:")
    for tier, count in report['by_quality_tier'].items():
        print(f"  {tier}: {count}")

    if report.get('top_quality'):
        print(f"\nTop Quality Projects:")
        for p in report['top_quality'][:5]:
            print(f"  - {p['name']} ({p['production_readiness']}, score: {p['quality_score']})")

    if report.get('needs_attention'):
        print(f"\nProjects Needing Attention:")
        for p in report['needs_attention'][:5]:
            print(f"  - {p['name']} (score: {p['quality_score']}, issues: {', '.join(p['key_issues'][:2]) if p['key_issues'] else 'N/A'})")
else:
    print(f"Failed: {r.status_code}")
    print(r.text)
