"""
Configuration management for Lily Cafe POS System.
Loads environment variables and provides application settings.
"""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # App Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    TOKEN_EXPIRY_HOURS: int = int(os.getenv("TOKEN_EXPIRY_HOURS", "24"))
    MAX_TABLES: int = int(os.getenv("MAX_TABLES", "15"))
    GST_RATE: float = float(os.getenv("GST_RATE", "18"))

    # Restaurant Details
    RESTAURANT_NAME: str = os.getenv("RESTAURANT_NAME", "Lily Cafe by Mary's Kitchen")
    RESTAURANT_ADDRESS_LINE1: str = os.getenv(
        "RESTAURANT_ADDRESS_LINE1", "Shop 123, Main Street"
    )
    RESTAURANT_ADDRESS_LINE2: str = os.getenv(
        "RESTAURANT_ADDRESS_LINE2", "City, State - 123456"
    )
    RESTAURANT_PHONE: str = os.getenv("RESTAURANT_PHONE", "+91-1234567890")
    RESTAURANT_EMAIL: str = os.getenv("RESTAURANT_EMAIL", "info@lilycafe.com")
    RESTAURANT_GSTIN: str = os.getenv("RESTAURANT_GSTIN", "29ABCDE1234F1Z5")
    RESTAURANT_LOGO_PATH: str = os.getenv("RESTAURANT_LOGO_PATH", "")

    # Admin Credentials
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "changeme123")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./restaurant.db")

    # CORS Origins (comma-separated)
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"


# Create a singleton instance
settings = Settings()
