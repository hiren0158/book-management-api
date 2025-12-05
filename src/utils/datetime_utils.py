"""
Utility functions for datetime operations.
Provides timezone-naive UTC datetime for compatibility with existing models.
"""

from datetime import datetime, timezone


def utcnow_naive() -> datetime:
    """
    Get current UTC time as timezone-naive datetime.

    This replaces datetime.utcnow() which is deprecated.
    Returns timezone-naive datetime for compatibility with existing models.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
