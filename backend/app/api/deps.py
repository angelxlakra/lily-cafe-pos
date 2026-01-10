"""
Shared dependencies for API endpoints.
"""

from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user, get_current_owner

# Re-export for convenience
__all__ = ["get_db", "get_current_user", "get_current_owner"]
