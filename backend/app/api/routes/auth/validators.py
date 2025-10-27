import re
from typing import Optional

EMAIL_PATTERN = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)


def normalize_email(raw_email: Optional[str]) -> str:
    if raw_email is None:
        raise ValueError("Email is required.")

    normalized = raw_email.strip().lower()

    if not normalized or not EMAIL_PATTERN.fullmatch(normalized):
        raise ValueError("Invalid email format.")

    return normalized


__all__ = ["normalize_email"]
