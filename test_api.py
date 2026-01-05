"""Quick API test script."""
import requests
import sys
import time

BASE_URL = "http://127.0.0.1:8000"

# Check for catalog-all mode
if len(sys.argv) > 1 and sys.argv[1] == "catalog-all":
    print("=== CATALOG ALL MODE ===")

    # Login
    r = requests.post(f"{BASE_URL}/api/v1/auth/login", data={"username": "test@example.com", "password": "Test1234"})
    if r.status_code != 200:
        print(f"Login failed: {r.text}")
        sys.exit(1)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Trigger scan
    print("\n1. Triggering scan...")
    r = requests.post(
        f"{BASE_URL}/api/v1/catalog/scan",
        headers=headers,
        json={"paths": [r"C:\Users\ayrto"], "max_depth": 4}
    )
    print(f"   Status: {r.status_code}")
    if r.status_code == 202:
        job = r.json()
        job_id = job["job_id"]
        print(f"   Job ID: {job_id}")
        print(f"   Message: {job['message']}")

        # Monitor
        print("\n2. Monitoring job progress...")
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
                discovered = result.get("discovered", 0)
                created = result.get("created", 0)
                print(f"   [{i*5}s] {job_status} | Discovered: {discovered} | Created: {created}")

                if job_status in ("completed", "failed"):
                    print(f"\n   Final result: {result}")
                    break
            else:
                print(f"   [{i*5}s] Error: {r.status_code}")

        # Show projects
        print("\n3. Listing cataloged projects...")
        r = requests.get(f"{BASE_URL}/api/v1/catalog/projects?limit=10", headers=headers)
        if r.status_code == 200:
            data = r.json()
            print(f"   Total: {data['total']} projects")
            for p in data["items"][:5]:
                langs = ", ".join(p.get("languages", [])[:3])
                print(f"   - {p['name']}: [{langs}]")

        # Trigger LLM analysis
        print("\n4. Triggering LLM analysis...")
        r = requests.post(f"{BASE_URL}/api/v1/catalog/analyze-all", headers=headers)
        if r.status_code == 202:
            job = r.json()
            print(f"   LLM Analysis Job: {job['job_id']}")
            print(f"   Message: {job['message']}")
        else:
            print(f"   Error: {r.text}")

        # Trigger embedding index
        print("\n5. Triggering embedding index...")
        r = requests.post(f"{BASE_URL}/api/v1/catalog/index-embeddings", headers=headers)
        if r.status_code == 202:
            job = r.json()
            print(f"   Embedding Index Job: {job['job_id']}")
        else:
            print(f"   Error: {r.text}")
    else:
        print(f"   Error: {r.text}")

    print("\n=== CATALOG ALL COMPLETE ===")
    sys.exit(0)

# Test health
print("1. Testing health endpoint...")
r = requests.get(f"{BASE_URL}/health")
print(f"   Status: {r.status_code}, Response: {r.json()}")

# Register user first
print("\n2. Registering test user...")
r = requests.post(
    f"{BASE_URL}/api/v1/auth/register",
    json={
        "email": "test@example.com",
        "password": "Test1234",
        "full_name": "Test User",
        "organization_name": "TestOrg"
    }
)
if r.status_code == 201:
    print(f"   User created: {r.json()['email']}")
elif r.status_code == 400 and "already registered" in r.text:
    print("   User already exists, continuing...")
else:
    print(f"   Error: {r.status_code} - {r.text}")

# Login
print("\n3. Testing login...")
r = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    data={"username": "test@example.com", "password": "Test1234"}
)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    token = r.json()["access_token"]
    print(f"   Token: {token[:50]}...")
else:
    print(f"   Error: {r.text}")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# Get current user
print("\n4. Testing /auth/me...")
r = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    print(f"   User: {r.json()['email']}")

# Skip index tests and go directly to catalog tests
print("\n5-10. [SKIPPED] Index tests - focusing on catalog LLM endpoints")

# ========== Catalog LLM Tests ==========

print("\n" + "="*50)
print("CATALOG LLM TESTS")
print("="*50)

# Test LLM status
print("\n11. Testing LLM status...")
r = requests.get(f"{BASE_URL}/api/v1/catalog/llm/status", headers=headers)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    status = r.json()
    llm_info = status.get('llm', {})
    embed_info = status.get('embeddings', {})
    print(f"   LLM Available: {llm_info.get('available')}")
    print(f"   LLM Model: {llm_info.get('model')}")
    print(f"   Embeddings Available: {embed_info.get('available')}")
    print(f"   Indexed Projects: {embed_info.get('indexed_projects')}")

# List catalog projects
print("\n12. Listing catalog projects...")
r = requests.get(f"{BASE_URL}/api/v1/catalog/projects?limit=5", headers=headers)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"   Total projects: {data.get('total', 0)}")
    for p in data.get("items", [])[:3]:
        langs = ", ".join(p.get("languages", [])[:3])
        print(f"   - {p['name']}: [{langs}]")

# Test natural language search
print("\n13. Testing natural language search: 'python web'...")
r = requests.get(
    f"{BASE_URL}/api/v1/catalog/search/natural",
    headers=headers,
    params={"q": "python web", "limit": 5}  # Correct param name
)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    results = data.get('results', [])
    print(f"   Found {len(results)} results")
    for result in results[:3]:
        score = result.get('relevance_score', 0)
        langs = ", ".join(result.get('languages', [])[:2])
        print(f"   - {result['name']} (score: {score:.3f}) [{langs}]")
else:
    print(f"   Error: {r.text}")

# Test semantic search
print("\n14. Testing semantic search: 'machine learning'...")
r = requests.get(
    f"{BASE_URL}/api/v1/catalog/search/semantic",
    headers=headers,
    params={"q": "machine learning", "limit": 5}  # Correct param name
)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    results = data.get('results', [])
    print(f"   Found {len(results)} results")
    for result in results[:3]:
        score = result.get('relevance_score', 0)
        print(f"   - {result['name']} (score: {score:.3f})")
else:
    print(f"   Response: {r.text[:200]}")

# Test basic catalog search
print("\n15. Testing catalog search: 'discord'...")
r = requests.get(
    f"{BASE_URL}/api/v1/catalog/search",
    headers=headers,
    params={"q": "discord", "limit": 5}  # Correct param name
)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    results = data.get('results', [])
    print(f"   Found {len(results)} results")
    for result in results[:3]:
        print(f"   - {result['name']}")
else:
    print(f"   Response: {r.text[:200]}")

print("\n" + "="*50)
print("[OK] All tests completed!")
print("="*50)
