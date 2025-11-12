"""
Version information for Lily Cafe POS System
"""

__version__ = "0.1.0"
__version_info__ = (0, 1, 0)

# Version history
VERSION_HISTORY = {
    "0.1.0": "2025-11-11 - Initial MVP release with core POS functionality",
    # "0.2.0": "TBD - Inventory management and cash counter",
}

def get_version() -> str:
    """Return the current version string."""
    return __version__

def get_version_info() -> dict:
    """Return detailed version information."""
    return {
        "version": __version__,
        "version_tuple": __version_info__,
        "release_date": VERSION_HISTORY.get(__version__, "Unknown"),
    }
