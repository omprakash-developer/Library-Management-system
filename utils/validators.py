"""
Validation Utilities Module
Provides reusable input validation and sanitization functions for the Library Management System.
"""


def validate_string(value, min_length=1):
    """
    Validate that a given value is a non-empty string of at least min_length characters.

    Args:
        value (str): The string to validate.
        min_length (int): Minimum length required (default 1).

    Returns:
        str: The stripped string if valid, or None if invalid.
    """
    if value is None:
        return None
    cleaned = str(value).strip()
    if len(cleaned) < min_length:
        return None
    return cleaned


def validate_positive_integer(value, allow_zero=False):
    """
    Validate that a value is a valid integer, optionally allowing zero.

    Args:
        value: The value to validate (string or int).
        allow_zero (bool): Whether 0 is considered valid (default False).

    Returns:
        int: The parsed integer if valid, or None if invalid.
    """
    try:
        val = int(value)
        if allow_zero and val >= 0:
            return val
        elif not allow_zero and val > 0:
            return val
        return None
    except (ValueError, TypeError):
        return None


def get_non_empty_input(prompt, field_name="Field", default=None):
    """
    Prompt the user repeatedly until a non-empty string is entered.
    If default is provided and user presses Enter, default is returned.

    Args:
        prompt (str): Prompt text to display.
        field_name (str): Name of the field for error messages.
        default (str, optional): Default value if user enters blank.

    Returns:
        str: The sanitized non-empty string.
    """
    while True:
        user_input = input(prompt).strip()
        if not user_input and default is not None:
            return default
        if user_input:
            return user_input
        print(f"[!] {field_name} cannot be empty. Please try again.")


def get_integer_input(prompt, field_name="Value", min_value=0, allow_blank=False, default=None):
    """
    Prompt the user repeatedly until a valid integer meeting the minimum value is entered.

    Args:
        prompt (str): Prompt text to display.
        field_name (str): Name of the field for error messages.
        min_value (int, optional): Minimum allowed value (inclusive).
        allow_blank (bool): If True, allows user to press Enter to keep default.
        default (int, optional): Default value returned when blank is allowed.

    Returns:
        int: The parsed integer.
    """
    while True:
        user_input = input(prompt).strip()
        if allow_blank and user_input == "" and default is not None:
            return default
        try:
            val = int(user_input)
            if min_value is not None and val < min_value:
                print(f"[!] {field_name} must be at least {min_value}. Please try again.")
                continue
            return val
        except ValueError:
            print(f"[!] Invalid input! Please enter a valid whole number for {field_name}.")


def get_confirmation(prompt="Are you sure? (yes/no): "):
    """
    Prompt the user for a yes/no confirmation.

    Args:
        prompt (str): Prompt text.

    Returns:
        bool: True if confirmed ('yes' or 'y'), False otherwise.
    """
    user_input = input(prompt).strip().lower()
    return user_input in ("yes", "y")

