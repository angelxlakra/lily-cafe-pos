"""
API v1 Router - Combines all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    categories,
    menu,
    orders,
    admin,
    config,
    inventory_categories
)

api_router = APIRouter()

# Include all endpoint routers with their prefixes and tags
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(menu.router, prefix="/menu", tags=["menu"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(config.router, prefix="/config", tags=["config"])
api_router.include_router(
    inventory_categories.router,
    prefix="/inventory-categories",
    tags=["inventory-categories"]
)
