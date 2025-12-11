"""API v1 main router.

Aggregates all v1 API routers into a single router for inclusion in the app.
"""

from fastapi import APIRouter

from bookbytes.api.v1.processing import router as processing_router
from bookbytes.api.v1.search import router as search_router

router = APIRouter()

# Include sub-routers
router.include_router(search_router, prefix="/books", tags=["Books"])
router.include_router(processing_router, prefix="/books", tags=["Processing"])

# Future routers:
# router.include_router(users_router, prefix="/users", tags=["Users"])
