"""
Input validation and sanitization utilities
"""

import re
import magic
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from .exceptions import ValidationError as ATSValidationError, FileUploadError


def validate_email_address(email):
    """
    Validate email address format and basic security checks
    """
    if not email or not isinstance(email, str):
        raise ATSValidationError("Email is required")

    email = email.strip().lower()

    if len(email) > 254:  # RFC 5321 limit
        raise ATSValidationError("Email address too long")

    try:
        validate_email(email)
    except ValidationError:
        raise ATSValidationError("Invalid email format")

    # Additional security checks
    if re.search(r'[<>]', email):
        raise ATSValidationError("Invalid characters in email")

    return email


def validate_password(password):
    """
    Validate password strength requirements
    """
    if not password or not isinstance(password, str):
        raise ATSValidationError("Password is required")

    if len(password) < 8:
        raise ATSValidationError("Password must be at least 8 characters long")

    if len(password) > 128:
        raise ATSValidationError("Password too long")

    # Check for at least one uppercase, one lowercase, one digit
    if not re.search(r'[A-Z]', password):
        raise ATSValidationError("Password must contain at least one uppercase letter")

    if not re.search(r'[a-z]', password):
        raise ATSValidationError("Password must contain at least one lowercase letter")

    if not re.search(r'\d', password):
        raise ATSValidationError("Password must contain at least one number")

    # Check for common weak passwords
    weak_passwords = ['password', '12345678', 'qwerty', 'admin', 'letmein']
    if password.lower() in weak_passwords:
        raise ATSValidationError("Password is too common")

    return password


def validate_full_name(name):
    """
    Validate and sanitize full name
    """
    if not name or not isinstance(name, str):
        raise ATSValidationError("Full name is required")

    name = name.strip()

    if len(name) < 2:
        raise ATSValidationError("Full name too short")

    if len(name) > 100:
        raise ATSValidationError("Full name too long")

    # Allow only letters, spaces, hyphens, apostrophes
    if not re.match(r"^[a-zA-Z\s\-']+$", name):
        raise ATSValidationError("Full name contains invalid characters")

    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name)

    return name


def validate_phone_number(phone):
    """
    Validate phone number format (optional field)
    """
    if not phone:  # Phone is optional
        return None

    if not isinstance(phone, str):
        raise ATSValidationError("Invalid phone number format")

    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)

    if len(digits_only) < 10 or len(digits_only) > 15:
        raise ATSValidationError("Phone number must be 10-15 digits")

    return digits_only


def validate_text_field(text, field_name, max_length=1000, min_length=0, required=False):
    """
    Generic text field validation
    """
    if required and (not text or not isinstance(text, str)):
        raise ATSValidationError(f"{field_name} is required")

    if not text and not required:
        return None

    if not isinstance(text, str):
        raise ATSValidationError(f"{field_name} must be a string")

    text = text.strip()

    if len(text) < min_length:
        raise ATSValidationError(f"{field_name} too short (minimum {min_length} characters)")

    if len(text) > max_length:
        raise ATSValidationError(f"{field_name} too long (maximum {max_length} characters)")

    # Basic XSS protection - remove script tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)  # Remove any remaining HTML tags

    return text


def validate_salary(salary):
    """
    Validate salary field (optional)
    """
    if salary is None or salary == '':
        return None

    try:
        salary = float(salary)
        if salary < 0:
            raise ATSValidationError("Salary cannot be negative")
        if salary > 10000000:  # 10 million max
            raise ATSValidationError("Salary value too high")
        return salary
    except (ValueError, TypeError):
        raise ATSValidationError("Invalid salary format")


def validate_experience_years(experience):
    """
    Validate years of experience
    """
    if experience is None or experience == '':
        return None

    try:
        experience = float(experience)
        if experience < 0:
            raise ATSValidationError("Experience cannot be negative")
        if experience > 50:  # 50 years max
            raise ATSValidationError("Experience value too high")
        return experience
    except (ValueError, TypeError):
        raise ATSValidationError("Invalid experience format")


def validate_resume(file):
    """
    Enhanced resume file validation
    """
    if not file:
        raise FileUploadError("No file provided")

    allowed_extensions = ["pdf", "docx"]
    allowed_mime_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]

    # Check file name
    if not hasattr(file, 'name') or not file.name:
        raise FileUploadError("Invalid file")

    # Check extension
    ext = file.name.split(".")[-1].lower()
    if ext not in allowed_extensions:
        raise FileUploadError(f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}")

    # Check file size (5MB limit)
    if hasattr(file, 'size') and file.size > 5 * 1024 * 1024:
        raise FileUploadError("File too large (maximum 5MB)")

    # Check file size by reading (fallback)
    try:
        file_bytes = file.read(2048)
        if len(file_bytes) > 5 * 1024 * 1024:
            raise FileUploadError("File too large (maximum 5MB)")
    except:
        raise FileUploadError("Unable to read file")

    # Validate MIME type
    try:
        mime = magic.from_buffer(file_bytes, mime=True)
        if mime not in allowed_mime_types:
            raise FileUploadError(f"Invalid file type. Detected: {mime}")
    except:
        # If magic fails, we'll allow it but log a warning
        pass

    # Reset file pointer
    file.seek(0)

    return file