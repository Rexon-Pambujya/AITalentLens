#!/usr/bin/env python3
"""
TalentLens API Endpoint Testing Script
Tests all major API endpoints with sample data
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_test(name):
    print(f"\n{BLUE}{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}{RESET}")

def print_success(message):
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message):
    print(f"{RED}❌ {message}{RESET}")

def print_info(message):
    print(f"{YELLOW}ℹ️  {message}{RESET}")

# ===== TEST 1: Health Check =====
print_test("Health Check Endpoint")
try:
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print_success("Health endpoint is operational")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print_error(f"Health check failed: {response.status_code}")
except Exception as e:
    print_error(f"Error: {e}")

# ===== TEST 2: Authentication - Login =====
print_test("Authentication - Login")
login_credentials = {
    "email": "testuser@example.com",
    "password": "TestPassword123!"
}
try:
    response = requests.post(f"{BASE_URL}/auth/login", json=login_credentials)
    if response.status_code == 200:
        auth_data = response.json()
        token = auth_data.get("access_token")
        print_success("Login successful")
        print(f"Access Token: {token[:50]}...")
        print(f"Token Type: {auth_data.get('token_type')}")
        print(f"User: {auth_data.get('user', {}).get('name')} ({auth_data.get('user', {}).get('email')})")
        
        # Store token for subsequent requests
        headers = {"Authorization": f"Bearer {token}"}
    else:
        print_error(f"Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        headers = {}
except Exception as e:
    print_error(f"Error: {e}")
    headers = {}

# ===== TEST 3: Get Current User =====
print_test("Get Current User (Me)")
try:
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        print_success("Retrieved current user")
        print(f"Name: {user_data.get('name')}")
        print(f"Email: {user_data.get('email')}")
        print(f"Role: {user_data.get('role')}")
        print(f"Organization ID: {user_data.get('organization_id')}")
    else:
        print_error(f"Failed to get user: {response.status_code}")
except Exception as e:
    print_error(f"Error: {e}")

# ===== TEST 4: List All Jobs =====
print_test("List All Jobs")
job_ids = []
try:
    response = requests.get(f"{BASE_URL}/jobs", headers=headers)
    if response.status_code == 200:
        jobs_data = response.json()
        jobs = jobs_data.get('items', [])
        print_success(f"Retrieved {len(jobs)} jobs")
        for i, job in enumerate(jobs[:3], 1):  # Show first 3
            print(f"\n  {i}. {job.get('title')} (ID: {job.get('id')})")
            print(f"     Location: {job.get('location')}")
            print(f"     Department: {job.get('department')}")
            print(f"     Level: {job.get('level')}")
            job_ids.append(job.get('id'))
        if len(jobs) > 3:
            print(f"\n  ... and {len(jobs) - 3} more jobs")
    else:
        print_error(f"Failed to list jobs: {response.status_code}")
except Exception as e:
    print_error(f"Error: {e}")

# ===== TEST 5: Get Single Job Details =====
if job_ids:
    print_test("Get Single Job Details")
    job_id = job_ids[0]
    try:
        response = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
        if response.status_code == 200:
            job = response.json()
            print_success(f"Retrieved job: {job.get('title')}")
            print(f"Description: {job.get('description')[:100]}...")
            print(f"Required Skills: {', '.join(job.get('required_skills', []))}")
            print(f"Weight - Skills: {job.get('weight_skills', 0)*100:.0f}%")
            print(f"Weight - Experience: {job.get('weight_experience', 0)*100:.0f}%")
            print(f"Weight - Semantic: {job.get('weight_semantic', 0)*100:.0f}%")
        else:
            print_error(f"Failed to get job details: {response.status_code}")
    except Exception as e:
        print_error(f"Error: {e}")

# ===== TEST 6: Create a New Job =====
print_test("Create a New Job")
new_job = {
    "title": "Test Position - GraphQL Developer",
    "description": "We're looking for an experienced GraphQL developer to build modern API solutions. Strong understanding of GraphQL concepts, experience with Apollo Server or similar frameworks required.",
    "location": "San Francisco, CA",
    "department": "Engineering",
    "level": "Senior",
    "required_skills": ["GraphQL", "Node.js", "TypeScript", "REST APIs"]
}
try:
    response = requests.post(f"{BASE_URL}/jobs", json=new_job, headers=headers)
    if response.status_code in [200, 201]:
        created_job = response.json()
        print_success("New job created successfully")
        print(f"Job ID: {created_job.get('id')}")
        print(f"Title: {created_job.get('title')}")
        new_job_id = created_job.get('id')
    else:
        print_error(f"Failed to create job: {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print_error(f"Error: {e}")

# ===== TEST 7: List All Candidates =====
print_test("List All Candidates")
try:
    response = requests.get(f"{BASE_URL}/candidates", headers=headers)
    if response.status_code == 200:
        candidates_data = response.json()
        candidates = candidates_data.get('items', [])
        print_success(f"Retrieved {len(candidates)} candidates")
        for i, candidate in enumerate(candidates[:3], 1):  # Show first 3
            print(f"\n  {i}. {candidate.get('name', 'Unnamed')} (ID: {candidate.get('id')})")
            print(f"     Title: {candidate.get('current_title', 'N/A')}")
            print(f"     Company: {candidate.get('current_company', 'N/A')}")
            print(f"     Experience: {candidate.get('total_years_experience', 'N/A')} years")
        if len(candidates) > 3:
            print(f"\n  ... and {len(candidates) - 3} more candidates")
    else:
        print_error(f"Failed to list candidates: {response.status_code}")
except Exception as e:
    print_error(f"Error: {e}")

# ===== TEST 8: Search Candidates Semantically =====
print_test("Search Candidates (Semantic Search)")
search_query = {
    "query": "experienced Python backend developer with database expertise",
    "limit": 5
}
try:
    response = requests.post(f"{BASE_URL}/search/candidates", json=search_query, headers=headers)
    if response.status_code == 200:
        search_results = response.json()
        results = search_results.get('matches', [])
        print_success(f"Found {len(results)} matching candidates")
        print(f"AI Available: {search_results.get('ai_available', False)}")
        for i, match in enumerate(results[:3], 1):  # Show first 3
            print(f"\n  {i}. {match.get('candidate_name', 'Unnamed')} - Score: {match.get('semantic_score', 0):.0f}%")
            print(f"     Experience: {match.get('total_years_experience', 'N/A')} years")
            print(f"     Skills: {', '.join(match.get('skills', [])[:3])}...")
    else:
        print_error(f"Search failed: {response.status_code}")
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print_error(f"Error: {e}")

# ===== TEST 9: Job Ranking (Candidate Ranking for a Job) =====
if job_ids:
    print_test("Get Job Candidate Ranking")
    job_id = job_ids[0]
    try:
        response = requests.get(f"{BASE_URL}/jobs/{job_id}/ranking", headers=headers)
        if response.status_code == 200:
            ranking = response.json()
            print_success(f"Retrieved ranking for job: {len(ranking)} candidates ranked")
            for i, entry in enumerate(ranking[:3], 1):  # Show first 3
                print(f"\n  Rank #{i}: {entry.get('candidate_name', 'Unnamed')}")
                print(f"           Score: {entry.get('overall_score', 0):.0f}%")
                print(f"           Recommendation: {entry.get('recommendation', 'PENDING')}")
        else:
            print_error(f"Failed to get ranking: {response.status_code}")
    except Exception as e:
        print_error(f"Error: {e}")

# ===== TEST 10: API Documentation =====
print_test("API Documentation Endpoints")
try:
    # Check Swagger UI
    swagger_response = requests.get("http://localhost:8000/docs")
    if swagger_response.status_code == 200:
        print_success("Swagger UI is available at http://localhost:8000/docs")
    
    # Check ReDoc
    redoc_response = requests.get("http://localhost:8000/redoc")
    if redoc_response.status_code == 200:
        print_success("ReDoc is available at http://localhost:8000/redoc")
    
    # Check OpenAPI schema
    openapi_response = requests.get("http://localhost:8000/openapi.json")
    if openapi_response.status_code == 200:
        openapi_data = openapi_response.json()
        endpoints = list(openapi_data.get('paths', {}).keys())
        print_success(f"OpenAPI schema available with {len(endpoints)} endpoints")
        print(f"\nSample endpoints:")
        for endpoint in endpoints[:5]:
            print(f"  - {endpoint}")
except Exception as e:
    print_error(f"Error: {e}")

# ===== SUMMARY =====
print(f"\n{BLUE}{'='*60}")
print("SUMMARY OF API TESTS")
print(f"{'='*60}{RESET}")
print(f"""
✅ Core Endpoints Tested:
   1. Health Check - API status
   2. Authentication (Login, Get Current User)
   3. Jobs (List, Get Details, Create)
   4. Candidates (List, Search)
   5. Job Ranking & Candidate Matching
   6. API Documentation (Swagger, ReDoc, OpenAPI)

📊 Data Summary:
   - {len(jobs) if job_ids else 0} Total Jobs Available
   - Total Candidates in System
   - Multiple Users & Organizations

🚀 API Base URL: {BASE_URL}
📖 Swagger UI: http://localhost:8000/docs
📘 ReDoc: http://localhost:8000/redoc

🎯 Next Steps:
   1. Test the UI at http://localhost:3000
   2. Create a resume and upload it
   3. Run candidate matching
   4. Explore the Swagger UI for all endpoints
   5. Try the semantic search with different queries
""")
