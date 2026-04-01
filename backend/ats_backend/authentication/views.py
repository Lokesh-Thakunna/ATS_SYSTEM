from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import IsAdmin, get_user_role
from .services import create_candidate, create_recruiter, deactivate_recruiter
from .models import RecruiterProfile
from core.validators import (
    validate_email_address, validate_password, validate_full_name,
    validate_phone_number, validate_text_field
)
from core.exceptions import ValidationError, AuthenticationError


def _build_user_payload(user):
    full_name = user.get_full_name().strip()
    role = get_user_role(user) or 'candidate'

    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": full_name or user.email,
        "role": role,
    }


def _resolve_login_user(identifier):
    if identifier is None:
        return None

    raw_identifier = str(identifier).strip()
    if not raw_identifier:
        return None

    queryset = User.objects.all()

    if raw_identifier.isdigit():
        return queryset.filter(id=int(raw_identifier)).first()

    normalized_email = raw_identifier.lower()
    return queryset.filter(
        Q(email__iexact=normalized_email) | Q(username__iexact=raw_identifier)
    ).first()


@api_view(['POST'])
def register_candidate(request):
    try:
        data = request.data

        # Validate required fields
        email = validate_email_address(data.get('email'))
        password = validate_password(data.get('password'))
        full_name = validate_full_name(data.get('full_name'))

        # Validate optional fields
        phone = validate_phone_number(data.get('phone'))
        summary = validate_text_field(data.get('summary'), 'Summary', max_length=500, required=False)
        experience = data.get('experience')

        # Prepare validated data
        validated_data = {
            'email': email,
            'password': password,
            'full_name': full_name,
            'phone': phone,
            'summary': summary,
            'experience': experience
        }

        user = create_candidate(validated_data)
        return Response({
            "message": "Candidate registered successfully",
            "email": email,
            "user": _build_user_payload(user),
        }, status=201)

    except ValidationError as e:
        return Response({"error": str(e)}, status=400)
    except ValueError as e:
        return Response({"error": str(e)}, status=400)
    except Exception as e:
        raise


@api_view(['POST'])
def register_recruiter(request):
    try:
        data = request.data

        # Validate required fields
        email = validate_email_address(data.get('email'))
        password = validate_password(data.get('password'))
        full_name = validate_full_name(data.get('full_name'))

        # Validate optional fields
        company_name = validate_text_field(data.get('company_name'), 'Company Name', max_length=100, required=False)

        # Prepare validated data
        validated_data = {
            'email': email,
            'password': password,
            'full_name': full_name,
            'company_name': company_name
        }

        user = create_recruiter(validated_data, None)
        return Response({
            "message": "Recruiter registered successfully",
            "email": email,
            "user": _build_user_payload(user),
        }, status=201)

    except ValidationError as e:
        return Response({"error": str(e)}, status=400)
    except ValueError as e:
        return Response({"error": str(e)}, status=400)
    except Exception as e:
        raise


@api_view(['POST'])
def login(request):
    try:
        data = request.data

        identifier = data.get('email') or data.get('identifier') or data.get('login')
        password = data.get('password')

        if not identifier:
            raise ValidationError("Email or login ID is required")

        if not password:
            raise ValidationError("Password is required")

        resolved_user = _resolve_login_user(identifier)
        username = resolved_user.username if resolved_user else str(identifier).strip()
        user = authenticate(username=username, password=password)

        if not user:
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        refresh = RefreshToken.for_user(user)
        user_payload = _build_user_payload(user)

        return Response({
            "message": "Login successful",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "role": user_payload["role"],
            "user_id": user.id,
            "email": user.email,
            "user": user_payload,
        }, status=200)

    except (ValidationError, AuthenticationError) as e:
        return Response({"error": str(e)}, status=e.status_code)
    except Exception as e:
        raise


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def create_recruiter_view(request):
    user = create_recruiter(request.data, request.user)
    return Response({
        "message": "Recruiter created",
        "user": _build_user_payload(user),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def list_active_recruiters_view(request):
    recruiters = User.objects.filter(
        userprofile__role='recruiter',
        is_active=True,
    ).select_related('recruiterprofile').order_by('-date_joined')

    data = []
    for recruiter in recruiters:
        company_name = ''
        try:
            company_name = recruiter.recruiterprofile.company_name
        except RecruiterProfile.DoesNotExist:
            company_name = ''

        data.append({
            "id": recruiter.id,
            "email": recruiter.email,
            "first_name": recruiter.first_name,
            "last_name": recruiter.last_name,
            "full_name": recruiter.get_full_name().strip() or recruiter.email,
            "company_name": company_name,
            "date_joined": recruiter.date_joined,
            "is_active": recruiter.is_active,
        })

    return Response({
        "count": len(data),
        "results": data,
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsAdmin])
def deactivate_recruiter_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if get_user_role(user) != 'recruiter':
        return Response({"error": "Target user is not an active recruiter"}, status=400)
    deactivate_recruiter(user, request.user)

    return Response({"message": "Recruiter deactivated"})
