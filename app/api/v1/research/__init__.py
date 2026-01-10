from fastapi import APIRouter

from .index import router

research_router = APIRouter()
research_router.include_router(router, tags=["研究模块"])

__all__ = ["research_router"]
