"""Trigger quality assessment for remaining projects."""
import requests

BASE_URL = "http://127.0.0.1:8000"

# Login
r = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    data={"username": "test@example.com", "password": "Test1234"},
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)
print(f"Login status: {r.status_code}")
if r.status_code != 200:
    print(f"Login response: {r.text}")
    exit(1)

token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Trigger quality assessment (without force_refresh - only unassessed)
print("\nTriggering quality assessment for remaining projects...")
r = requests.post(f"{BASE_URL}/api/v1/catalog/assess-quality", headers=headers)
print(f"Response status: {r.status_code}")

if r.status_code == 200:
    job = r.json()
    print(f"Job ID: {job['job_id']}")
    print(f"Projects to assess: {job['projects_to_assess']}")
    print(f"\nMonitor with: python check_job.py {job['job_id']}")
else:
    print(f"Error: {r.text}")
