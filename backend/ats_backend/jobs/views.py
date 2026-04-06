from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from authentication.permissions import IsRecruiter

from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db.models import Q, Count

from .models import JobDescription, JobSkill, JobApplication
from .serializers import JobDescriptionSerializer, AddJobSkillsSerializer, UpdateJobApplicationStatusSerializer
from .utils.embedding import generate_embedding
from candidates.models import Candidate
from resumes.models import Resume, Skill, Project
from resumes.utils import build_resume_access_url, get_active_resume_for_candidate

import os
import uuid
from ats_backend.utils.supabase_client import get_supabase_client


def _get_recruiter_owned_job_or_404(request, job_id):
    queryset = JobDescription.objects.all()
    if not (request.user.is_superuser or request.user.is_staff):
        queryset = queryset.filter(posted_by=request.user)
    return get_object_or_404(queryset, id=job_id)


def _get_recruiter_owned_application_or_404(request, application_id):
    queryset = JobApplication.objects.select_related("job", "candidate")
    if not (request.user.is_superuser or request.user.is_staff):
        queryset = queryset.filter(job__posted_by=request.user)
    return get_object_or_404(queryset, id=application_id)


# CREATE JOB
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsRecruiter])
def create_job(request):

    serializer = JobDescriptionSerializer(data=request.data)

    if serializer.is_valid():

        title = serializer.validated_data.get("title", "")
        description = serializer.validated_data.get("description", "")

        # embedding ke liye text
        text = f"{title} {description}".strip()

        embedding = None
        if text:
            embedding = generate_embedding(text)
            # numpy → list
            if hasattr(embedding, "tolist"):
                embedding = embedding.tolist()

        job = serializer.save(embedding=embedding, posted_by=request.user)

        return Response(
            {
                "message": "Job created successfully",
                "job_id": job.id
            },
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# GET ALL JOBS
@api_view(["GET"])
def get_jobs(request):
    jobs = JobDescription.objects.prefetch_related("skills").filter(is_active=True)

    keyword = (request.query_params.get("keyword") or request.query_params.get("search") or "").strip()
    location = (request.query_params.get("location") or "").strip()

    if keyword:
        jobs = jobs.filter(
            Q(title__icontains=keyword) |
            Q(company__icontains=keyword) |
            Q(description__icontains=keyword) |
            Q(requirements__icontains=keyword) |
            Q(skills__skill__icontains=keyword)
        ).distinct()

    if location:
        jobs = jobs.filter(location__icontains=location)

    serializer = JobDescriptionSerializer(
        jobs,
        many=True,
        context={"request": request}
    )

    return Response(
        {
            "count": jobs.count(),
            "results": serializer.data
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsRecruiter])
def get_recruiter_jobs(request):
    jobs = (
        JobDescription.objects
        .filter(posted_by=request.user, is_active=True)
        .prefetch_related("skills")
        .annotate(applicant_count=Count("applications"))
        .order_by("-created_at")
    )

    serializer = JobDescriptionSerializer(
        jobs,
        many=True,
        context={"request": request}
    )

    return Response({
        "count": jobs.count(),
        "results": serializer.data
    })


# GET SINGLE JOB
@api_view(["GET"])
def get_job(request, job_id):

    job = get_object_or_404(
        JobDescription.objects.prefetch_related("skills"),
        id=job_id
    )

    serializer = JobDescriptionSerializer(
        job,
        context={"request": request}
    )

    return Response(serializer.data)


# UPDATE JOB
@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsRecruiter])
def update_job(request, job_id):
    job = _get_recruiter_owned_job_or_404(request, job_id)

    serializer = JobDescriptionSerializer(
        job,
        data=request.data,
        partial=True,
        context={"request": request}
    )

    if serializer.is_valid():

        title = serializer.validated_data.get("title", job.title)
        description = serializer.validated_data.get("description", job.description)

        text = f"{title} {description}"

        embedding = generate_embedding(text)

        if hasattr(embedding, "tolist"):
            embedding = embedding.tolist()

        serializer.save(embedding=embedding)

        return Response(
            {
                "message": "Job updated successfully",
                "data": serializer.data
            }
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# DELETE JOB
@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsRecruiter])
def delete_job(request, job_id):
    job = _get_recruiter_owned_job_or_404(request, job_id)

    job.delete()

    return Response(
        {"message": "Job deleted successfully"},
        status=status.HTTP_204_NO_CONTENT
    )


# ADD MULTIPLE SKILLS
class AddJobSkills(APIView):

    def post(self, request):

        serializer = AddJobSkillsSerializer(data=request.data)

        if serializer.is_valid():

            job_id = serializer.validated_data["job_id"]
            skills = serializer.validated_data["skills"]

            job = get_object_or_404(JobDescription, id=job_id)

            created_skills = []

            for skill in skills:

                obj = JobSkill.objects.create(
                    job=job,
                    skill=skill
                )

                created_skills.append(obj.skill)

            return Response(
                {
                    "message": "Skills added successfully",
                    "skills": created_skills
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsRecruiter])
def get_recruiter_applicants(request):
    jobs = (
        JobDescription.objects
        .filter(posted_by=request.user, is_active=True)
        .prefetch_related("applications__candidate")
        .order_by("-created_at")
    )

    results = []
    total_applicants = 0

    for job in jobs:
        applications = job.applications.select_related("candidate").order_by("-applied_at")
        serialized_applications = []

        for application in applications:
            total_applicants += 1
            candidate = application.candidate
            resume = get_active_resume_for_candidate(candidate)
            serialized_applications.append({
                "id": application.id,
                "status": application.status,
                "applied_at": application.applied_at,
                "updated_at": application.updated_at,
                "cover_letter": application.cover_letter,
                "expected_salary": application.expected_salary,
                "available_from": application.available_from,
                "candidate": {
                    "id": candidate.id,
                    "full_name": candidate.full_name,
                    "email": candidate.email,
                    "phone": candidate.phone,
                    "summary": candidate.summary,
                    "total_experience_years": candidate.total_experience_years,
                    "resume_url": build_resume_access_url(request, resume) if resume else candidate.resume_url,
                    "resume_file_name": (resume.file_name if resume else candidate.resume_file_name),
                    "resume_id": resume.id if resume else None,
                },
            })

        results.append({
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "created_at": job.created_at,
            "applications_count": len(serialized_applications),
            "applications": serialized_applications,
        })

    return Response({
        "count": jobs.count(),
        "total_applicants": total_applicants,
        "results": results,
    })


from core.validators import (
    validate_full_name, validate_phone_number, validate_text_field,
    validate_salary, validate_experience_years, validate_resume
)
from core.exceptions import ValidationError, AuthorizationError, ConflictError, FileUploadError


# APPLY FOR JOB
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def apply_for_job(request, job_id):
    """
    Apply for a job - creates/updates candidate profile and job application.
    """
    try:
        # Ensure user is authenticated
        if not request.user or not request.user.is_authenticated:
            raise AuthorizationError("Authentication required")

        # Ensure user is candidate
        try:
            profile = request.user.userprofile
            if profile.role != 'candidate':
                raise AuthorizationError("Only candidates can apply for jobs")
        except:
            raise AuthorizationError("User profile not found")

        # Get and validate job
        try:
            job = JobDescription.objects.get(id=job_id, is_active=True)
        except JobDescription.DoesNotExist:
            from core.exceptions import NotFoundError
            raise NotFoundError("Job not found or inactive")

        # Validate input data
        data = request.data
        full_name = validate_full_name(data.get('full_name', request.user.get_full_name()))
        phone = validate_phone_number(data.get('phone'))
        summary = validate_text_field(data.get('summary'), 'Professional summary', max_length=500, required=False)
        experience_years = validate_experience_years(data.get('total_experience_years'))
        cover_letter = validate_text_field(data.get('cover_letter'), 'Cover letter', max_length=2000, required=False)
        expected_salary = validate_salary(data.get('expected_salary'))

        # Create or update candidate profile
        candidate = Candidate.objects.filter(user=request.user).first()
        created = False
        if not candidate:
            candidate = Candidate.objects.filter(email=request.user.email).first()

        if not candidate:
            candidate = Candidate(
                user=request.user,
                email=request.user.email,
                full_name=full_name,
                phone=phone,
                summary=summary,
                total_experience_years=experience_years,
            )
            created = True
        elif candidate.user_id != request.user.id:
            candidate.user = request.user

        # Update candidate information if not created
        candidate.email = request.user.email
        candidate.full_name = full_name
        candidate.phone = phone or candidate.phone
        candidate.summary = summary or candidate.summary
        candidate.total_experience_years = experience_years if experience_years is not None else candidate.total_experience_years
        candidate.save()

        # Prevent duplicate application
        if JobApplication.objects.filter(candidate=candidate, job=job).exists():
            raise ConflictError("Already applied for this job")

        # Handle resume upload
        if 'resume' in request.FILES:
            resume_file = request.FILES['resume']
            validate_resume(resume_file)

            try:
                from services.parser.resume_parser import parse_resume

                file_name = f"{uuid.uuid4()}_{resume_file.name}"
                file_bytes = resume_file.read()
                supabase = get_supabase_client()

                # Upload to Supabase (with fallback to local when RLS/permission failure)
                try:
                    if supabase is None:
                        raise RuntimeError("Supabase client unavailable")

                    supabase.storage.from_("Candidate_resume").upload(file_name, file_bytes)
                    cloud_url = supabase.storage.from_("Candidate_resume").get_public_url(file_name)
                except Exception as upload_err:
                    upload_msg = str(upload_err)
                    if 'row-level security policy' in upload_msg or 'Unauthorized' in upload_msg or 'statusCode' in upload_msg:
                        # Fallback to local storage
                        cloud_url = None
                        local_folder = os.path.join(settings.BASE_DIR, 'tmp_resume_uploads')
                        os.makedirs(local_folder, exist_ok=True)
                        local_path = os.path.join(local_folder, file_name)
                        with open(local_path, 'wb') as f:
                            f.write(file_bytes)
                    else:
                        raise FileUploadError(f"Resume upload failed: {upload_msg}")

                # Parse and store resume
                raw_text = ''
                parsed_skills = []
                parsed_projects = []
                parsed_experience = None
                try:
                    parsed_data = parse_resume(file_bytes, resume_file.content_type)
                    raw_text = parsed_data.get('raw_text', '')
                    parsed_skills = sorted({str(skill).strip() for skill in parsed_data.get('skills', []) if str(skill).strip()})
                    parsed_projects = sorted({str(project).strip() for project in parsed_data.get('projects', []) if str(project).strip()})
                    parsed_experience = parsed_data.get('experience')
                except Exception as parse_err:
                    # Log parsing error but don't fail the application
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Resume parsing failed: {str(parse_err)}")

                # Generate embedding
                embedding = None
                if raw_text:
                    try:
                        embedding = generate_embedding(raw_text)
                        if hasattr(embedding, 'tolist'):
                            embedding = embedding.tolist()
                    except Exception as embed_err:
                        # Log embedding error but don't fail the application
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Embedding generation failed: {str(embed_err)}")

                storage_backend = Resume.StorageBackend.SUPABASE if cloud_url else Resume.StorageBackend.LOCAL
                storage_path = file_name if cloud_url else local_path

                # Create resume record
                resume = Resume.objects.create(
                    candidate=candidate,
                    file_name=resume_file.name,
                    cloud_url=cloud_url,
                    storage_backend=storage_backend,
                    storage_path=storage_path,
                    file_size=len(file_bytes),
                    mime_type=resume_file.content_type,
                    raw_text=raw_text,
                    embedding=embedding,
                    parsing_status=Resume.ParsingStatus.COMPLETED if raw_text else Resume.ParsingStatus.FAILED,
                    parsing_error='' if raw_text else 'No readable text could be extracted from the uploaded resume.',
                    is_primary=False,
                )

                Resume.objects.filter(candidate=candidate, is_active=True).exclude(id=resume.id).update(is_primary=False)
                resume.is_primary = True
                resume.save(update_fields=['is_primary', 'updated_at'])

                # Update candidate resume info
                candidate.resume_url = cloud_url
                candidate.resume_file_name = resume_file.name
                if parsed_experience is not None and parsed_experience > 0:
                    candidate.total_experience_years = parsed_experience
                candidate.save()

                if parsed_skills:
                    Skill.objects.bulk_create(
                        [Skill(resume=resume, skill_name=skill) for skill in parsed_skills],
                        ignore_conflicts=True,
                    )

                if parsed_projects:
                    Project.objects.bulk_create(
                        [Project(resume=resume, name=project_name) for project_name in parsed_projects]
                    )

            except (FileUploadError, ValidationError):
                raise  # Re-raise our custom exceptions
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Resume processing failed: {str(e)}", exc_info=True)
                raise FileUploadError("Resume processing failed")

        # Create job application
        application = JobApplication.objects.create(
            candidate=candidate,
            job=job,
            cover_letter=cover_letter,
            expected_salary=expected_salary,
            available_from=data.get('available_from') or None,
        )

        return Response({
            "message": "Successfully applied for job",
            "application_id": application.id,
            "candidate_id": candidate.id,
            "job_id": job.id
        }, status=201)

    except (ValidationError, AuthorizationError, ConflictError, FileUploadError) as e:
        return Response({"error": str(e)}, status=e.status_code)
    except Exception as e:
        # This will be handled by the global exception handler
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in apply_for_job: {str(e)}", exc_info=True)
        raise


# GET MY APPLICATIONS
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_my_applications(request):
    """Get current user's job applications"""
    from .models import JobApplication

    try:
        candidate = Candidate.get_for_user(request.user)
    except Candidate.DoesNotExist:
        return Response({"error": "Candidate profile not found"}, status=404)

    applications = JobApplication.objects.filter(candidate=candidate).select_related('job')

    data = []
    for app in applications:
        data.append({
            "id": app.id,
            "job": {
                "id": app.job.id,
                "title": app.job.title,
                "company": app.job.company,
                "location": app.job.location,
                "salary_min": app.job.salary_min,
                "salary_max": app.job.salary_max,
            },
            "status": app.status,
            "applied_at": app.applied_at,
            "updated_at": app.updated_at,
            "cover_letter": app.cover_letter,
            "expected_salary": app.expected_salary,
            "available_from": app.available_from,
        })

    return Response({
        "count": len(data),
        "applications": data
    })


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsRecruiter])
def update_application_status(request, application_id):
    application = _get_recruiter_owned_application_or_404(request, application_id)
    serializer = UpdateJobApplicationStatusSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    application.status = serializer.validated_data["status"]
    application.save(update_fields=["status", "updated_at"])

    return Response({
        "message": "Application status updated successfully",
        "application": {
            "id": application.id,
            "status": application.status,
            "updated_at": application.updated_at,
            "candidate_id": application.candidate_id,
            "job_id": application.job_id,
        },
    })
