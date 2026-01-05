"""Test DAM and Code Discovery endpoints."""
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

# Test health
print("1. Testing health endpoint...")
r = requests.get(f"{BASE_URL}/health")
print(f"   Status: {r.status_code}")
if r.status_code != 200:
    print("   Server not running!")
    exit(1)

# Login (using existing test user or create new)
print("\n2. Logging in...")
r = requests.post(
    f"{BASE_URL}/api/v1/auth/register",
    json={
        "email": "damtest@example.com",
        "password": "Test1234",
        "full_name": "DAM Test User",
        "organization_name": "DAMTestOrg"
    }
)
if r.status_code not in [201, 400]:
    print(f"   Registration error: {r.status_code} - {r.text}")

r = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    data={"username": "damtest@example.com", "password": "Test1234"}
)
if r.status_code != 200:
    print(f"   Login error: {r.status_code} - {r.text}")
    exit(1)
token = r.json()["access_token"]
print(f"   Logged in successfully")

headers = {"Authorization": f"Bearer {token}"}

# Create an index for testing - first check if it exists
print("\n3. Getting or creating test index...")
r = requests.get(f"{BASE_URL}/api/v1/indexes", headers=headers)
if r.status_code == 200:
    indexes = r.json()
    index = next((i for i in indexes if i["name"] == "DAMCodeTest2"), None)
    if index:
        index_id = index["id"]
        print(f"   Using existing index: {index_id}")
    else:
        # Create new index
        r = requests.post(
            f"{BASE_URL}/api/v1/indexes",
            headers=headers,
            json={
                "name": "DAMCodeTest2",
                "root_path": r"C:\Users\ayrto\indexer-api",
                "include_patterns": ["*"],
                "exclude_patterns": ["*.git*", "*node_modules*", "*__pycache__*", "*.pyc"],
            }
        )
        if r.status_code == 201:
            index = r.json()
            index_id = index["id"]
            print(f"   Created index: {index_id}")
        else:
            print(f"   Error creating index: {r.status_code} - {r.text}")
            exit(1)
else:
    print(f"   Error listing indexes: {r.status_code} - {r.text}")
    exit(1)

# Run file scan first
print("\n4. Running file scan...")
r = requests.post(
    f"{BASE_URL}/api/v1/indexes/{index_id}/scan",
    headers=headers,
    json={"job_type": "full_scan"}
)
if r.status_code == 202:
    job = r.json()
    print(f"   Scan job started: {job['id']}")

    # Wait for scan to complete
    print("   Waiting for scan to complete...")
    for i in range(30):
        time.sleep(1)
        r = requests.get(f"{BASE_URL}/api/v1/indexes/{index_id}/jobs/{job['id']}", headers=headers)
        if r.status_code == 200:
            job_status = r.json()
            if job_status["status"] in ["completed", "failed"]:
                print(f"   Scan {job_status['status']}: {job_status['processed_files']} files")
                break
        print(".", end="", flush=True)
    print()
else:
    print(f"   Note: {r.status_code} - {r.text}")

# Test Code Discovery endpoints
print("\n5. Testing Code Analysis endpoint...")
r = requests.post(
    f"{BASE_URL}/api/v1/indexes/{index_id}/code/analyze",
    headers=headers
)
print(f"   Status: {r.status_code}")
if r.status_code == 202:
    job = r.json()
    print(f"   Code analysis job started: {job['job_id']}")
    print(f"   Files to analyze: {job['total_files_to_analyze']}")

    # Wait for analysis to complete
    print("   Waiting for analysis to complete...")
    time.sleep(5)
else:
    print(f"   Error: {r.text}")

# Test Code files endpoint
print("\n6. Testing Code files endpoint...")
r = requests.get(
    f"{BASE_URL}/api/v1/indexes/{index_id}/code/files",
    headers=headers,
    params={"language": "python", "page_size": 5}
)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    result = r.json()
    print(f"   Total code files: {result['total']}")
    for f in result["items"][:3]:
        code = f.get("code", {})
        print(f"   - {f['filename']}: {code.get('lines_total', 'N/A')} lines, {code.get('language', 'N/A')}")
else:
    print(f"   Error: {r.text}")

# Test Project stats
print("\n7. Testing Project stats endpoint...")
r = requests.get(
    f"{BASE_URL}/api/v1/indexes/{index_id}/code/stats",
    headers=headers
)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    stats = r.json()
    print(f"   Total code files: {stats['total_code_files']}")
    print(f"   Total lines: {stats['total_lines']}")
    print(f"   Languages: {list(stats['language_breakdown'].keys())}")
else:
    print(f"   Error: {r.text}")

# Test MVP readiness
print("\n8. Testing MVP Readiness endpoint...")
r = requests.get(
    f"{BASE_URL}/api/v1/indexes/{index_id}/code/mvp-score",
    headers=headers
)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    mvp = r.json()
    print(f"   Score: {mvp['score']}/100 (Grade: {mvp['grade']})")
    print(f"   Has README: {mvp['has_readme']}")
    print(f"   Has Tests: {mvp['has_tests']}")
    print(f"   Has License: {mvp['has_license']}")
    print(f"   Recommendations:")
    for rec in mvp["recommendations"][:3]:
        print(f"     - {rec}")
else:
    print(f"   Error: {r.text}")

# Test Dependencies
print("\n9. Testing Dependencies endpoint...")
r = requests.get(
    f"{BASE_URL}/api/v1/indexes/{index_id}/code/dependencies",
    headers=headers
)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    deps = r.json()
    print(f"   Total unique imports: {deps['total_unique_imports']}")
    print(f"   Top stdlib imports: {[d['name'] for d in deps['stdlib_imports'][:5]]}")
    print(f"   Top third-party imports: {[d['name'] for d in deps['third_party_imports'][:5]]}")
else:
    print(f"   Error: {r.text}")

# Test DAM endpoints
print("\n10. Testing DAM Analysis endpoint...")
r = requests.post(
    f"{BASE_URL}/api/v1/indexes/{index_id}/dam/analyze",
    headers=headers
)
print(f"   Status: {r.status_code}")
if r.status_code == 202:
    job = r.json()
    print(f"   DAM analysis job started: {job['job_id']}")
    print(f"   Files to analyze: {job['total_files_to_analyze']}")
else:
    print(f"   Note: {r.text}")

# Test DAM stats
print("\n11. Testing DAM Stats endpoint...")
r = requests.get(
    f"{BASE_URL}/api/v1/indexes/{index_id}/dam/stats",
    headers=headers
)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    stats = r.json()
    print(f"   Total assets: {stats['total_assets']}")
    print(f"   Images: {stats['total_images']}")
    print(f"   Videos: {stats['total_videos']}")
    print(f"   Audio: {stats['total_audio']}")
    print(f"   Documents: {stats['total_documents']}")
else:
    print(f"   Error: {r.text}")

print("\n[OK] All DAM and Code Discovery endpoints tested!")
