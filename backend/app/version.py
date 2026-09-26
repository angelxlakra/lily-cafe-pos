"""
Version information for Lily Cafe POS System
"""

import os

__version__ = "0.2.0"
__version_info__ = (0, 2, 0)


# Version history
VERSION_HISTORY = {
    "0.1.0": "2025-11-11 - Initial MVP release with core POS functionality",
    "0.1.1": "2025-01-12 - Dark mode theme toggle",
    "0.1.2": "2025-12-27 - Partial serving & payment editing",
    "0.2.0": "2025-12-30 - Inventory management & cash counter system",
}

def get_version() -> str:
    """Return the current version string."""
    return __version__

def get_build_info() -> dict:
    """What is actually running, as opposed to what the version string claims.

    `__version__` is hardcoded, so it reads the same for a current image and a
    stale one — in September 2026 a deploy shipped an image with no /counts
    routes while still reporting 0.2.0, and it took four days to notice. The
    commit is stamped into the image at build time (see backend/Dockerfile);
    it reads "unknown" for a local run, or a deploy that forgot --build-arg.
    The image ref is set by Fly and changes on every deploy regardless.
    """
    return {
        "commit": os.getenv("GIT_SHA", "unknown"),
        "image": os.getenv("FLY_IMAGE_REF", "").rsplit("/", 1)[-1] or "local",
    }


def get_version_info() -> dict:
    """Return detailed version information."""
    return {
        "version": __version__,
        "version_tuple": __version_info__,
        "release_date": VERSION_HISTORY.get(__version__, "Unknown"),
        **get_build_info(),
    }
