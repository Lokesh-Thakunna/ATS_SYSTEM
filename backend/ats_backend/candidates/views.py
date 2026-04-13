from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from authentication.models import UserProfile
from authentication.organization import (
    ensure_candidate_organization,
    get_user_organization,
    resolve_candidate_organization,
)
from .models import Candidate
from resumes.models import Resume
from resumes.utils import build_resume_access_url, get_active_resume_for_candidate


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_candidate_profile(request):
    """Get current user's candidate profile"""
    try:
        candidate = Candidate.get_for_user(request.user)
        resume = get_active_resume_for_candidate(candidate)
        return Response({
            "id": candidate.id,
            "full_name": candidate.full_name,
            "email": candidate.email,
            "phone": candidate.phone,
            "summary": candidate.summary,
            "total_experience_years": candidate.total_experience_years,
            "resume_url": build_resume_access_url(request, resume) if resume else candidate.resume_url,
            "resume_file_name": (resume.file_name if resume else candidate.resume_file_name),
            "resume_id": resume.id if resume else None,
            "resume_mime_type": resume.mime_type if resume else None,
            "created_at": candidate.created_at,
            "updated_at": candidate.updated_at
        })
    except Candidate.DoesNotExist:
        return Response({"error": "Candidate profile not found"}, status=404)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_candidate_profile(request):
    """Update current user's candidate profile"""
    try:
        candidate = Candidate.get_for_user(request.user)
    except Candidate.DoesNotExist:
        return Response({"error": "Candidate profile not found"}, status=404)

    # Update fields
    candidate.full_name = request.data.get("full_name", candidate.full_name)
    candidate.phone = request.data.get("phone", candidate.phone)
    candidate.summary = request.data.get("summary", candidate.summary)
    candidate.total_experience_years = request.data.get("total_experience_years", candidate.total_experience_years)
    candidate.save()

    return Response({
        "message": "Candidate profile updated",
        "candidate_id": candidate.id
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_or_update_candidate_profile(request):
    """
    Create candidate profile if doesn't exist, or update if it does
    Used during job application process
    """
    # Check if user has candidate role
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'candidate':
            return Response({"error": "Only candidates can manage profiles"}, status=403)
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found"}, status=400)

    candidate = Candidate.objects.filter(
        user=request.user,
        organization=get_user_organization(request.user),
    ).first()
    created = False

    if not candidate:
        candidate = Candidate.objects.filter(
            email=request.user.email,
            organization=get_user_organization(request.user),
        ).first()

    if candidate:
        if candidate.user_id != request.user.id:
            candidate.user = request.user
    else:
        organization = resolve_candidate_organization(user=request.user)
        candidate = Candidate(
            user=request.user,
            organization=organization,
            email=request.user.email,
            full_name=request.data.get("full_name", request.user.get_full_name() or request.user.username),
            phone=request.data.get("phone", ""),
            summary=request.data.get("summary", ""),
            total_experience_years=request.data.get("total_experience_years", 0),
        )
        created = True

    # Keep the profile pinned to the authenticated user's organization so
    # candidate records do not drift across tenant boundaries.
    ensure_candidate_organization(candidate, get_user_organization(request.user))
    candidate.email = request.user.email
    candidate.full_name = request.data.get("full_name", candidate.full_name)
    candidate.phone = request.data.get("phone", candidate.phone)
    candidate.summary = request.data.get("summary", candidate.summary)
    candidate.total_experience_years = request.data.get("total_experience_years", candidate.total_experience_years)
    candidate.save()

    return Response({
        "message": "Candidate profile created" if created else "Candidate profile updated",
        "candidate_id": candidate.id
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_candidate_resumes(request):
    """Get all resumes for the current user"""
    try:
        candidate = Candidate.get_for_user(request.user)
        resumes = Resume.objects.filter(
            candidate=candidate,
            organization=candidate.organization,
            is_active=True,
        ).prefetch_related('skills', 'projects').order_by('-uploaded_at')

        resume_data = []
        for resume in resumes:
            resume_data.append({
                "id": resume.id,
                "file_name": resume.file_name,
                "filename": resume.file_name,
                "cloud_url": resume.cloud_url,
                "resume_url": build_resume_access_url(request, resume),
                "access_url": build_resume_access_url(request, resume),
                "file_size": resume.file_size,
                "mime_type": resume.mime_type,
                "raw_text": resume.raw_text,
                "parsing_status": resume.parsing_status,
                "uploaded_at": resume.uploaded_at,
                "created_at": resume.created_at,
                "category": resume.category,
                "is_primary": resume.is_primary,
                "storage_backend": resume.storage_backend,
                "skills": list(resume.skills.values_list("skill_name", flat=True)),
                "projects": list(resume.projects.values_list("name", flat=True)),
            })

        return Response(resume_data)
    except Candidate.DoesNotExist:
        return Response({"error": "Candidate profile not found"}, status=404)
