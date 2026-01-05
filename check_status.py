#!/usr/bin/env python3
"""Check catalog status."""
import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

# Login
r = requests.post(f"{BASE_URL}/api/v1/auth/login", data={"username": "test@example.com", "password": "Test1234"})
if r.status_code != 200:
    print(f"Login failed: {r.text}")
    sys.exit(1)
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get projects
print("=== Catalog Projects ===")
r = requests.get(f"{BASE_URL}/api/v1/catalog/projects?limit=10", headers=headers)
if r.status_code != 200:
    print(f"Error: {r.status_code}")
    print(r.text[:500])
else:
    data = r.json()
    print(f"Total projects: {data.get('total', 'N/A')}")
    print("\nTop 10 projects:")
    for p in data.get("items", [])[:10]:
        langs = ", ".join(p.get("languages", [])[:3])
        print(f"  - {p['name']}: [{langs}]")

# Health report
print("\n=== Health Report ===")
r = requests.get(f"{BASE_URL}/api/v1/catalog/health-report", headers=headers)
if r.status_code == 200:
    report = r.json()
    print(f"Total projects: {report['total_projects']}")
    by_lang = dict(list(report.get('by_language', {}).items())[:5])
    print(f"Top languages: {by_lang}")
    print(f"Average health: {report.get('avg_health_score')}")
else:
    print(f"Error: {r.status_code} - {r.text[:200]}")

# LLM status
print("\n=== LLM Status ===")
r = requests.get(f"{BASE_URL}/api/v1/catalog/llm/status", headers=headers)
if r.status_code == 200:
    status = r.json()
    print(f"LLM: {status['llm']['available']} ({status['llm']['model']})")
    print(f"Embeddings: {status['embeddings']['available']}")
    print(f"Indexed projects: {status['embeddings']['indexed_projects']}")
else:
    print(f"Error: {r.status_code}")

print("\n=== Done ===")
