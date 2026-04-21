import logging
from io import BytesIO
from pathlib import Path

from django.http import FileResponse, HttpResponse
from django.shortcuts import redirect
from django.utils.html import escape
from django.urls import reverse

from ats_backend.utils.supabase_client import get_supabase_client
from authentication.organization import get_user_organization
from jobs.models import JobApplication

logger = logging.getLogger(__name__)


def get_active_resume_for_candidate(candidate, organization=None):
    if not candidate:
        return None

    resumes = candidate.resumes.filter(is_active=True)
    if organization is not None:
        preferred = resumes.filter(organization=organization).order_by("-is_primary", "-uploaded_at", "-id").first()
        if preferred:
            return preferred

    return resumes.order_by("-is_primary", "-uploaded_at", "-id").first()


def build_resume_access_path(resume):
    return reverse("resume_file", args=[resume.id])


def build_resume_access_url(request, resume):
    path = build_resume_access_path(resume)
    if request is None:
        return path
    return request.build_absolute_uri(path)


def resolve_resume_access_target(request, resume):
    if (
        resume.storage_backend == resume.StorageBackend.SUPABASE
        and resume.cloud_url
        and not resume.storage_path
    ):
        return {
            "url": resume.cloud_url,
            "requires_auth": False,
        }

    access_url = build_resume_access_url(request, resume)
    return {
        "url": access_url,
        "requires_auth": True,
    }


def can_user_access_resume(user, resume):
    if not user or not user.is_authenticated:
        return False

    if user.is_staff or user.is_superuser:
        return True

    profile = getattr(user, "userprofile", None)
    role = getattr(profile, "role", None)

    if role == "candidate":
        return (
            get_user_organization(user) == resume.organization
            and (resume.candidate.user_id == user.id or resume.candidate.email == user.email)
        )

    if role == "recruiter":
        return JobApplication.objects.filter(
            candidate=resume.candidate,
            job__posted_by=user,
        ).exists()

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
        supabase = get_supabase_client()
        if supabase is None:
            raise FileNotFoundError("Supabase storage is not available")

        try:
            file_bytes = supabase.storage.from_("Candidate_resume").download(resume.storage_path)
            if file_bytes:
                return FileResponse(
                    BytesIO(file_bytes),
                    content_type=resume.mime_type or "application/octet-stream",
                    filename=resume.file_name,
                    as_attachment=False,
                )
        except Exception as error:
            logger.warning("Supabase resume download failed for resume %s: %s", resume.id, error)

    if resume.storage_backend == resume.StorageBackend.SUPABASE and resume.cloud_url:
        return redirect(resume.cloud_url)

    if resume.storage_path:
        file_path = Path(resume.storage_path)
        return FileResponse(
            file_path.open("rb"),
            content_type=resume.mime_type or "application/octet-stream",
            filename=resume.file_name,
            as_attachment=False,
        )

    raise FileNotFoundError("Resume file is not available")


def build_resume_text_fallback_response(resume):
    raw_text = (resume.raw_text or "").strip()
    if not raw_text:
        raise FileNotFoundError("Resume file is not available")

    safe_title = escape(resume.file_name or "Resume Preview")
    safe_body = escape(raw_text)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; background: #f8fafc; color: #0f172a; margin: 0; }}
    main {{ max-width: 960px; margin: 0 auto; padding: 32px 20px 48px; }}
    .card {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06); }}
    h1 {{ font-size: 24px; margin: 0 0 8px; }}
    p {{ color: #475569; margin: 0 0 20px; }}
    pre {{ white-space: pre-wrap; word-break: break-word; font-family: inherit; font-size: 14px; line-height: 1.7; margin: 0; }}
  </style>
</head>
<body>
  <main>
    <div class="card">
      <h1>{safe_title}</h1>
      <p>Original resume file is unavailable right now, so this extracted preview is being shown instead.</p>
      <pre>{safe_body}</pre>
    </div>
  </main>
</body>
</html>"""
    return HttpResponse(html, content_type="text/html; charset=utf-8")
