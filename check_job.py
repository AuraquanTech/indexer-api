"""Check job status."""
import requests
import sys
import time

BASE_URL = "http://127.0.0.1:8000"
JOB_ID = sys.argv[1] if len(sys.argv) > 1 else "eaa46736-e5d2-4bbd-8200-3ec9fa87db08"

# Login
r = requests.post(f"{BASE_URL}/api/v1/auth/login", data={"username": "test@example.com", "password": "Test1234"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Check job
r = requests.get(f"{BASE_URL}/api/v1/catalog/jobs/{JOB_ID}", headers=headers)
if r.status_code == 200:
    status = r.json()
    job_status = status["status"]
    runs = status.get("runs", [])
    result = runs[0].get("result", {}) if runs else {}
    if result is None:
        result = {}
    analyzed = result.get("analyzed", 0)
    total = result.get("total", "?")
    print(f"Job ID: {JOB_ID}")
    print(f"Status: {job_status}")
    print(f"Progress: {analyzed}/{total}")
    if job_status == "completed":
        print(f"Result: {result}")
    elif job_status == "failed":
        print(f"Error: {status.get('last_error', {})}")
else:
    print(f"Error: {r.status_code}")
