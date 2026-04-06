import os
import re
from decimal import Decimal
from datetime import datetime, timezone as dt_timezone

import numpy as np
from django.utils import timezone

from .models import MatchScore, AIProcessingLog
from resumes.models import Resume
from jobs.models import JobDescription
from jobs.utils.embedding import generate_embedding


MODEL_VERSION = "hybrid-explainable-v2.0"
DEFAULT_MATCHING_JOB_LIMIT = max(20, int(os.getenv("MATCHING_JOB_LIMIT", "100")))

STOPWORDS = {
    "a", "an", "and", "or", "the", "for", "with", "to", "of", "in", "on",
    "at", "by", "from", "using", "developer", "engineer", "specialist",
    "role", "job", "experience", "knowledge", "working",
}

SKILL_ALIAS_GROUPS = {
    "javascript": {"javascript", "js", "ecmascript"},
    "typescript": {"typescript", "ts"},
    "react": {"react", "reactjs", "react.js"},
    "nextjs": {"nextjs", "next.js"},
    "nodejs": {"nodejs", "node.js", "node"},
    "expressjs": {"expressjs", "express.js", "express"},
    "postgresql": {"postgresql", "postgres", "psql"},
    "mongodb": {"mongodb", "mongo", "mongo db"},
    "python": {"python", "python3"},
    "django": {"django", "django rest framework", "drf"},
    "machinelearning": {"machinelearning", "machine learning", "ml"},
    "deeplearning": {"deeplearning", "deep learning", "dl"},
    "artificialintelligence": {"artificialintelligence", "artificial intelligence", "ai"},
    "cplusplus": {"cplusplus", "c++", "cpp"},
    "csharp": {"csharp", "c#"},
    "dotnet": {"dotnet", ".net", "asp.net", "aspnet"},
    "aws": {"aws", "amazon web services"},
    "gcp": {"gcp", "google cloud platform", "google cloud"},
    "azure": {"azure", "microsoft azure"},
    "sql": {"sql", "mysql", "mssql", "sql server"},
    "htmlcss": {"htmlcss", "html css", "html", "css"},
}

SKILL_CANONICAL_MAP = {
    variant: canonical
    for canonical, variants in SKILL_ALIAS_GROUPS.items()
    for variant in variants
}


def clamp(value, minimum=0.0, maximum=1.0):
    return max(minimum, min(float(value), maximum))


def normalize_text(value):
    if not value:
        return ""

    text = str(value).lower().strip()
    replacements = {
        "c++": "cplusplus",
        "c#": "csharp",
        ".net": " dotnet ",
        "node.js": " nodejs ",
        "react.js": " react ",
        "next.js": " nextjs ",
        "express.js": " expressjs ",
        "machine learning": " machinelearning ",
        "deep learning": " deeplearning ",
        "artificial intelligence": " artificialintelligence ",
        "google cloud platform": " gcp ",
        "amazon web services": " aws ",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)

    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(value):
    return [
        token
        for token in normalize_text(value).split()
        if token and token not in STOPWORDS
    ]


def canonicalize_skill(value):
    normalized = normalize_text(value)
    return SKILL_CANONICAL_MAP.get(normalized, normalized)


def unique_non_empty(values):
    seen = set()
    ordered = []
    for value in values:
        cleaned = str(value or "").strip()
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        ordered.append(cleaned)
    return ordered


def safe_all(manager_or_none):
    if manager_or_none is None:
        return []
    try:
        return list(manager_or_none.all())
    except Exception:
        return []


def cosine_similarity(vec1, vec2):
    if vec1 is None or vec2 is None:
        return 0.0

    try:
        a = np.array(vec1, dtype=float)
        b = np.array(vec2, dtype=float)
    except (ValueError, TypeError):
        return 0.0

    if a.size == 0 or b.size == 0:
        return 0.0

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0

    try:
        return clamp(np.dot(a, b) / (norm_a * norm_b))
    except (ValueError, ZeroDivisionError):
        return 0.0


def phrase_similarity(left, right):
    left_norm = canonicalize_skill(left)
    right_norm = canonicalize_skill(right)

    if not left_norm or not right_norm:
        return 0.0

    if left_norm == right_norm:
        return 1.0

    if left_norm in right_norm or right_norm in left_norm:
        return 0.9

    left_tokens = set(tokenize(left_norm))
    right_tokens = set(tokenize(right_norm))
    if not left_tokens or not right_tokens:
        return 0.0

    intersection = left_tokens & right_tokens
    if not intersection:
        return 0.0

    jaccard = len(intersection) / len(left_tokens | right_tokens)
    containment = len(intersection) / min(len(left_tokens), len(right_tokens))
    return clamp(max(jaccard, containment * 0.85))


def split_technologies(value):
    if not value:
        return []
    return [part.strip() for part in re.split(r"[,/|]", str(value)) if part.strip()]


def build_job_matching_text(job):
    parts = [
        job.title,
        job.company,
        job.description,
        job.requirements,
        job.location,
        job.job_type,
        " ".join(job.skills.values_list("skill", flat=True)),
    ]
    if job.min_experience:
        parts.append(f"{job.min_experience} years experience")
    return "\n".join(str(part).strip() for part in parts if part)


def build_candidate_matching_text(candidate, resume=None, application=None):
    experiences = safe_all(getattr(resume, "experiences", None))
    projects = safe_all(getattr(resume, "projects", None))
    education = safe_all(getattr(resume, "education", None))
    skills = safe_all(getattr(resume, "skills", None))

    parts = [
        getattr(candidate, "full_name", ""),
        getattr(candidate, "summary", ""),
        getattr(resume, "raw_text", "") if resume else "",
        " ".join(skill.skill_name for skill in skills),
        " ".join(
            " ".join(filter(None, [experience.job_title, experience.company, experience.description]))
            for experience in experiences
        ),
        " ".join(
            " ".join(filter(None, [project.name, project.description, project.technologies]))
            for project in projects
        ),
        " ".join(
            " ".join(filter(None, [record.degree, record.field_of_study, record.institution]))
            for record in education
        ),
        getattr(application, "cover_letter", "") if application else "",
    ]
    return "\n".join(str(part).strip() for part in parts if part)


def ensure_job_embedding(job):
    try:
        if job.embedding is not None and len(job.embedding) > 0:
            return job.embedding
    except (TypeError, ValueError):
        pass

    job_text = build_job_matching_text(job)
    embedding = generate_embedding(job_text)
    if embedding and hasattr(embedding, "tolist"):
        embedding = embedding.tolist()
    if embedding:
        job.embedding = embedding
        job.save(update_fields=["embedding"])
    return embedding


def ensure_resume_embedding(candidate, resume=None, application=None):
    if resume is not None:
        try:
            if resume.embedding is not None and len(resume.embedding) > 0:
                return resume.embedding
        except (TypeError, ValueError):
            pass

    candidate_text = build_candidate_matching_text(candidate, resume=resume, application=application)
    if not candidate_text.strip():
        return None

    embedding = generate_embedding(candidate_text)
    if embedding and hasattr(embedding, "tolist"):
        embedding = embedding.tolist()

    if resume is not None and embedding:
        resume.embedding = embedding
        resume.save(update_fields=["embedding"])

    return embedding


def get_best_resume_for_candidate(candidate):
    resumes = [resume for resume in safe_all(candidate.resumes) if getattr(resume, "is_active", False)]
    if resumes:
        resumes.sort(
            key=lambda resume: (
                bool(getattr(resume, "is_primary", False)),
                getattr(resume, "uploaded_at", None) or datetime.min.replace(tzinfo=dt_timezone.utc),
                getattr(resume, "id", 0),
            ),
            reverse=True,
        )
        return resumes[0]

    queryset = candidate.resumes.filter(is_active=True).prefetch_related(
        "skills",
        "education",
        "experiences",
        "projects",
    ).order_by("-is_primary", "-uploaded_at", "-id")
    return queryset.first()


def collect_candidate_skills(candidate, resume=None, candidate_text=""):
    skills = []
    if resume is not None:
        skills.extend(skill.skill_name for skill in safe_all(getattr(resume, "skills", None)))
        for project in safe_all(getattr(resume, "projects", None)):
            skills.extend(split_technologies(project.technologies))

    normalized_text = normalize_text(candidate_text)
    for canonical, variants in SKILL_ALIAS_GROUPS.items():
        for variant in variants:
            if normalize_text(variant) in normalized_text:
                skills.append(canonical)
                break

    return unique_non_empty(skills)


def calculate_skill_match_details(job, candidate, resume=None, candidate_text=""):
    required_skills = unique_non_empty(job.skills.values_list("skill", flat=True))
    if not required_skills:
        return {
            "score": 0.6,
            "matched_skills": [],
            "missing_skills": [],
            "partial_matches": [],
            "required_skills": [],
            "candidate_skills": collect_candidate_skills(candidate, resume, candidate_text),
        }

    candidate_skills = collect_candidate_skills(candidate, resume, candidate_text)
    normalized_candidate_text = normalize_text(candidate_text)
    title_tokens = set(tokenize(job.title))
    requirement_tokens = set(tokenize(job.requirements or ""))

    matched_skills = []
    missing_skills = []
    partial_matches = []

    weighted_total = 0.0
    weighted_score = 0.0

    for required_skill in required_skills:
        required_tokens = set(tokenize(required_skill))
        weight = 1.35 if required_tokens & (title_tokens | requirement_tokens) else 1.0
        weighted_total += weight

        best_similarity = 0.0
        best_evidence = None

        for candidate_skill in candidate_skills:
            similarity = phrase_similarity(required_skill, candidate_skill)
            if similarity > best_similarity:
                best_similarity = similarity
                best_evidence = candidate_skill

        required_normalized = normalize_text(required_skill)
        if required_normalized and required_normalized in normalized_candidate_text and best_similarity < 0.78:
            best_similarity = 0.78
            best_evidence = required_skill

        weighted_score += weight * best_similarity

        if best_similarity >= 0.78:
            matched_skills.append({"required": required_skill, "matched_with": best_evidence or required_skill})
        elif best_similarity >= 0.45:
            partial_matches.append({"required": required_skill, "matched_with": best_evidence or required_skill})
        else:
            missing_skills.append(required_skill)

    return {
        "score": clamp(weighted_score / weighted_total if weighted_total else 0.0),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "partial_matches": partial_matches,
        "required_skills": required_skills,
        "candidate_skills": candidate_skills,
    }


def infer_candidate_experience_years(candidate, resume=None):
    if getattr(candidate, "total_experience_years", None) is not None:
        return float(candidate.total_experience_years)

    if resume is None:
        return 0.0

    total_months = 0
    for experience in safe_all(getattr(resume, "experiences", None)):
        if experience.duration_months:
            total_months += experience.duration_months
    return round(total_months / 12, 2) if total_months else 0.0


def calculate_experience_match_details(job, candidate, resume=None):
    required_experience = float(job.min_experience or 0)
    candidate_experience = infer_candidate_experience_years(candidate, resume=resume)

    if required_experience <= 0:
        score = 1.0 if candidate_experience > 0 else 0.75
    elif candidate_experience >= required_experience:
        score = 1.0
    elif candidate_experience <= 0:
        score = 0.0
    else:
        score = clamp((candidate_experience / required_experience) ** 0.75)

    return {
        "score": score,
        "candidate_experience": candidate_experience,
        "required_experience": required_experience,
        "gap_years": max(required_experience - candidate_experience, 0.0),
    }


def calculate_title_alignment_details(job, candidate, resume=None, application=None, candidate_text=""):
    comparison_texts = []

    if resume is not None:
        comparison_texts.extend(
            experience.job_title
            for experience in safe_all(getattr(resume, "experiences", None))
            if experience.job_title
        )
        comparison_texts.extend(
            project.name
            for project in safe_all(getattr(resume, "projects", None))
            if project.name
        )

    comparison_texts.extend([
        getattr(candidate, "summary", ""),
        getattr(application, "cover_letter", "") if application else "",
    ])

    best_score = 0.0
    matched_titles = []
    for text in comparison_texts:
        if not text:
            continue
        score = phrase_similarity(job.title, text)
        if score > best_score:
            best_score = score
        if score >= 0.6:
            matched_titles.append(text.strip())

    job_title_normalized = normalize_text(job.title)
    if job_title_normalized and job_title_normalized in normalize_text(candidate_text):
        best_score = max(best_score, 0.95)

    return {
        "score": clamp(best_score),
        "matched_titles": unique_non_empty(matched_titles)[:3],
    }


def calculate_education_match_details(job, resume=None):
    education_records = safe_all(getattr(resume, "education", None))
    job_text = normalize_text(f"{job.title} {job.requirements or ''} {job.description or ''}")
    degree_keywords = {
        "bachelor", "masters", "master", "degree", "btech", "mtech",
        "bsc", "msc", "be", "bs", "computer", "engineering", "science",
    }
    degree_required = any(keyword in job_text for keyword in degree_keywords)

    if not education_records:
        return {
            "score": 0.0 if degree_required else 0.45,
            "education_count": 0,
        }

    if not degree_required:
        return {
            "score": 0.8,
            "education_count": len(education_records),
        }

    relevant = False
    for record in education_records:
        text = normalize_text(
            f"{record.degree or ''} {record.field_of_study or ''} {record.institution or ''}"
        )
        if any(keyword in text for keyword in degree_keywords):
            relevant = True
            break

    return {
        "score": 1.0 if relevant else 0.7,
        "education_count": len(education_records),
    }


def calculate_application_relevance_details(job, application=None):
    if application is None or not application.cover_letter:
        return {"score": 0.4, "has_cover_letter": False}

    cover_letter = application.cover_letter
    title_similarity = phrase_similarity(job.title, cover_letter)
    job_skills = unique_non_empty(job.skills.values_list("skill", flat=True))
    normalized_cover_letter = normalize_text(cover_letter)
    skill_hits = 0
    for skill in job_skills:
        if normalize_text(skill) in normalized_cover_letter:
            skill_hits += 1

    skill_ratio = skill_hits / len(job_skills) if job_skills else 0.5
    score = clamp(0.25 + (0.4 * title_similarity) + (0.35 * skill_ratio))
    return {
        "score": score,
        "has_cover_letter": True,
    }


def calculate_semantic_score(job, candidate, resume=None, application=None):
    job_embedding = ensure_job_embedding(job)
    resume_embedding = ensure_resume_embedding(candidate, resume=resume, application=application)
    return cosine_similarity(resume_embedding, job_embedding)


def calculate_data_confidence(candidate, resume=None, application=None, candidate_text=""):
    signals = [
        1.0 if resume is not None else 0.0,
        1.0 if candidate_text.strip() else 0.0,
        1.0 if getattr(candidate, "summary", "") else 0.0,
        1.0 if infer_candidate_experience_years(candidate, resume=resume) > 0 else 0.0,
        1.0 if application and application.cover_letter else 0.0,
    ]
    return round(sum(signals) / len(signals), 4)


def build_strengths_and_concerns(skill_details, experience_details, title_details, semantic_score, application_details):
    strengths = []
    concerns = []

    required_skills = skill_details["required_skills"]
    matched_count = len(skill_details["matched_skills"])

    if required_skills and matched_count:
        strengths.append(f"Matched {matched_count}/{len(required_skills)} required skills")
    if not skill_details["missing_skills"] and required_skills:
        strengths.append("Covered all explicitly listed job skills")
    elif skill_details["missing_skills"]:
        concerns.append(f"Missing skills: {', '.join(skill_details['missing_skills'][:4])}")

    if experience_details["required_experience"] > 0:
        if experience_details["score"] >= 1.0:
            strengths.append("Experience meets or exceeds the job requirement")
        elif experience_details["gap_years"] > 0:
            concerns.append(
                f"Experience is about {round(experience_details['gap_years'], 1)} years below the target"
            )

    if title_details["score"] >= 0.7:
        strengths.append("Previous role titles align closely with this job")
    elif title_details["score"] < 0.3:
        concerns.append("Past role titles show weak alignment with this opening")

    if semantic_score >= 0.65:
        strengths.append("Resume language strongly aligns with the job description")
    elif semantic_score < 0.25:
        concerns.append("Overall resume context has low similarity to the job description")

    if application_details["has_cover_letter"] and application_details["score"] >= 0.65:
        strengths.append("Cover letter appears tailored to the role")

    return unique_non_empty(strengths)[:4], unique_non_empty(concerns)[:4]


def fit_label_for_score(score):
    if score >= 0.8:
        return "Excellent"
    if score >= 0.68:
        return "Strong"
    if score >= 0.52:
        return "Good"
    if score >= 0.35:
        return "Moderate"
    return "Weak"


def recommendation_for_score(score, skill_details, experience_details):
    if score >= 0.72 and len(skill_details["missing_skills"]) <= 1 and experience_details["score"] >= 0.7:
        return "shortlist"
    if score >= 0.55:
        return "review"
    if score >= 0.4:
        return "consider"
    return "low_fit"


def score_candidate_job_fit(job, candidate, resume=None, application=None, persist=False):
    candidate_text = build_candidate_matching_text(candidate, resume=resume, application=application)
    skill_details = calculate_skill_match_details(job, candidate, resume=resume, candidate_text=candidate_text)
    experience_details = calculate_experience_match_details(job, candidate, resume=resume)
    title_details = calculate_title_alignment_details(
        job,
        candidate,
        resume=resume,
        application=application,
        candidate_text=candidate_text,
    )
    education_details = calculate_education_match_details(job, resume=resume)
    application_details = calculate_application_relevance_details(job, application=application)
    semantic_score = calculate_semantic_score(job, candidate, resume=resume, application=application)
    confidence = calculate_data_confidence(candidate, resume=resume, application=application, candidate_text=candidate_text)

    weights = {
        "skills": 0.40,
        "semantic": 0.22,
        "experience": 0.16,
        "title": 0.10,
        "education": 0.05,
        "application": 0.07,
    }

    base_score = (
        (weights["skills"] * skill_details["score"]) +
        (weights["semantic"] * semantic_score) +
        (weights["experience"] * experience_details["score"]) +
        (weights["title"] * title_details["score"]) +
        (weights["education"] * education_details["score"]) +
        (weights["application"] * application_details["score"])
    )

    penalty_multiplier = 1.0
    if skill_details["required_skills"]:
        if skill_details["score"] < 0.25:
            penalty_multiplier *= 0.68
        elif skill_details["score"] < 0.50:
            penalty_multiplier *= 0.84

    if experience_details["required_experience"] > 0 and experience_details["score"] < 0.50:
        penalty_multiplier *= 0.84

    if title_details["score"] < 0.20 and semantic_score < 0.25:
        penalty_multiplier *= 0.90

    bonus = 0.0
    if skill_details["score"] >= 0.80 and semantic_score >= 0.60:
        bonus += 0.03
    if experience_details["score"] >= 1.0 and title_details["score"] >= 0.60:
        bonus += 0.02

    final_score = clamp(((base_score * penalty_multiplier) + bonus) * (0.90 + (0.10 * confidence)))
    strengths, concerns = build_strengths_and_concerns(
        skill_details,
        experience_details,
        title_details,
        semantic_score,
        application_details,
    )

    result = {
        "model_version": MODEL_VERSION,
        "final_score": final_score,
        "fit_label": fit_label_for_score(final_score),
        "recommendation": recommendation_for_score(final_score, skill_details, experience_details),
        "confidence": confidence,
        "weights": weights,
        "component_scores": {
            "skills": round(skill_details["score"], 4),
            "semantic": round(semantic_score, 4),
            "experience": round(experience_details["score"], 4),
            "title": round(title_details["score"], 4),
            "education": round(education_details["score"], 4),
            "application": round(application_details["score"], 4),
        },
        "evidence": {
            "matched_skills": skill_details["matched_skills"],
            "missing_skills": skill_details["missing_skills"],
            "partial_matches": skill_details["partial_matches"],
            "matched_titles": title_details["matched_titles"],
            "strengths": strengths,
            "concerns": concerns,
            "candidate_skills": skill_details["candidate_skills"],
        },
        "metrics": {
            "required_skills_count": len(skill_details["required_skills"]),
            "matched_skills_count": len(skill_details["matched_skills"]),
            "required_experience": experience_details["required_experience"],
            "candidate_experience": round(experience_details["candidate_experience"], 2),
            "experience_gap_years": round(experience_details["gap_years"], 2),
        },
    }

    if persist and resume is not None:
        MatchScore.objects.update_or_create(
            resume=resume,
            job=job,
            defaults={
                "score": Decimal(str(round(final_score, 4))),
                "created_at": timezone.now(),
            },
        )
        AIProcessingLog.objects.create(
            resume=resume,
            job=job,
            raw_score=Decimal(str(round(semantic_score, 4))),
            normalized_score=Decimal(str(round(final_score, 4))),
            model_version=MODEL_VERSION,
            processing_time_ms=0,
            processed_at=timezone.now(),
        )

    return result


def calculate_weighted_match_score(resume, job, application=None):
    result = score_candidate_job_fit(
        job,
        candidate=resume.candidate,
        resume=resume,
        application=application,
        persist=False,
    )
    components = {
        "skill_score": result["component_scores"]["skills"],
        "education_score": result["component_scores"]["education"],
        "experience_score": result["component_scores"]["experience"],
        "semantic_score": result["component_scores"]["semantic"],
        "title_score": result["component_scores"]["title"],
        "application_score": result["component_scores"]["application"],
        "weights": result["weights"],
        "confidence": result["confidence"],
        "evidence": result["evidence"],
        "metrics": result["metrics"],
        "fit_label": result["fit_label"],
        "recommendation": result["recommendation"],
        "model_version": result["model_version"],
    }
    return result["final_score"], components


def update_match_scores_for_resume(resume_id, persist=False, limit=None):
    resume = Resume.objects.select_related("candidate").prefetch_related(
        "skills",
        "education",
        "experiences",
        "projects",
    ).filter(id=resume_id).first()
    if not resume:
        return []

    max_jobs = limit or DEFAULT_MATCHING_JOB_LIMIT
    jobs = JobDescription.objects.filter(is_active=True).prefetch_related("skills")[:max_jobs]
    results = []

    for job in jobs:
        scoring = score_candidate_job_fit(job, candidate=resume.candidate, resume=resume, persist=persist)
        results.append({
            "job_id": job.id,
            "score": scoring["final_score"],
            "components": {
                "skill_score": scoring["component_scores"]["skills"],
                "education_score": scoring["component_scores"]["education"],
                "experience_score": scoring["component_scores"]["experience"],
                "semantic_score": scoring["component_scores"]["semantic"],
                "title_score": scoring["component_scores"]["title"],
                "application_score": scoring["component_scores"]["application"],
                "weights": scoring["weights"],
                "confidence": scoring["confidence"],
                "evidence": scoring["evidence"],
                "metrics": scoring["metrics"],
                "fit_label": scoring["fit_label"],
                "recommendation": scoring["recommendation"],
                "model_version": scoring["model_version"],
            },
        })

    results.sort(key=lambda item: item["score"], reverse=True)
    return results


def get_match_score_for_resume_and_job(resume_id, job_id):
    resume = Resume.objects.select_related("candidate").prefetch_related(
        "skills",
        "education",
        "experiences",
        "projects",
    ).filter(id=resume_id).first()
    if not resume:
        return None

    job = JobDescription.objects.filter(id=job_id, is_active=True).prefetch_related("skills").first()
    if not job:
        return None

    scoring = score_candidate_job_fit(job, candidate=resume.candidate, resume=resume, persist=True)

    return {
        "job_id": job.id,
        "resume_id": resume.id,
        "final_score": scoring["final_score"],
        "components": {
            "skill_score": scoring["component_scores"]["skills"],
            "education_score": scoring["component_scores"]["education"],
            "experience_score": scoring["component_scores"]["experience"],
            "semantic_score": scoring["component_scores"]["semantic"],
            "title_score": scoring["component_scores"]["title"],
            "application_score": scoring["component_scores"]["application"],
            "weights": scoring["weights"],
            "confidence": scoring["confidence"],
            "evidence": scoring["evidence"],
            "metrics": scoring["metrics"],
            "fit_label": scoring["fit_label"],
            "recommendation": scoring["recommendation"],
            "model_version": scoring["model_version"],
        },
    }


def rank_job_applications(job, applications, top_n=None):
    ranked = []

    for application in applications:
        candidate = application.candidate
        resume = get_best_resume_for_candidate(candidate)
        scoring = score_candidate_job_fit(
            job,
            candidate=candidate,
            resume=resume,
            application=application,
            persist=False,
        )

        ranked.append({
            "application": application,
            "resume": resume,
            "candidate": candidate,
            "score": scoring["final_score"],
            "score_percent": round(scoring["final_score"] * 100, 2),
            "fit_label": scoring["fit_label"],
            "recommendation": scoring["recommendation"],
            "confidence": scoring["confidence"],
            "model_version": scoring["model_version"],
            "component_scores": scoring["component_scores"],
            "weights": scoring["weights"],
            "evidence": scoring["evidence"],
            "metrics": scoring["metrics"],
        })

    ranked.sort(key=lambda item: (item["score"], -item["application"].id), reverse=True)
    return ranked[:top_n] if top_n is not None else ranked
