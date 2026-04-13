import hashlib
from pathlib import Path


from django.conf import settings


from django.utils import timezone


import httpx

from ats_backend.utils.supabase_client import get_supabase_client


from core.logger import logger


from jobs.utils.embedding import generate_embedding


from services.parser.resume_parser import parse_resume


from .models import Project, Resume, Skill


def compute_resume_checksum(file_bytes):
    return hashlib.sha256(file_bytes).hexdigest()

def validate_resume_integrity(file_bytes, expected_size=None):
    if not file_bytes:
        raise ValueError("Uploaded resume is empty")

    if expected_size is not None and len(file_bytes) != int(expected_size):
        raise ValueError("Uploaded resume failed integrity validation")

    return compute_resume_checksum(file_bytes)

def load_resume_bytes(resume):
    if resume.storage_backend == Resume.StorageBackend.LOCAL and resume.storage_path:
        return Path(resume.storage_path).read_bytes()

    if resume.storage_backend == Resume.StorageBackend.SUPABASE and resume.storage_path:
        supabase = get_supabase_client()
        if supabase is None:
            raise FileNotFoundError("Supabase client unavailable")
        try:
            return supabase.storage.from_("Candidate_resume").download(resume.storage_path)
        except Exception:
            if resume.cloud_url and str(resume.cloud_url).startswith("http"):
                response = httpx.get(resume.cloud_url, timeout=30.0)
                response.raise_for_status()
                return response.content
            raise

    if resume.storage_backend == Resume.StorageBackend.LOCAL and resume.cloud_url:
        return Path(resume.cloud_url).read_bytes()

    raise FileNotFoundError("Resume storage path is unavailable")

def process_uploaded_resume(resume_id):
    resume = Resume.objects.select_related("candidate", "organization").filter(id=resume_id).first()
    if not resume:
        logger.warning("Resume %s not found for background processing", resume_id)
        return False

    try:
        file_bytes = load_resume_bytes(resume)
        calculated_checksum = validate_resume_integrity(file_bytes, expected_size=resume.file_size)
        if resume.checksum_sha256 and resume.checksum_sha256 != calculated_checksum:
            raise ValueError("Stored checksum does not match uploaded file contents")

        parsed_data = parse_resume(file_bytes, resume.mime_type or "application/pdf")
        raw_text = parsed_data.get("raw_text", "") or ""
        parsed_skills = sorted(
            {str(skill).strip() for skill in parsed_data.get("skills", []) if str(skill).strip()}
        )
        parsed_projects = sorted(
            {str(project).strip() for project in parsed_data.get("projects", []) if str(project).strip()}
        )
        parsed_experience = parsed_data.get("experience")

        embedding = None
        if raw_text:
            embedding = generate_embedding(raw_text)
            if hasattr(embedding, "tolist"):
                embedding = embedding.tolist()

        resume.raw_text = raw_text
        resume.embedding = embedding
        resume.parsing_status = (
            Resume.ParsingStatus.COMPLETED if raw_text else Resume.ParsingStatus.FAILED
        )
        resume.parsing_error = "" if raw_text else "No readable text could be extracted from the uploaded resume."
        resume.parsed_at = timezone.now()
        resume.checksum_sha256 = calculated_checksum
        resume.save(
            update_fields=[
                "raw_text",
                "embedding",
                "parsing_status",
                "parsing_error",
                "parsed_at",
                "checksum_sha256",
                "updated_at",
            ]
        )

        resume.skills.all().delete()
        resume.projects.all().delete()

        if parsed_skills:
            Skill.objects.bulk_create(
                [Skill(resume=resume, skill_name=skill) for skill in parsed_skills],
                ignore_conflicts=True,
            )

        if parsed_projects:
            Project.objects.bulk_create(
                [Project(resume=resume, name=project_name) for project_name in parsed_projects]
            )

        candidate = resume.candidate
        candidate.resume_url = resume.cloud_url or str(resume.storage_path or "")
        candidate.resume_file_name = resume.file_name
        if parsed_experience is not None and parsed_experience > 0:
            candidate.total_experience_years = parsed_experience
        candidate.save(update_fields=["resume_url", "resume_file_name", "total_experience_years", "updated_at"])

        logger.info("Resume %s processed successfully", resume_id)
        return True
    except Exception as error:
        resume.parsing_status = Resume.ParsingStatus.FAILED
        resume.parsing_error = str(error)
        resume.parsed_at = timezone.now()
        resume.save(update_fields=["parsing_status", "parsing_error", "parsed_at", "updated_at"])
        logger.error("Resume %s processing failed: %s", resume_id, error, exc_info=True)
        return False
