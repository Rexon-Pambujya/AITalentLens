from fastapi import APIRouter

from app.api.v1 import auth, candidates, health, jobs, matching, rankings, resumes, search

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(jobs.router)
api_router.include_router(resumes.router)
api_router.include_router(candidates.router)
api_router.include_router(matching.router)
api_router.include_router(rankings.router)
api_router.include_router(search.router)

# Registered in later phases:
# api_router.include_router(analytics.router)
# api_router.include_router(notes.router)  # note endpoints already live under candidates.router
# api_router.include_router(matching.router)
# api_router.include_router(rankings.router)
# api_router.include_router(search.router)
# api_router.include_router(analytics.router)
# api_router.include_router(notes.router)
