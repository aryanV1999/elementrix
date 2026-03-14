from fastapi import APIRouter

from . import diet_generator

router = APIRouter()
router.include_router(diet_generator.router, tags=["Diet Generator"])
