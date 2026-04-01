from django.contrib.auth.models import User
from candidates.models import Candidate
from authentication.models import RecruiterProfile, UserProfile, AuditLog
from core.exceptions import ValidationError, ConflictError
from core.validators import validate_email_address, validate_experience_years, validate_full_name


def _split_full_name(full_name):
    validated_name = validate_full_name(full_name)
    parts = validated_name.split()
    first_name = parts[0]
    last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
    return validated_name, first_name, last_name


def create_candidate(data):
    """
    Create a new candidate user and profile with validation
    """
    try:
        # Validate email (should already be validated in view, but double-check)
        email = validate_email_address(data['email'])

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            raise ConflictError("Email already exists")

        full_name, first_name, last_name = _split_full_name(data['full_name'])

        user = User.objects.create_user(
            username=email,
            email=email,
            password=data['password'],
            first_name=first_name,
            last_name=last_name,
        )

        UserProfile.objects.create(user=user, role=UserProfile.Role.CANDIDATE)

        experience_years = validate_experience_years(data.get('experience'))

        Candidate.objects.create(
            user=user,
            full_name=full_name,
            email=email,
            phone=data.get('phone', ''),
            summary=data.get('summary', ''),
            total_experience_years=experience_years
        )

        AuditLog.objects.create(
            user=user,
            action="Candidate account created"
        )

        return user

    except KeyError as e:
        raise ValidationError(f"Missing required field: {e}")
    except Exception as e:
        if isinstance(e, (ValidationError, ConflictError)):
            raise
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating candidate: {str(e)}", exc_info=True)
        raise ValidationError("Failed to create candidate account")


def create_recruiter(data, admin_user=None):
    email = validate_email_address(data.get('email'))
    full_name_input = data.get('full_name')
    if not full_name_input:
        first_name_input = (data.get('first_name') or '').strip()
        last_name_input = (data.get('last_name') or '').strip()
        full_name_input = ' '.join(part for part in [first_name_input, last_name_input] if part)
    full_name, first_name, last_name = _split_full_name(full_name_input)

    if User.objects.filter(email=email).exists():
        raise ConflictError("Email already exists")

    user = User.objects.create_user(
        username=email,
        email=email,
        password=data['password'],
        first_name=first_name,
        last_name=last_name,
    )

    UserProfile.objects.create(user=user, role=UserProfile.Role.RECRUITER)

    RecruiterProfile.objects.create(
        user=user,
        company_name=data.get('company_name', '')
    )

    # Only create audit log if admin_user is provided
    if admin_user:
        AuditLog.objects.create(
            user=admin_user,
            action=f"Created recruiter {full_name} ({user.email})"
        )

    return user


def deactivate_recruiter(user, admin_user):
    user.is_active = False
    user.save()

    AuditLog.objects.create(
        user=admin_user,
        action=f"Deactivated recruiter {user.email}"
    )
