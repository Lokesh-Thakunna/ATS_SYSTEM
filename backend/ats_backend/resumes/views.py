import uuid

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import Http404
from django.conf import settings

from candidates.models import Candidate
from resumes.models import Resume, Skill, Project
from ats_backend.utils.supabase_client import supabase
from jobs.utils.embedding import generate_embedding
from matching.utils import update_match_scores_for_resume

from .serializers import ResumeUploadSerializer

from services.parser.resume_parser import parse_resume
from core.validators import validate_resume
from core.logger import logger
from .utils import build_resume_access_url, can_user_access_resume, build_resume_file_response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_resume(request):
    try:
        logger.info("Resume upload request received")

        serializer = ResumeUploadSerializer(data=request.data)

        if not serializer.is_valid():
            print(serializer.errors)
            return Response(serializer.errors, status=400)

        candidate_id = serializer.validated_data.get("candidate_id")
        file = serializer.validated_data["resume"]

        validate_resume(file)

        if candidate_id:
            candidate = Candidate.objects.get(id=candidate_id)
        else:
            candidate = Candidate.objects.filter(user=request.user).first()
            if not candidate:
                candidate = Candidate.objects.filter(email=request.user.email).first()
            if not candidate:
                candidate = Candidate.objects.create(
                    user=request.user,
                    email=request.user.email,
                    full_name=request.user.get_full_name().strip() or request.user.email,
                )

        file_name = f"{uuid.uuid4()}_{file.name}"

        file_bytes = file.read()

        # Upload to Candidate_resume bucket in Supabase
        try:
            supabase.storage.from_("Candidate_resume").upload(file_name, file_bytes)
            file_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/Candidate_resume/{file_name}"
            storage_backend = Resume.StorageBackend.SUPABASE
            storage_path = file_name
        except Exception as upload_err:
            logger.warning("Supabase upload failed, falling back to local storage: %s", upload_err)
            local_folder = settings.BASE_DIR / "tmp_resume_uploads"
            local_folder.mkdir(parents=True, exist_ok=True)
            local_path = local_folder / file_name
            with open(local_path, "wb") as local_file:
                local_file.write(file_bytes)
            file_url = str(local_path)
            storage_backend = Resume.StorageBackend.LOCAL
            storage_path = str(local_path)

        parsed_data = parse_resume(file_bytes, file.content_type)

        raw_text = parsed_data.get("raw_text", "")
        skills = parsed_data.get("skills", [])
        experience_years = parsed_data.get("experience", 0.0)
        projects = parsed_data.get("projects", [])

        resume_embedding = generate_embedding(raw_text)
        if hasattr(resume_embedding, "tolist"):
            resume_embedding = resume_embedding.tolist()

        resume = Resume.objects.create(
            candidate=candidate,
            file_name=file.name,
            cloud_url=file_url,
            storage_backend=storage_backend,
            storage_path=storage_path,
            file_size=file.size,
            mime_type=file.content_type,
            raw_text=raw_text,
            embedding=resume_embedding,
            parsing_status=Resume.ParsingStatus.COMPLETED,
            is_primary=False,
        )

        Resume.objects.filter(candidate=candidate, is_active=True).exclude(id=resume.id).update(is_primary=False)
        resume.is_primary = True
        resume.save(update_fields=["is_primary", "updated_at"])

        candidate.resume_url = file_url
        candidate.resume_file_name = file.name
        if experience_years > 0:
            candidate.total_experience_years = experience_years
        candidate.save()

        logger.info(f"Resume uploaded successfully for candidate {candidate_id}")

        for skill in skills:
            Skill.objects.create(resume=resume, skill_name=skill)

        for project_name in projects:
            Project.objects.create(resume=resume, name=project_name)

        try:
            matching_results = update_match_scores_for_resume(resume.id)
        except Exception:
            matching_results = []

        match_scores = [round(m['score'] * 100, 2) for m in matching_results[:10]]
        top_match_score = match_scores[0] if match_scores else None

        return Response({
            "message": "Resume uploaded and parsed successfully",
            "skills": skills,
            "experience_years": experience_years,
            "experience": experience_years,
            "projects": projects,
            "url": build_resume_access_url(request, resume),
            "resume_url": build_resume_access_url(request, resume),
            "candidate_id": candidate.id,
            "resume_id": resume.id,
            "match_scores": match_scores,
            "match_score": top_match_score,
            "file_name": resume.file_name,
            "uploaded_at": resume.uploaded_at,
        })

    except Candidate.DoesNotExist:
        return Response({"error": "Candidate not found"}, status=404)
    except Exception as e:
        logger.error(f"Resume upload error: {str(e)}")
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def serve_resume_file(request, resume_id):
    resume = Resume.objects.select_related("candidate").filter(id=resume_id, is_active=True).first()
    if not resume:
        raise Http404("Resume not found")

    if not can_user_access_resume(request.user, resume):
        return Response({"error": "You do not have permission to access this resume"}, status=403)

    try:
        return build_resume_file_response(resume)
    except FileNotFoundError:
        raise Http404("Resume file not found")
