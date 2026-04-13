import uuid
from pathlib import Path


from rest_framework.decorators import api_view, permission_classes


from rest_framework.permissions import IsAuthenticated


from rest_framework.response import Response


from rest_framework import status


from django.conf import settings


from django.http import Http404


from django.db import transaction


from authentication.organization import (


    ensure_candidate_organization,
    ensure_resume_organization,
    get_user_organization,
    resolve_candidate_organization,
)
from candidates.models import Candidate


from resumes.models import Resume


from ats_backend.utils.supabase_client import get_supabase_client


from .serializers import ResumeUploadSerializer


from .processing import validate_resume_integrity


from .tasks import process_uploaded_resume_task


from core.validators import validate_resume


from core.exceptions import FileUploadError


from core.logger import logger


from .utils import (


    build_resume_access_url,
    can_user_access_resume,
    build_resume_file_response,
    build_resume_text_fallback_response,
    resolve_resume_access_target,
)

def _dispatch_resume_processing(resume_id):
    mode = getattr(settings, "RESUME_PROCESSING_MODE", "auto")
    broker_url = getattr(settings, "CELERY_BROKER_URL", "")

    use_celery = mode == "celery" or (mode == "auto" and bool(broker_url))
    if use_celery:
        try:
            process_uploaded_resume_task.delay(resume_id)
            return "celery"
        except Exception as error:
            logger.warning("Celery dispatch failed for resume %s, falling back to sync: %s", resume_id, error)

    process_uploaded_resume_task(resume_id)
    return "sync"

def _should_use_local_resume_storage():
    mode = getattr(settings, "RESUME_PROCESSING_MODE", "auto")
    broker_url = getattr(settings, "CELERY_BROKER_URL", "")
    if mode == "celery":
        return False
    if mode == "auto" and broker_url:
        return False
    return True

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_resume(request):
    try:
        logger.info("Resume upload request received")

        serializer = ResumeUploadSerializer(data=request.data)

        if not serializer.is_valid():
            logger.error(f"Resume serializer validation failed: {serializer.errors}")
            return Response(serializer.errors, status=400)

        candidate_id = serializer.validated_data.get("candidate_id")
        file = serializer.validated_data["resume"]
        user_organization = get_user_organization(request.user)

        validate_resume(file)

        if candidate_id:
            candidate = Candidate.objects.get(id=candidate_id, organization=user_organization)
        else:
            candidate = Candidate.objects.filter(user=request.user, organization=user_organization).first()
            if not candidate:
                candidate = Candidate.objects.filter(email=request.user.email, organization=user_organization).first()
            if not candidate:
                candidate = Candidate.objects.create(
                    user=request.user,
                    organization=resolve_candidate_organization(user=request.user),
                    email=request.user.email,
                    full_name=request.user.get_full_name().strip() or request.user.email,
                )

        ensure_candidate_organization(candidate, user_organization)

        file_bytes = file.read()
        checksum = validate_resume_integrity(file_bytes, expected_size=file.size)
        duplicate_resume = Resume.objects.filter(
            candidate=candidate,
            organization=user_organization,
            checksum_sha256=checksum,
            is_active=True,
        ).order_by("-uploaded_at", "-id").first()
        if duplicate_resume:
            return Response({
                "message": "Resume already uploaded",
                "candidate_id": candidate.id,
                "resume_id": duplicate_resume.id,
                "resume_url": build_resume_access_url(request, duplicate_resume),
                "file_name": duplicate_resume.file_name,
                "uploaded_at": duplicate_resume.uploaded_at,
                "parsing_status": duplicate_resume.parsing_status,
                "checksum_sha256": duplicate_resume.checksum_sha256,
            }, status=200)

        file_name = f"{uuid.uuid4()}_{file.name}"
        supabase = get_supabase_client()

        try:
            if _should_use_local_resume_storage():
                raise RuntimeError("Configured to use local storage for resume processing")

            if supabase is None:
                raise RuntimeError("Supabase client unavailable")

            supabase.storage.from_("Candidate_resume").upload(file_name, file_bytes)
            file_url = supabase.storage.from_("Candidate_resume").get_public_url(file_name)
            storage_backend = Resume.StorageBackend.SUPABASE
            storage_path = file_name
        except Exception as upload_err:
            logger.warning("Using local storage for resume upload: %s", upload_err)
            local_folder = Path(settings.BASE_DIR) / "tmp_resume_uploads"
            local_folder.mkdir(parents=True, exist_ok=True)
            local_path = local_folder / file_name
            local_path.write_bytes(file_bytes)
            file_url = str(local_path)
            storage_backend = Resume.StorageBackend.LOCAL
            storage_path = str(local_path)

        with transaction.atomic():
            resume = Resume.objects.create(
                candidate=candidate,
                organization=candidate.organization,
                file_name=file.name,
                cloud_url=file_url,
                storage_backend=storage_backend,
                storage_path=storage_path,
                checksum_sha256=checksum,
                file_size=file.size,
                mime_type=file.content_type,
                raw_text="",
                embedding=None,
                parsing_status=Resume.ParsingStatus.PENDING,
                parsing_error="",
                is_primary=False,
            )

            Resume.objects.filter(
                candidate=candidate,
                organization=candidate.organization,
                is_active=True,
            ).exclude(id=resume.id).update(is_primary=False)
            ensure_resume_organization(resume, candidate.organization)
            resume.is_primary = True
            resume.save(update_fields=["is_primary", "updated_at"])

            candidate.resume_url = file_url
            candidate.resume_file_name = file.name
            candidate.save(update_fields=["resume_url", "resume_file_name", "updated_at"])

        logger.info("Resume uploaded successfully for candidate %s", candidate.id)
        dispatch_mode = _dispatch_resume_processing(resume.id)
        resume.refresh_from_db()

        response_status = 202 if dispatch_mode == "celery" else 200
        response_message = (
            "Resume uploaded successfully and queued for background processing"
            if dispatch_mode == "celery"
            else "Resume uploaded and processed successfully"
        )
        return Response({
            "message": response_message,
            "url": build_resume_access_url(request, resume),
            "resume_url": build_resume_access_url(request, resume),
            "candidate_id": candidate.id,
            "resume_id": resume.id,
            "match_scores": [],
            "match_score": None,
            "file_name": resume.file_name,
            "uploaded_at": resume.uploaded_at,
            "parsing_status": resume.parsing_status,
            "checksum_sha256": resume.checksum_sha256,
            "processing_mode": dispatch_mode,
        }, status=response_status)

    except Candidate.DoesNotExist:
        return Response({"error": "Candidate not found"}, status=404)
    except FileUploadError as error:
        logger.warning("Resume upload validation failed: %s", error)
        return Response({"error": str(error)}, status=error.status_code)
    except ValueError as error:
        logger.warning("Resume integrity validation failed: %s", error)
        return Response({"error": str(error)}, status=400)
    except Exception as e:
        logger.error(f"Resume upload error: {str(e)}")
        return Response({"error": str(e)}, status=500)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def resolve_resume_access(request, resume_id):
    resume = Resume.objects.select_related("candidate", "organization").filter(id=resume_id, is_active=True).first()
    if not resume:
        raise Http404("Resume not found")

    if not can_user_access_resume(request.user, resume):
        return Response({"error": "You do not have permission to access this resume"}, status=403)

    target = resolve_resume_access_target(request, resume)
    return Response({
        "resume_id": resume.id,
        "file_name": resume.file_name,
        "mime_type": resume.mime_type,
        **target,
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def serve_resume_file(request, resume_id):
    resume = Resume.objects.select_related("candidate", "organization").filter(id=resume_id, is_active=True).first()
    if not resume:
        raise Http404("Resume not found")

    if not can_user_access_resume(request.user, resume):
        return Response({"error": "You do not have permission to access this resume"}, status=403)

    try:
        return build_resume_file_response(resume)
    except FileNotFoundError:
        try:
            return build_resume_text_fallback_response(resume)
        except FileNotFoundError:
            raise Http404("Resume file not found")
