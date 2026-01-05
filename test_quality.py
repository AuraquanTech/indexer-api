"""Test quality assessment."""
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

# Login
r = requests.post(f"{BASE_URL}/api/v1/auth/login", data={"username": "test@example.com", "password": "Test1234"})
if r.status_code != 200:
    print(f"Login failed: {r.status_code}")
    exit(1)
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Check LLM status
print("Checking LLM status...")
r = requests.get(f"{BASE_URL}/api/v1/catalog/llm/status", headers=headers)
print(f"LLM Status: {r.json()}")

# List available routes (debug)
print("\nChecking available endpoints...")
r = requests.get(f"{BASE_URL}/openapi.json")
if r.status_code == 200:
    openapi = r.json()
    quality_endpoints = [p for p in openapi.get("paths", {}).keys() if "quality" in p.lower()]
    print(f"Quality endpoints found: {quality_endpoints}")

# Trigger quality assessment
print("\nTriggering quality assessment for all projects...")
r = requests.post(f"{BASE_URL}/api/v1/catalog/assess-quality?force_refresh=true", headers=headers)
print(f"Response status: {r.status_code}")
if r.status_code not in (200, 201, 202):
    print(f"Failed to trigger quality assessment: {r.status_code}")
    print(r.text)
    exit(1)

job = r.json()
print(f"Job ID: {job['job_id']}")
print(f"Projects to assess: {job['projects_to_assess']}")

# Monitor job
job_id = job["job_id"]
print("\nMonitoring job progress...")
for i in range(120):  # Up to 10 minutes
    time.sleep(5)
    r = requests.get(f"{BASE_URL}/api/v1/catalog/jobs/{job_id}", headers=headers)
    if r.status_code == 200:
        status = r.json()
        job_status = status["status"]
        runs = status.get("runs", [])
        result = runs[0].get("result") if runs and runs[0].get("result") else {}
        if result is None:
            result = {}
        assessed = result.get("assessed", 0)
        total = result.get("total", "?")
        print(f"[{(i+1)*5}s] {job_status} | Assessed: {assessed}/{total}")

        if job_status in ("completed", "failed"):
            print(f"\nFinal result: {result}")
            break
    else:
        print(f"[{(i+1)*5}s] Error: {r.status_code}")

# Get quality report
print("\n=== Quality Report ===")
r = requests.get(f"{BASE_URL}/api/v1/catalog/quality-report", headers=headers)
if r.status_code == 200:
    report = r.json()
    print(f"Total projects: {report['total_projects']}")
    print(f"Assessed projects: {report['assessed_projects']}")
    print(f"Avg quality score: {report['avg_quality_score']}")
    print(f"Production ready: {report['production_ready_count']}")
    print(f"\nBy Production Readiness:")
    for level, count in report['by_production_readiness'].items():
        print(f"  {level}: {count}")
    print(f"\nBy Quality Tier:")
    for tier, count in report['by_quality_tier'].items():
        print(f"  {tier}: {count}")
else:
    print(f"Failed to get quality report: {r.status_code}")
    print(r.text)

print("\n=== Done ===")
