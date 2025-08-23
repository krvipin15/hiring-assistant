#!/usr/bin/env python3
"""
This script provides functions to validate the format and deliverability of email addresses,
the validity of international phone numbers, and the existence of geographic locations using
the OpenStreetMap Nominatim API.

Functions:
    - validate_email(email: str) -> bool: Checks if an email address is valid and deliverable.
    - validate_phone(phone: str) -> bool: Checks if a phone number is valid according to international standards.
    - validate_location(location: str) -> bool: Checks if a location exists using geocoding.
"""

import requests
import phonenumbers
from email_validator import EmailNotValidError, validate_email as ev_validate

def validate_email(email: str) -> bool:
    """Validate email address format"""
    try:
        valid = ev_validate(email, check_deliverability=True)
        return True
    except EmailNotValidError:
        return False


def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    try:
        parsed = phonenumbers.parse(phone, None)
        return phonenumbers.is_valid_number(parsed)
    except phonenumbers.NumberParseException:
        return False


def validate_location(location: str) -> bool:
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": location, "format": "json", "limit": 1}
    resp = requests.get(url, params=params, headers={"User-Agent": "hiring-assistant"})
    data = resp.json()
    return len(data) > 0


# Example usage
if __name__ == "__main__":
    print(validate_email("abc@xyz.com"))          # False
    print(validate_phone("+91 2451253377"))       # False
    print(validate_location("New Delhi, India"))  # True
