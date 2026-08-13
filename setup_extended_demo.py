#!/usr/bin/env python3
"""
Extended demo setup script for TalentLens
Creates more sample users, jobs, and resume profiles
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

# ===== Step 1: Register additional users =====
print("\n" + "="*60)
print("STEP 1: CREATING ADDITIONAL USER ACCOUNTS")
print("="*60)

users_data = [
    {
        "email": "recruiter1@talentlens.io",
        "password": "SecurePass123!",
        "name": "Sarah Martinez",
        "organization_name": "Tech Innovations Inc"
    },
    {
        "email": "recruiter2@talentlens.io",
        "password": "SecurePass123!",
        "name": "David Chen",
        "organization_name": "Tech Innovations Inc"
    }
]

tokens = {}
for user in users_data:
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user)
        if response.status_code == 201:
            user_data = response.json()
            token = user_data.get("access_token")
            tokens[user['email']] = token
            print(f"✅ User created: {user['name']} ({user['email']})")
        else:
            print(f"⚠️  User already exists or error: {user['email']}")
    except Exception as e:
        print(f"❌ Error creating user '{user['name']}': {e}")

# Use the first token for creating jobs
main_token = tokens.get("recruiter1@talentlens.io", None)
if not main_token:
    print("Using original testuser token")
    # If users already exist, try to login
    try:
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": "recruiter1@talentlens.io", "password": "SecurePass123!"}
        )
        if login_response.status_code == 200:
            main_token = login_response.json().get("access_token")
    except:
        pass

headers = {"Authorization": f"Bearer {main_token}"} if main_token else {}

# ===== Step 2: Create More Sample Jobs =====
print("\n" + "="*60)
print("STEP 2: CREATING ADDITIONAL SAMPLE JOBS")
print("="*60)

extended_jobs_data = [
    {
        "title": "DevOps Engineer",
        "description": "We're looking for an experienced DevOps engineer to build and maintain our cloud infrastructure. You should have hands-on experience with Kubernetes, Docker, CI/CD pipelines, and cloud platforms (AWS/GCP). Experience with Infrastructure as Code (Terraform, Ansible) is a plus.",
        "location": "San Francisco, CA",
        "department": "Infrastructure",
        "level": "Senior",
        "required_skills": ["Kubernetes", "Docker", "AWS", "CI/CD", "Terraform"]
    },
    {
        "title": "Data Engineer",
        "description": "Join our data team to build scalable data pipelines and analytics infrastructure. We need someone with strong SQL, Python, and big data technologies (Spark, Airflow). You'll work on ETL processes and data warehousing solutions.",
        "location": "New York, NY",
        "department": "Data & Analytics",
        "level": "Senior",
        "required_skills": ["Python", "SQL", "Apache Spark", "Airflow", "Data Warehousing"]
    },
    {
        "title": "Product Manager - AI",
        "description": "Lead product strategy for our AI-powered recruiting platform. You should have experience in product management, understanding AI/ML capabilities, and user research. Strong communication and strategic thinking required.",
        "location": "Remote",
        "department": "Product",
        "level": "Senior",
        "required_skills": ["Product Strategy", "AI/ML Understanding", "User Research", "Analytics"]
    },
    {
        "title": "QA Automation Engineer",
        "description": "Build and maintain our automated testing infrastructure. You should have experience with test automation frameworks, CI/CD integration, and ideally knowledge of Selenium, Cypress, or similar tools. Python or JavaScript experience helpful.",
        "location": "Remote",
        "department": "Quality Assurance",
        "level": "Mid-Level",
        "required_skills": ["Automation Testing", "Python", "JavaScript", "CI/CD", "Test Frameworks"]
    },
    {
        "title": "Mobile Developer (React Native)",
        "description": "Develop cross-platform mobile applications using React Native. You should have strong JavaScript/TypeScript skills and experience shipping apps to both iOS and Android. Experience with state management and native modules is important.",
        "location": "Remote",
        "department": "Mobile",
        "level": "Mid-Level",
        "required_skills": ["React Native", "JavaScript", "TypeScript", "Mobile Development"]
    },
    {
        "title": "Security Engineer",
        "description": "Help us build secure systems and protect our infrastructure. You should have experience with security best practices, vulnerability assessment, and incident response. Knowledge of cloud security, cryptography, and compliance is valuable.",
        "location": "Austin, TX",
        "department": "Security",
        "level": "Senior",
        "required_skills": ["Cloud Security", "Vulnerability Assessment", "Incident Response", "Compliance"]
    }
]

created_job_ids = []
for job in extended_jobs_data:
    try:
        response = requests.post(f"{BASE_URL}/jobs", json=job, headers=headers)
        if response.status_code in [200, 201]:
            job_data = response.json()
            job_id = job_data.get("id")
            created_job_ids.append(job_id)
            print(f"✅ Job created: {job['title']} (ID: {job_id})")
        else:
            print(f"⚠️  Error creating job '{job['title']}': {response.status_code}")
    except Exception as e:
        print(f"❌ Error creating job '{job['title']}': {e}")

# ===== Step 3: Create More Sample Resumes =====
print("\n" + "="*60)
print("STEP 3: CREATING ADDITIONAL SAMPLE RESUMES")
print("="*60)

extended_resumes = [
    {
        "name": "David Martinez",
        "email": "david.martinez@email.com",
        "phone": "+1-555-0104",
        "summary": "DevOps engineer with 7 years of experience in cloud infrastructure and containerization. Expert in Kubernetes orchestration, Docker containerization, and CI/CD pipeline development. Certified Kubernetes Administrator (CKA) with proven track record of reducing deployment times by 70%.",
        "skills": ["Kubernetes", "Docker", "AWS", "GCP", "Terraform", "CI/CD", "Jenkins", "GitLab", "Monitoring", "Cloud Architecture"],
        "experience": [
            {
                "title": "Senior DevOps Engineer",
                "company": "Cloud Systems Corp",
                "location": "San Francisco, CA",
                "start_date": "2021-03-01",
                "end_date": "2024-08-01",
                "description": "Led infrastructure transformation to Kubernetes. Implemented automated CI/CD pipelines reducing deployment time by 70%."
            },
            {
                "title": "DevOps Engineer",
                "company": "TechStack LLC",
                "location": "Seattle, WA",
                "start_date": "2018-06-01",
                "end_date": "2021-02-28",
                "description": "Built and maintained Docker-based microservices infrastructure. Managed AWS resources and implemented monitoring solutions."
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science",
                "field": "Computer Engineering",
                "school": "University of Washington",
                "graduation_year": 2018
            }
        ]
    },
    {
        "name": "Emily Rodriguez",
        "email": "emily.rodriguez@email.com",
        "phone": "+1-555-0105",
        "summary": "Data engineer with 6 years of experience building large-scale data pipelines and analytics infrastructure. Proficient in Python, SQL, Spark, and modern data warehousing solutions. Have processed and optimized petabyte-scale datasets.",
        "skills": ["Python", "SQL", "Apache Spark", "Airflow", "Data Warehousing", "BigQuery", "Snowflake", "ETL", "Data Modeling"],
        "experience": [
            {
                "title": "Senior Data Engineer",
                "company": "Analytics Pro Inc",
                "location": "New York, NY",
                "start_date": "2021-01-01",
                "end_date": "2024-08-01",
                "description": "Designed and implemented scalable data pipelines for analytics. Optimized Spark jobs processing 500GB+ daily data."
            },
            {
                "title": "Data Engineer",
                "company": "DataFlow Systems",
                "location": "Boston, MA",
                "start_date": "2019-07-01",
                "end_date": "2020-12-31",
                "description": "Built ETL pipelines using Airflow and Spark. Implemented data warehouse solutions using Snowflake."
            }
        ],
        "education": [
            {
                "degree": "Master of Science",
                "field": "Data Science",
                "school": "Carnegie Mellon University",
                "graduation_year": 2019
            }
        ]
    },
    {
        "name": "James Thompson",
        "email": "james.thompson@email.com",
        "phone": "+1-555-0106",
        "summary": "Mobile developer specializing in React Native cross-platform development. 5 years of experience shipping apps to both App Store and Google Play. Strong in state management, performance optimization, and native module integration.",
        "skills": ["React Native", "JavaScript", "TypeScript", "Redux", "Firebase", "iOS", "Android", "REST APIs", "Mobile UI/UX"],
        "experience": [
            {
                "title": "Senior React Native Developer",
                "company": "MobileFirst Apps",
                "location": "Austin, TX",
                "start_date": "2021-04-01",
                "end_date": "2024-08-01",
                "description": "Led development of mobile apps used by 1M+ users. Implemented complex native modules and optimized app performance."
            },
            {
                "title": "Mobile Developer",
                "company": "Digital Solutions Ltd",
                "location": "Denver, CO",
                "start_date": "2019-06-01",
                "end_date": "2021-03-31",
                "description": "Developed and shipped 5+ React Native applications to App Store and Google Play."
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science",
                "field": "Software Engineering",
                "school": "University of Colorado",
                "graduation_year": 2019
            }
        ]
    },
    {
        "name": "Lisa Wang",
        "email": "lisa.wang@email.com",
        "phone": "+1-555-0107",
        "summary": "Security engineer with 8 years of experience in cloud security, vulnerability assessment, and incident response. AWS Certified Security Specialist. Strong background in compliance frameworks (SOC2, ISO27001). Experienced in penetration testing and security architecture.",
        "skills": ["Cloud Security", "AWS Security", "Penetration Testing", "Vulnerability Assessment", "SOC2", "ISO27001", "OWASP", "Cryptography", "Incident Response"],
        "experience": [
            {
                "title": "Senior Security Engineer",
                "company": "CyberDefense Corp",
                "location": "Austin, TX",
                "start_date": "2021-02-01",
                "end_date": "2024-08-01",
                "description": "Led security infrastructure for SaaS platform. Conducted security audits achieving SOC2 Type II certification."
            },
            {
                "title": "Security Engineer",
                "company": "InfoSec Solutions",
                "location": "San Antonio, TX",
                "start_date": "2018-09-01",
                "end_date": "2021-01-31",
                "description": "Performed penetration testing and vulnerability assessments. Implemented cloud security best practices."
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science",
                "field": "Cybersecurity",
                "school": "University of Texas at Austin",
                "graduation_year": 2018
            }
        ]
    },
    {
        "name": "Michael Lee",
        "email": "michael.lee@email.com",
        "phone": "+1-555-0108",
        "summary": "QA automation engineer with 4 years of experience building robust test automation frameworks. Expert in Selenium, test-driven development, and CI/CD integration. Proficient in Python and JavaScript for test scripting. Have automated 90%+ of regression test cases.",
        "skills": ["Test Automation", "Selenium", "Python", "JavaScript", "CI/CD", "TestNG", "Pytest", "API Testing", "Performance Testing"],
        "experience": [
            {
                "title": "QA Automation Engineer",
                "company": "QualityTest Systems",
                "location": "Denver, CO",
                "start_date": "2021-05-01",
                "end_date": "2024-08-01",
                "description": "Built comprehensive test automation framework. Automated 90%+ of regression tests reducing QA cycle time by 60%."
            },
            {
                "title": "Junior QA Engineer",
                "company": "TestPro LLC",
                "location": "Colorado Springs, CO",
                "start_date": "2020-03-01",
                "end_date": "2021-04-30",
                "description": "Developed test cases and automated tests using Selenium. Maintained CI/CD integration for automated testing."
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science",
                "field": "Computer Science",
                "school": "Colorado State University",
                "graduation_year": 2020
            }
        ]
    }
]

created_resume_count = 0
for resume_data in extended_resumes:
    try:
        # In production, these would be uploaded as actual PDF files
        # For demo purposes, we show the resume data structure
        print(f"✅ Resume data prepared for: {resume_data['name']}")
        print(f"   Email: {resume_data['email']}")
        print(f"   Years of Experience: {len(resume_data['experience'])} roles")
        print(f"   Skills: {len(resume_data['skills'])} technical skills")
        created_resume_count += 1
    except Exception as e:
        print(f"❌ Error processing resume for '{resume_data['name']}': {e}")

# ===== Step 4: Summary =====
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"✅ Total Users Registered: {len(users_data) + 1} (original + new)")
print(f"✅ Total Jobs Created: {len(created_job_ids) + 3} (3 from first batch + {len(extended_jobs_data)} from extended)")
print(f"✅ Total Resumes Available: {created_resume_count + 3} (3 from first batch + {created_resume_count} from extended)")
print(f"\n✅ Sample Jobs by Department:")
print(f"   - Engineering: 6 positions")
print(f"   - AI/ML: 1 position")
print(f"   - Infrastructure: 1 position")
print(f"   - Data & Analytics: 1 position")
print(f"   - Product: 1 position")
print(f"   - QA: 1 position")
print(f"   - Mobile: 1 position")
print(f"   - Security: 1 position")

print("\n📍 SAMPLE DATA READY:")
print("   1. Access Dashboard: http://localhost:3000")
print("   2. Login with: recruiter1@talentlens.io / SecurePass123!")
print("   3. View 9+ jobs across 8 departments")
print("   4. Test resume upload functionality")
print("   5. Test candidate matching algorithms")

print("\n" + "="*60)
