"""
Version information for Lily Cafe POS System
"""

__version__ = "0.1.3"
__version_info__ = (0, 1, 3)

# Version history
VERSION_HISTORY = {
    "0.1.0": "2025-11-11 - Initial MVP release with core POS functionality",
    "0.1.1": "2025-01-12 - Dark mode theme toggle",
    "0.1.2": "2025-12-27 - Partial serving & payment editing",
    "0.1.3": "2025-12-30 - Edit served quantity via status badge click",
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
