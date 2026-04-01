from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from authentication.permissions import IsRecruiter
from candidates.models import Candidate
from jobs.models import JobApplication, JobDescription
from resumes.models import Resume
from resumes.utils import build_resume_access_url

from matching.utils import (
    calculate_weighted_match_score,
    get_best_resume_for_candidate,
    get_match_score_for_resume_and_job,
    rank_job_applications,
    score_candidate_job_fit,
    update_match_scores_for_resume,
)


FORMULA = (
    "final_score = weighted blend of skills, semantic alignment, experience fit, "
    "title alignment, education fit, and application quality with penalties for key gaps"
)


def _serialize_job(job):
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "type": job.job_type,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "created_at": job.created_at,
    }


def _serialize_match_payload(score_data):
    components = score_data["components"]
    return {
        "score": round(score_data["score"] * 100, 2),
        "final_score": round(score_data["score"], 4),
        "fit_label": components.get("fit_label"),
        "recommendation": components.get("recommendation"),
        "confidence": components.get("confidence"),
        "component_scores": {
            "skills": round(components["skill_score"], 4),
            "education": round(components["education_score"], 4),
            "experience": round(components["experience_score"], 4),
            "semantic": round(components["semantic_score"], 4),
            "title": round(components.get("title_score", 0), 4),
            "application": round(components.get("application_score", 0), 4),
        },
        "weights": components["weights"],
        "evidence": components.get("evidence", {}),
        "metrics": components.get("metrics", {}),
        "model_version": components.get("model_version"),
    }


def _serialize_candidate(candidate, resume=None, request=None):
    return {
        "id": candidate.id,
        "full_name": candidate.full_name,
        "email": candidate.email,
        "phone": candidate.phone,
        "summary": candidate.summary,
        "total_experience_years": candidate.total_experience_years,
        "resume_url": build_resume_access_url(request, resume) if resume else candidate.resume_url,
        "resume_file_name": (resume.file_name if resume else candidate.resume_file_name),
        "resume_id": resume.id if resume else None,
    }


def _serialize_ranked_application(item, request=None):
    application = item["application"]
    candidate = item["candidate"]
    resume = item["resume"]
    return {
        "application_id": application.id,
        "status": application.status,
        "applied_at": application.applied_at,
        "updated_at": application.updated_at,
        "cover_letter": application.cover_letter,
        "expected_salary": application.expected_salary,
        "available_from": application.available_from,
        "candidate": _serialize_candidate(candidate, resume=resume, request=request),
        "resume_id": resume.id if resume else None,
        "score": item["score_percent"],
        "final_score": round(item["score"], 4),
        "fit_label": item["fit_label"],
        "recommendation": item["recommendation"],
        "confidence": item["confidence"],
        "component_scores": item["component_scores"],
        "weights": item["weights"],
        "evidence": item["evidence"],
        "metrics": item["metrics"],
        "model_version": item["model_version"],
    }


def _get_recruiter_owned_job_or_404(request, job_id):
    queryset = JobDescription.objects.filter(is_active=True)
    if not (request.user.is_superuser or request.user.is_staff):
        queryset = queryset.filter(posted_by=request.user)
    return get_object_or_404(queryset, id=job_id)


def _parse_top_n(request, default=20, minimum=1, maximum=200):
    raw_value = request.query_params.get("top") or request.data.get("top_n") or request.data.get("top")
    try:
        value = int(raw_value or default)
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(value, maximum))


@api_view(["GET"])
def match_jobs_for_resume(request, resume_id):
    resume = Resume.objects.select_related("candidate").filter(id=resume_id).first()
    if not resume:
        return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)

    scores = update_match_scores_for_resume(resume_id)
    job_map = {
        job.id: job
        for job in JobDescription.objects.filter(id__in=[score["job_id"] for score in scores[:20]])
    }

    formatted_scores = []
    for score_data in scores[:20]:
        job = job_map.get(score_data["job_id"])
        if not job:
            continue
        formatted_scores.append({
            "job_id": score_data["job_id"],
            "job": _serialize_job(job),
            **_serialize_match_payload(score_data),
        })

    return Response({
        "resume_id": resume_id,
        "matches": formatted_scores,
        "formula": FORMULA,
    })


@api_view(["GET"])
def match_jobs_for_candidate(request, candidate_id):
    candidate = Candidate.objects.filter(id=candidate_id).first()
    if not candidate:
        return Response({"error": "Candidate not found"}, status=status.HTTP_404_NOT_FOUND)

    latest_resume = get_best_resume_for_candidate(candidate)
    if not latest_resume:
        return Response({"error": "Candidate has no resume"}, status=status.HTTP_404_NOT_FOUND)

    scores = update_match_scores_for_resume(latest_resume.id)
    job_map = {
        job.id: job
        for job in JobDescription.objects.filter(id__in=[score["job_id"] for score in scores[:20]])
    }

    formatted_scores = []
    for score_data in scores[:20]:
        job = job_map.get(score_data["job_id"])
        if not job:
            continue
        formatted_scores.append({
            "job_id": score_data["job_id"],
            "job": _serialize_job(job),
            **_serialize_match_payload(score_data),
        })

    return Response({
        "candidate_id": candidate_id,
        "resume_id": latest_resume.id,
        "matches": formatted_scores,
        "formula": FORMULA,
    })


@api_view(["GET"])
def match_candidates_for_job(request, job_id):
    job = JobDescription.objects.filter(id=job_id, is_active=True).prefetch_related("skills").first()
    if not job:
        return Response({"error": "Job not found or inactive"}, status=status.HTTP_404_NOT_FOUND)

    top_n = _parse_top_n(request)
    resumes = Resume.objects.filter(is_active=True).select_related("candidate").prefetch_related(
        "skills",
        "education",
        "experiences",
        "projects",
    )[:2000]

    results = []
    for resume in resumes:
        final_score, components = calculate_weighted_match_score(resume, job)
        results.append({
            "candidate_id": resume.candidate.id,
            "candidate": _serialize_candidate(resume.candidate, resume=resume, request=request),
            "resume_id": resume.id,
            "score": round(final_score * 100, 2),
            "final_score": round(final_score, 4),
            "fit_label": components.get("fit_label"),
            "recommendation": components.get("recommendation"),
            "confidence": components.get("confidence"),
            "component_scores": {
                "skills": round(components["skill_score"], 4),
                "education": round(components["education_score"], 4),
                "experience": round(components["experience_score"], 4),
                "semantic": round(components["semantic_score"], 4),
                "title": round(components.get("title_score", 0), 4),
                "application": round(components.get("application_score", 0), 4),
            },
            "weights": components["weights"],
            "evidence": components.get("evidence", {}),
            "metrics": components.get("metrics", {}),
            "model_version": components.get("model_version"),
        })

    results.sort(key=lambda item: item["final_score"], reverse=True)

    return Response({
        "job_id": job_id,
        "job": _serialize_job(job),
        "total_candidates_scored": len(results),
        "requested_top": top_n,
        "matches": results[:top_n],
        "formula": FORMULA,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsRecruiter])
def match_applicants_for_job(request, job_id):
    job = _get_recruiter_owned_job_or_404(request, job_id)
    top_n = _parse_top_n(request, default=20)

    applications = job.applications.select_related("candidate").prefetch_related(
        "candidate__resumes__skills",
        "candidate__resumes__education",
        "candidate__resumes__experiences",
        "candidate__resumes__projects",
    ).order_by("-applied_at")

    ranked_applications = rank_job_applications(job, applications, top_n=top_n)

    return Response({
        "job": _serialize_job(job),
        "total_applicants": job.applications.count(),
        "requested_top": top_n,
        "returned_count": len(ranked_applications),
        "matches": [_serialize_ranked_application(item, request=request) for item in ranked_applications],
        "formula": FORMULA,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsRecruiter])
def shortlist_top_candidates_for_job(request, job_id):
    job = _get_recruiter_owned_job_or_404(request, job_id)
    top_n = _parse_top_n(request, default=3, maximum=50)

    eligible_statuses = [
        JobApplication.Status.APPLIED,
        JobApplication.Status.UNDER_REVIEW,
        JobApplication.Status.INTERVIEWED,
        JobApplication.Status.SHORTLISTED,
    ]
    applications = job.applications.filter(status__in=eligible_statuses).select_related("candidate").prefetch_related(
        "candidate__resumes__skills",
        "candidate__resumes__education",
        "candidate__resumes__experiences",
        "candidate__resumes__projects",
    ).order_by("-applied_at")

    ranked_applications = rank_job_applications(job, applications, top_n=top_n)
    selected_ids = [item["application"].id for item in ranked_applications]

    with transaction.atomic():
        job.applications.filter(status=JobApplication.Status.SHORTLISTED).exclude(
            id__in=selected_ids
        ).update(status=JobApplication.Status.UNDER_REVIEW)

        if selected_ids:
            job.applications.filter(id__in=selected_ids).exclude(
                status__in=[JobApplication.Status.REJECTED, JobApplication.Status.HIRED]
            ).update(status=JobApplication.Status.SHORTLISTED)

    return Response({
        "message": f"Top {len(selected_ids)} candidates shortlisted",
        "job": _serialize_job(job),
        "requested_top": top_n,
        "shortlisted_count": len(selected_ids),
        "shortlisted_application_ids": selected_ids,
        "matches": [_serialize_ranked_application(item, request=request) for item in ranked_applications],
        "formula": FORMULA,
    })


@api_view(["GET"])
def match_resume_to_job(request, resume_id, job_id):
    match_data = get_match_score_for_resume_and_job(resume_id, job_id)
    if not match_data:
        return Response({"error": "Resume or job not found"}, status=status.HTTP_404_NOT_FOUND)

    components = match_data["components"]
    return Response({
        "resume_id": resume_id,
        "job_id": job_id,
        "score": round(match_data["final_score"] * 100, 2),
        "match_score": round(match_data["final_score"], 4),
        "fit_label": components.get("fit_label"),
        "recommendation": components.get("recommendation"),
        "confidence": components.get("confidence"),
        "components": {
            "skills": round(components["skill_score"], 4),
            "education": round(components["education_score"], 4),
            "experience": round(components["experience_score"], 4),
            "semantic": round(components["semantic_score"], 4),
            "title": round(components.get("title_score", 0), 4),
            "application": round(components.get("application_score", 0), 4),
        },
        "weights": components["weights"],
        "evidence": components.get("evidence", {}),
        "metrics": components.get("metrics", {}),
        "model_version": components.get("model_version"),
        "formula": FORMULA,
    })
