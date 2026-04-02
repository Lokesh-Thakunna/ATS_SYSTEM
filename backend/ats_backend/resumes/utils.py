from io import BytesIO
from pathlib import Path

from django.http import FileResponse
from django.urls import reverse

from ats_backend.utils.supabase_client import supabase
from jobs.models import JobApplication


def get_active_resume_for_candidate(candidate):
    if not candidate:
        return None

    return (
        candidate.resumes
        .filter(is_active=True)
        .order_by("-is_primary", "-uploaded_at", "-id")
        .first()
    )


def build_resume_access_path(resume):
    return reverse("resume_file", args=[resume.id])


def build_resume_access_url(request, resume):
    path = build_resume_access_path(resume)
    if request is None:
        return path
    return request.build_absolute_uri(path)


def can_user_access_resume(user, resume):
    if not user or not user.is_authenticated:
        return False

    if user.is_staff or user.is_superuser:
        return True

    profile = getattr(user, "userprofile", None)
    role = getattr(profile, "role", None)

    if role == "candidate":
        return resume.candidate.user_id == user.id or resume.candidate.email == user.email

    if role == "recruiter":
        return JobApplication.objects.filter(candidate=resume.candidate, job__posted_by=user).exists()

    return False


def build_resume_file_response(resume):
    if resume.storage_backend == resume.StorageBackend.LOCAL and resume.storage_path:
        file_path = Path(resume.storage_path)
        return FileResponse(
            file_path.open("rb"),
            content_type=resume.mime_type or "application/octet-stream",
            filename=resume.file_name,
            as_attachment=False,
        )

    if resume.storage_backend == resume.StorageBackend.SUPABASE and resume.storage_path:
        file_bytes = supabase.storage.from_("Candidate_resume").download(resume.storage_path)
        if file_bytes:
            return FileResponse(
                BytesIO(file_bytes),
                content_type=resume.mime_type or "application/octet-stream",
                filename=resume.file_name,
                as_attachment=False,
            )

    if resume.storage_path:
        file_path = Path(resume.storage_path)
        return FileResponse(
            file_path.open("rb"),
            content_type=resume.mime_type or "application/octet-stream",
            filename=resume.file_name,
            as_attachment=False,
        )

    raise FileNotFoundError("Resume file is not available")
