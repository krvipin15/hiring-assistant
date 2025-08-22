#!/usr/bin/env python3

"""
Utility functions for validating and sanitizing user input.
"""

import html
import requests
import phonenumbers
from email_validator import EmailNotValidError,validate_email as ev_validate

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


def sanitize_input(text: str) -> str:
    # Basic HTML escaping to prevent XSS
    return html.escape(text.strip()) if text else ""


if __name__ == "__main__":
    print(validate_email("vipinkr3000@gmail.com"))
    print(validate_phone("+91 8766312199"))
    print(validate_location("Meerut, India"))
    print(sanitize_input("<script>alert('xss')</script>"))
