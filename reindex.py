"""Trigger embedding reindex."""
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

# Login
r = requests.post(f"{BASE_URL}/api/v1/auth/login", data={"username": "test@example.com", "password": "Test1234"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Trigger embedding reindex
print("Triggering embedding reindex...")
r = requests.post(f"{BASE_URL}/api/v1/catalog/index-embeddings", headers=headers)
print(f"Status: {r.status_code}")
job = r.json()
print(f"Job ID: {job['job_id']}")
print(f"Message: {job['message']}")

# Monitor job
job_id = job["job_id"]
print("\nMonitoring job progress...")
for i in range(60):  # Up to 5 minutes
    time.sleep(5)
    r = requests.get(f"{BASE_URL}/api/v1/catalog/jobs/{job_id}", headers=headers)
    if r.status_code == 200:
        status = r.json()
        job_status = status["status"]
        runs = status.get("runs", [])
        result = runs[0].get("result") if runs and runs[0].get("result") else {}
        if result is None:
            result = {}
        indexed = result.get("indexed", 0)
        print(f"[{(i+1)*5}s] {job_status} | Indexed: {indexed}")

        if job_status in ("completed", "failed"):
            print(f"\nFinal result: {result}")
            break
    else:
        print(f"[{(i+1)*5}s] Error: {r.status_code}")

print("\n=== Done ===")
