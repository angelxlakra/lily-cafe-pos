"""
Configuration management for Lily Cafe POS System.
Loads environment variables for secrets and bootstrap values only.

Non-secret settings (restaurant info, GST rate, etc.) are stored in the
database and accessed via app.core.settings_store.
"""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Secrets and bootstrap settings loaded from environment variables."""

    # App Bootstrap
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

    # Admin Credentials
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "changeme123")

    # Owner Credentials
    OWNER_USERNAME: str = os.getenv("OWNER_USERNAME", "owner")
    OWNER_PASSWORD: str = os.getenv("OWNER_PASSWORD", "owner123")

    # Owner Password Hash (for cash counter verification)
    OWNER_PASSWORD_HASH: str = os.getenv(
        "OWNER_PASSWORD_HASH",
        "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
    )

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./restaurant.db")

    # CORS Origins (comma-separated) — needed at startup before DB is accessible
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174",
    ).split(",")

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"

    # Thesys C1 Configuration
    THESYS_API_KEY: str = os.getenv("THESYS_API_KEY", "")

    # Print Agent API Key (shared secret between backend and agent.py)
    PRINT_AGENT_API_KEY: str = os.getenv("PRINT_AGENT_API_KEY", "change-me-in-production")

    # Email / SMTP Password (secret — stays in env var)
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

    # Thermal Printer Configuration (local hardware — not stored in DB)
    PRINTER_ENABLED: bool = os.getenv("PRINTER_ENABLED", "false").lower() == "true"
    PRINTER_TYPE: str = os.getenv("PRINTER_TYPE", "")
    PRINTER_NAME: str = os.getenv("PRINTER_NAME", "")
    PRINTER_VENDOR_ID: str = os.getenv("PRINTER_VENDOR_ID", "")
    PRINTER_PRODUCT_ID: str = os.getenv("PRINTER_PRODUCT_ID", "")
    PRINTER_PORT: str = os.getenv("PRINTER_PORT", "")
    PRINTER_BAUDRATE: int = int(os.getenv("PRINTER_BAUDRATE", "9600"))

    # Restaurant logo path (local filesystem — not applicable in cloud deployment)
    RESTAURANT_LOGO_PATH: str = os.getenv("RESTAURANT_LOGO_PATH", "")


# Create a singleton instance
settings = Settings()
