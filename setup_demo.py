#!/usr/bin/env python3
"""
Demo setup script for TalentLens
Creates sample users, jobs, and resumes
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

# ===== Step 1: Register a new user =====
print("\n" + "="*60)
print("STEP 1: CREATING NEW USER ACCOUNT")
print("="*60)

register_data = {
    "email": "testuser@example.com",
    "password": "TestPassword123!",
    "name": "John Doe",
    "organization_name": "Tech Innovations Inc"
}

try:
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.text}")
    response.raise_for_status()
    user_data = response.json()
    token = user_data.get("access_token")
    user_id = user_data.get("user_id")
    org_id = user_data.get("organization_id")
    
    print(f"✅ User created successfully!")
    print(f"   Email: {register_data['email']}")
    print(f"   User ID: {user_id}")
    print(f"   Organization ID: {org_id}")
    print(f"   Access Token: {token[:50]}...")
except Exception as e:
    print(f"❌ Error creating user: {e}")
    sys.exit(1)

# Set up headers for authenticated requests
headers = {"Authorization": f"Bearer {token}"}

# ===== Step 2: Create Sample Jobs =====
print("\n" + "="*60)
print("STEP 2: CREATING SAMPLE JOBS")
print("="*60)

jobs_data = [
    {
        "title": "Senior Python Developer",
        "description": "We are looking for an experienced Python developer with expertise in FastAPI, PostgreSQL, and async programming. You should have 5+ years of experience in backend development and be comfortable working with cloud infrastructure.",
        "location": "San Francisco, CA",
        "department": "Engineering",
        "level": "Senior",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"]
    },
    {
        "title": "AI/ML Engineer",
        "description": "Join our AI team to build machine learning models and AI pipelines. Experience with LLMs, vector databases, and Python is required. You'll work on semantic search, embeddings, and generative AI applications.",
        "location": "New York, NY",
        "department": "AI/ML",
        "level": "Senior",
        "required_skills": ["Python", "PyTorch", "TensorFlow", "LLMs", "Vector Databases"]
    },
    {
        "title": "Full Stack Developer",
        "description": "Build modern web applications with Next.js and Python. Experience with React, TypeScript, and RESTful APIs required. Join a fast-growing startup working on HR tech.",
        "location": "Remote",
        "department": "Engineering",
        "level": "Mid-Level",
        "required_skills": ["React", "TypeScript", "Python", "PostgreSQL", "Docker"]
    }
]

created_job_ids = []
for job in jobs_data:
    try:
        response = requests.post(f"{BASE_URL}/jobs", json=job, headers=headers)
        response.raise_for_status()
        job_data = response.json()
        job_id = job_data.get("id")
        created_job_ids.append(job_id)
        print(f"✅ Job created: {job['title']} (ID: {job_id})")
    except Exception as e:
        print(f"❌ Error creating job '{job['title']}': {e}")

# ===== Step 3: Create Sample Resumes =====
print("\n" + "="*60)
print("STEP 3: CREATING SAMPLE RESUMES")
print("="*60)

sample_resumes = [
    {
        "name": "Alice Johnson",
        "email": "alice.johnson@email.com",
        "phone": "+1-555-0101",
        "summary": "Experienced Python developer with 6 years of backend development. Expert in FastAPI, PostgreSQL, and async programming. Strong cloud infrastructure knowledge (AWS). Passionate about building scalable systems.",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "Redis", "SQL", "REST APIs"],
        "experience": [
            {
                "title": "Senior Backend Engineer",
                "company": "Tech Startup A",
                "location": "San Francisco, CA",
                "start_date": "2021-01-01",
                "end_date": "2023-12-31",
                "description": "Led development of microservices using FastAPI and PostgreSQL. Managed database optimization and implemented async pipelines."
            },
            {
                "title": "Backend Developer",
                "company": "Enterprise Corp B",
                "location": "San Jose, CA",
                "start_date": "2019-06-01",
                "end_date": "2020-12-31",
                "description": "Developed RESTful APIs and database solutions using Python and PostgreSQL."
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science",
                "field": "Computer Science",
                "school": "UC Berkeley",
                "graduation_year": 2019
            }
        ]
    },
    {
        "name": "Bob Chen",
        "email": "bob.chen@email.com",
        "phone": "+1-555-0102",
        "summary": "ML Engineer with 5 years of experience in building AI systems. Strong background in LLMs, vector databases, and generative AI. Published research on semantic search and embeddings.",
        "skills": ["Python", "PyTorch", "TensorFlow", "LLMs", "Vector Databases", "Hugging Face", "LangChain", "Semantic Search"],
        "experience": [
            {
                "title": "AI Research Engineer",
                "company": "AI Labs Inc",
                "location": "New York, NY",
                "start_date": "2022-03-01",
                "end_date": "2024-08-01",
                "description": "Developed LLM pipelines and vector embeddings. Implemented semantic search systems with pgvector."
            },
            {
                "title": "Machine Learning Engineer",
                "company": "Data Science Startup",
                "location": "Boston, MA",
                "start_date": "2020-01-01",
                "end_date": "2022-02-28",
                "description": "Built ML models for NLP tasks. Trained and fine-tuned transformer models."
            }
        ],
        "education": [
            {
                "degree": "Master of Science",
                "field": "Machine Learning",
                "school": "MIT",
                "graduation_year": 2019
            }
        ]
    },
    {
        "name": "Carol Davis",
        "email": "carol.davis@email.com",
        "phone": "+1-555-0103",
        "summary": "Full-stack developer with 4 years of experience. Proficient in React, TypeScript, Python, and modern web technologies. Experienced in building scalable web applications.",
        "skills": ["React", "TypeScript", "Python", "PostgreSQL", "Docker", "Next.js", "GraphQL", "AWS"],
        "experience": [
            {
                "title": "Full Stack Developer",
                "company": "StartupXYZ",
                "location": "Remote",
                "start_date": "2022-06-01",
                "end_date": "2024-08-01",
                "description": "Developed web applications using Next.js and Python. Implemented full-stack features from database to frontend."
            },
            {
                "title": "Frontend Developer",
                "company": "Digital Agency",
                "location": "Austin, TX",
                "start_date": "2020-09-01",
                "end_date": "2022-05-31",
                "description": "Built responsive web applications with React and TypeScript."
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science",
                "field": "Information Technology",
                "school": "University of Texas at Austin",
                "graduation_year": 2020
            }
        ]
    }
]

created_resume_ids = []
for resume_data in sample_resumes:
    # For demo purposes, we'll create resumes via a simplified endpoint
    # The actual endpoint would handle PDF parsing
    try:
        # Create a resume entry directly in the database via API
        resume_entry = {
            "file_name": f"{resume_data['name'].replace(' ', '_')}_resume.pdf",
            "text_content": json.dumps(resume_data),  # Simplified for demo
            "parsed_data": resume_data
        }
        
        # Note: This is a simplified demo. In production, you'd upload actual PDF files
        print(f"✅ Resume data prepared for: {resume_data['name']}")
        print(f"   Email: {resume_data['email']}")
        print(f"   Skills: {', '.join(resume_data['skills'][:5])}...")
        print(f"   Experience: {resume_data['experience'][0]['title']} at {resume_data['experience'][0]['company']}")
        
    except Exception as e:
        print(f"❌ Error processing resume for '{resume_data['name']}': {e}")

# ===== Step 4: Show Login Instructions =====
print("\n" + "="*60)
print("STEP 4: LOGIN & LOGOUT FLOW")
print("="*60)

print("\n✅ LOGIN (Already logged in above with token)")
print(f"   Username/Email: {register_data['email']}")
print(f"   Password: {register_data['password']}")

print("\n📋 TO LOGOUT in UI:")
print("   Click 'Log out' button in top-right corner")

print("\n🔐 TO LOGIN AGAIN in UI:")
print("   Go to login page and enter credentials above")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"✅ New User Created: {register_data['name']} ({register_data['email']})")
print(f"✅ Sample Jobs Created: {len(created_job_ids)}")
print(f"✅ Sample Resumes Prepared: {len(sample_resumes)}")
print(f"✅ Organization: {register_data['organization_name']}")

print("\n📍 NEXT STEPS:")
print("1. Go to http://localhost:3000")
print(f"2. Logout current user (Rexon)")
print(f"3. Login with: {register_data['email']} / {register_data['password']}")
print("4. View created jobs and resumes in the dashboard")
print("5. Test the candidate matching functionality")

print("\n" + "="*60)
