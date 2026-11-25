"""Turn engine values into Python dates: SQLite returns text, MySQL returns date objects."""

from datetime import date, datetime


def to_date(value):
    if value is None or isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value)[:10])


def to_datetime(value):
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def to_db_datetime(value):
    """Same text format for both engines: 'YYYY-MM-DD HH:MM:SS'."""
    return None if value is None else value.strftime("%Y-%m-%d %H:%M:%S")
