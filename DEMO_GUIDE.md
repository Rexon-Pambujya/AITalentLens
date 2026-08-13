# TalentLens AI - Complete Setup & Walkthrough Guide

## 🎯 What We Accomplished

### ✅ Environment Setup

- Python virtual environment created (`venv/`)
- All dependencies installed (FastAPI, PostgreSQL, Redis, Celery, etc.)
- Docker Compose running with all services:
  - PostgreSQL 16 + pgvector
  - Redis (caching & message broker)
  - MinIO (S3 storage)
  - Backend API (port 8000)
  - Celery worker
  - Frontend (port 3000)

### ✅ Demo Data Created

#### 🔐 New User Account

```
Email: testuser@example.com
Password: TestPassword123!
Name: John Doe
Organization: Tech Innovations Inc
Role: ADMIN
```

#### 💼 3 Sample Jobs

1. **Senior Python Developer** (San Francisco)
   - Required: Python, FastAPI, PostgreSQL, Docker, AWS
   - Level: Senior
   - Experience: 5+ years

2. **AI/ML Engineer** (New York)
   - Required: Python, PyTorch, TensorFlow, LLMs, Vector Databases
   - Level: Senior

3. **Full Stack Developer** (Remote)
   - Required: React, TypeScript, Python, PostgreSQL, Docker
   - Level: Mid-Level

#### 👥 3 Sample Resumes (Created via Backend)

1. **Alice Johnson**
   - 6 years senior backend engineering experience
   - Expert: Python, FastAPI, PostgreSQL, Docker, AWS, Redis
   - Recent: Senior Backend Engineer @ Tech Startup A (2021-2023)
   - Education: BS Computer Science, UC Berkeley (2019)

2. **Bob Chen**
   - 5 years AI/ML research experience
   - Expert: Python, PyTorch, TensorFlow, LLMs, Vector Databases, LangChain
   - Recent: AI Research Engineer @ AI Labs Inc (2022-2024)
   - Education: MS Machine Learning, MIT (2019)

3. **Carol Davis**
   - 4 years full-stack development experience
   - Expert: React, TypeScript, Python, PostgreSQL, Docker, Next.js
   - Recent: Full Stack Developer @ StartupXYZ (2022-2024)
   - Education: BS Information Technology, UT Austin (2020)

---

## 🔄 User Flow Tested

### 1. **Create Account** ✅

```
POST /api/v1/auth/register
{
  "email": "testuser@example.com",
  "password": "TestPassword123!",
  "name": "John Doe",
  "organization_name": "Tech Innovations Inc"
}
Returns: JWT access_token
```

### 2. **Logout** ✅

- Click "Log out" button in UI (top-right corner)
- Redirects to login page

### 3. **Sign In** ✅

```
POST /api/v1/auth/login
{
  "email": "testuser@example.com",
  "password": "TestPassword123!"
}
Returns: JWT access_token
```

- UI redirects to dashboard

### 4. **Create Jobs** ✅

```
POST /api/v1/jobs
{
  "title": "Senior Python Developer",
  "description": "...",
  "location": "San Francisco, CA",
  "department": "Engineering",
  "level": "Senior",
  "required_skills": ["Python", "FastAPI", ...]
}
Returns: Job ID
```

---

## 🚀 Available API Endpoints

### Authentication

```
POST   /api/v1/auth/register     - Create new account
POST   /api/v1/auth/login        - Login
GET    /api/v1/auth/me           - Get current user
```

### Jobs

```
GET    /api/v1/jobs              - List all jobs
GET    /api/v1/jobs/{id}         - Get job details
POST   /api/v1/jobs              - Create new job
PUT    /api/v1/jobs/{id}         - Update job
DELETE /api/v1/jobs/{id}         - Delete job
```

### Resumes (for matching)

```
POST   /api/v1/resumes/upload    - Upload resume (PDF/DOCX)
GET    /api/v1/resumes           - List resumes
GET    /api/v1/resumes/{id}      - Get resume details
```

### Search & Matching

```
POST   /api/v1/search/candidates - Semantic search by job description
POST   /api/v1/matching/match    - Match candidate to job
GET    /api/v1/matching/matches  - List all matches
```

---

## 🌐 Access URLs

| Service                | URL                         | Credentials                             |
| ---------------------- | --------------------------- | --------------------------------------- |
| **Frontend Dashboard** | http://localhost:3000       | testuser@example.com / TestPassword123! |
| **API Swagger Docs**   | http://localhost:8000/docs  | None (public)                           |
| **API ReDoc**          | http://localhost:8000/redoc | None (public)                           |
| **MinIO Console**      | http://localhost:9001       | talentlens / talentlens123              |
| **PostgreSQL**         | localhost:5432              | talentlens / talentlens                 |
| **Redis**              | localhost:6379              | None (no auth)                          |

---

## 📝 Known Issues & Future Improvements

### Resume Upload in UI

**Current Status:** UI missing upload button

- Backend API is fully functional: `POST /api/v1/resumes/upload`
- Sample resumes can be uploaded via API
- Future: Frontend UI needs a "Upload Resume" button on job pages

### How to Upload Resumes via API

```bash
# Using curl with a real PDF file
curl -X POST http://localhost:8000/api/v1/resumes/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@path/to/resume.pdf" \
  -F "job_id=<job_id>"
```

### Next Steps for Full Functionality

1. Add resume upload UI component (estimated: 2-3 hours)
2. Implement resume parsing & extraction (currently in backend)
3. Add candidate matching UI & visualization
4. Implement analytics dashboard
5. Add more job creation workflows

---

## 🔧 Running the Project

### Start Services

```bash
# From workspace root
docker compose -f infra/docker-compose.yml up
```

### Stop Services

```bash
# Ctrl+C in the terminal, or:
docker compose -f infra/docker-compose.yml down
```

### Access Frontend

```
http://localhost:3000
```

### Access API Docs

```
http://localhost:8000/docs
```

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (Next.js)                    │
│              http://localhost:3000                      │
└──────────────────────┬──────────────────────────────────┘
                       │ (REST API calls)
┌──────────────────────▼──────────────────────────────────┐
│           Backend API (FastAPI + Uvicorn)              │
│              http://localhost:8000                      │
│  ┌─────────────┬─────────────┬──────────────────────┐   │
│  │   Auth      │    Jobs     │   Resumes/Search    │   │
│  │ Endpoints   │ Endpoints   │   Endpoints         │   │
│  └─────────────┴─────────────┴──────────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
    ┌───▼────┐    ┌───▼────┐    ┌───▼────┐
    │Postgres│    │ Redis  │    │ MinIO  │
    │+ pgvec │    │ Celery │    │ S3     │
    └────────┘    └────────┘    └────────┘
```

---

## 🎓 Learning Resources

### API Documentation (Interactive)

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Try any endpoint directly in the browser

### Code Structure

```
backend/
  app/
    api/          - API route definitions
    models/       - SQLAlchemy database models
    schemas/      - Pydantic request/response schemas
    services/     - Business logic (matching, search, etc.)
    core/         - Config, logging, auth, exceptions
    db/           - Database sessions
    workers/      - Celery async tasks
```

---

## ✨ Testing Checklist

- [x] User registration
- [x] User login/logout
- [x] Create jobs
- [x] Job listing & details
- [ ] Resume upload (UI missing, backend ready)
- [ ] Candidate search
- [ ] Candidate matching
- [ ] Scoring & explanations
- [ ] Analytics dashboard

---

**Created:** 2026-08-13  
**Demo User:** testuser@example.com  
**Status:** ✅ Ready for testing & development
