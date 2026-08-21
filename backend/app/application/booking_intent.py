"""Deterministic recognition of explicit appointment-booking requests."""

from enum import Enum
import re


class BookingIntent(str, Enum):
    NONE = "NONE"
    BOOKING_REQUEST = "BOOKING_REQUEST"


_BOOKING_VERB = r"(?:book|schedule|make|arrange)"
_APPOINTMENT = r"(?:an?|the|my|this|that)?\s*appointment(?:s)?"
_EXPLICIT_REQUEST = re.compile(
    rf"\b{_BOOKING_VERB}\b(?:\s+\w+){{0,5}}\s+{_APPOINTMENT}\b"
)
_REQUEST_TO_BOOK = re.compile(
    rf"\b(?:want|need|would\s+like|like|trying)\s+to\s+{_BOOKING_VERB}\b"
)
_NEGATED = re.compile(
    rf"\b(?:do\s+not|don't|dont|not|never|no\s+longer|wouldn't|would\s+not)"
    rf"(?:\s+\w+){{0,4}}\s+{_BOOKING_VERB}\b"
)
_UNCERTAIN_OR_INFORMATIONAL = re.compile(
    r"\b(?:what\s+if|if\s+i|how\s+does|how\s+do|what\s+happens|information"
    r"\s+about|tell\s+me\s+about)\b"
)
_EXCLUDED_VERB = re.compile(r"\b(?:cancel|cancell?ation|reschedule|re-?schedule)\b")


def classify_booking_intent(message: str) -> BookingIntent:
    """Return booking intent only for a clear, affirmative appointment request."""

    if not isinstance(message, str):
        return BookingIntent.NONE

    normalized = re.sub(r"\s+", " ", message.casefold()).strip()
    normalized = re.sub(r"[^\w\s'-]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if not normalized or _EXCLUDED_VERB.search(normalized):
        return BookingIntent.NONE
    if _NEGATED.search(normalized) or _UNCERTAIN_OR_INFORMATIONAL.search(normalized):
        return BookingIntent.NONE

    has_appointment = re.search(r"\bappointments?\b", normalized)
    if not has_appointment:
        return BookingIntent.NONE
    if _EXPLICIT_REQUEST.search(normalized):
        return BookingIntent.BOOKING_REQUEST
    if _REQUEST_TO_BOOK.search(normalized):
        return BookingIntent.BOOKING_REQUEST
    return BookingIntent.NONE
