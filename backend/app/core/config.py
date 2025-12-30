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
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Kolkata")  # IST timezone

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
    RESTAURANT_FSSAI: str = os.getenv("RESTAURANT_FSSAI", "29ABCDE1234F1Z5")
    RESTAURANT_LOGO_PATH: str = os.getenv("RESTAURANT_LOGO_PATH", "")

    # Receipt Configuration
    RECEIPT_PAPER_SIZE: str = os.getenv("RECEIPT_PAPER_SIZE", "80mm")  # "58mm" or "80mm"
    GOOGLE_REVIEW_URL: str = os.getenv(
        "GOOGLE_REVIEW_URL", "https://g.page/r/your-business-review"
    )
    FEEDBACK_FORM_URL: str = os.getenv(
        "FEEDBACK_FORM_URL", "https://forms.gle/your-feedback-form"
    )

    # Thermal Printer Configuration
    PRINTER_ENABLED: bool = os.getenv("PRINTER_ENABLED", "false").lower() == "true"
    PRINTER_TYPE: str = os.getenv("PRINTER_TYPE", "")  # "win32", "usb", "serial"
    PRINTER_NAME: str = os.getenv("PRINTER_NAME", "")  # Windows printer name
    PRINTER_VENDOR_ID: str = os.getenv("PRINTER_VENDOR_ID", "")  # USB vendor ID (hex)
    PRINTER_PRODUCT_ID: str = os.getenv("PRINTER_PRODUCT_ID", "")  # USB product ID (hex)
    PRINTER_PORT: str = os.getenv("PRINTER_PORT", "")  # Serial port (e.g., COM3)
    PRINTER_BAUDRATE: int = int(os.getenv("PRINTER_BAUDRATE", "9600"))  # Serial baudrate

    # Admin Credentials
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "changeme123")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./restaurant.db")

    # CORS Origins (comma-separated)
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"
    ).split(",")

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"


# Create a singleton instance
settings = Settings()
