import pytest

from app.application.booking_intent import BookingIntent, classify_booking_intent


@pytest.mark.parametrize(
    "message",
    [
        "book an appointment",
        "Can you schedule an appointment for me?",
        "I want to make an appointment.",
        "Please arrange my appointment!",
        "  SCHEDULE   THE   APPOINTMENT  ",
        "I'd like to book an appointment",
    ],
)
def test_explicit_booking_requests_are_recognized(message):
    assert classify_booking_intent(message) is BookingIntent.BOOKING_REQUEST


@pytest.mark.parametrize(
    "message",
    [
        "cancel my appointment",
        "reschedule my appointment",
        "I don't want to book an appointment",
        "How does appointment booking work?",
        "What happens during an appointment?",
        "What if I wanted to book an appointment?",
        "Book a table for two",
        "Can you schedule a meeting?",
        "appointment",
        "book",
        "   ",
        "",
    ],
)
def test_non_booking_messages_are_not_recognized(message):
    assert classify_booking_intent(message) is BookingIntent.NONE


def test_classifier_is_pure_and_does_not_call_a_provider():
    assert classify_booking_intent("BOOK an appointment!!!") == BookingIntent.BOOKING_REQUEST
    assert classify_booking_intent("BOOK an appointment!!!") == BookingIntent.BOOKING_REQUEST
