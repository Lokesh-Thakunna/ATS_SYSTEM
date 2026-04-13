import uuid
import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz
from django.db import transaction
from django.core.cache import cache
from django.conf import settings
from celery import shared_task

from .models import (
    MatchScore, JobEmbedding, CandidateEmbedding,
    SkillAlias, MatchingCache, AIProcessingLog
)
from resumes.models import Resume
from jobs.models import JobDescription
from organizations.models import Organization

class AIMatchingEngine:
    """Production-level AI matching engine with explainable scoring"""

    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.skill_weights = self._load_skill_weights()

    def _load_skill_weights(self) -> Dict[str, float]:
        """Load skill importance weights from database"""
        weights = {}
        for alias in SkillAlias.objects.filter(is_active=True):
            weights[alias.canonical_skill.lower()] = float(alias.importance_weight)
        return weights

    def calculate_match_score(self, resume: Resume, job: JobDescription) -> Dict:
        """
        Calculate comprehensive match score with explainable AI breakdown

        Scoring Formula:
        Total Score = (Skills Match × 40%) + (Semantic Similarity × 22%) +
                     (Experience Fit × 16%) + (Job Title Match × 10%) +
                     (Education Match × 5%) + (Application Quality × 7%)
        """
        start_time = datetime.now()

        try:
            # Extract data
            resume_data = self._extract_resume_data(resume)
            job_data = self._extract_job_data(job)

            # Calculate component scores
            skills_result = self._calculate_skills_match(
                job_data['required_skills'],
                resume_data['skills']
            )

            semantic_result = self._calculate_semantic_similarity(
                job_data['text_content'],
                resume_data['text_content']
            )

            experience_result = self._calculate_experience_fit(
                job_data.get('experience_required', 0),
                resume_data.get('experience_years', 0)
            )

            title_result = self._calculate_title_match(
                job_data.get('title', ''),
                resume_data.get('current_title', '')
            )

            education_result = self._calculate_education_match(
                job_data.get('education_required', ''),
                resume_data.get('education', [])
            )

            application_result = self._calculate_application_quality(
                resume_data, resume
            )

            # Calculate weighted total score
            total_score = (
                skills_result['score'] * 0.40 +
                semantic_result['score'] * 0.22 +
                experience_result['score'] * 0.16 +
                title_result['score'] * 0.10 +
                education_result['score'] * 0.05 +
                application_result['score'] * 0.07
            )

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(resume_data)

            # Generate explainable AI output
            explainable_output = self._generate_explainable_output(
                skills_result, semantic_result, experience_result,
                title_result, education_result, application_result
            )

            # Determine fit label
            fit_label = self._get_fit_label(total_score)

            # Processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            result = {
                'total_score': round(total_score, 2),
                'fit_label': fit_label,
                'confidence_score': confidence_score,
                'skills_match_score': skills_result['score'],
                'semantic_similarity_score': semantic_result['score'],
                'experience_fit_score': experience_result['score'],
                'job_title_match_score': title_result['score'],
                'education_match_score': education_result['score'],
                'application_quality_score': application_result['score'],
                'skills_details': skills_result['details'],
                'semantic_details': semantic_result['details'],
                'experience_details': experience_result['details'],
                'title_details': title_result['details'],
                'education_details': education_result['details'],
                'application_details': application_result['details'],
                'strengths': explainable_output['strengths'],
                'concerns': explainable_output['concerns'],
                'recommendations': explainable_output['recommendations'],
                'recommendation': explainable_output['recommendation'],
                'processing_time_ms': int(processing_time)
            }

            # Log processing
            self._log_processing(resume, job, result)

            return result

        except Exception as e:
            # Log error and return default result
            self._log_processing_error(resume, job, str(e))
            return self._get_default_result()

    def _extract_resume_data(self, resume: Resume) -> Dict:
        """Extract and normalize resume data"""
        skills = []
        if resume.skills:
            skills = [self._normalize_skill(skill) for skill in resume.skills]

        return {
            'skills': skills,
            'text_content': resume.text_content or '',
            'experience_years': getattr(resume, 'experience_years', 0),
            'current_title': getattr(resume, 'current_title', ''),
            'education': getattr(resume, 'education', []),
            'has_resume': bool(resume.file_path),
            'skills_count': len(skills),
            'text_length': len(resume.text_content or '')
        }

    def _extract_job_data(self, job: JobDescription) -> Dict:
        """Extract and normalize job data"""
        skills = []
        if job.required_skills:
            skills = [self._normalize_skill(skill) for skill in job.required_skills]

        text_content = f"{job.title or ''} {job.description or ''} {job.requirements or ''}"

        return {
            'required_skills': skills,
            'text_content': text_content,
            'title': job.title or '',
            'experience_required': getattr(job, 'experience_required', 0),
            'education_required': getattr(job, 'education_required', '')
        }

    def _normalize_skill(self, skill: str) -> str:
        """Normalize skill name using aliases"""
        skill_lower = skill.lower().strip()

        # Check for aliases
        alias = SkillAlias.objects.filter(
            alias__iexact=skill_lower,
            is_active=True
        ).first()

        if alias:
            return alias.canonical_skill.lower()

        return skill_lower

    def _calculate_skills_match(self, required_skills: List[str], candidate_skills: List[str]) -> Dict:
        """Calculate skills match with weighted scoring"""
        if not required_skills:
            return {'score': 0, 'details': {'matched_skills': [], 'missing_skills': [], 'skill_coverage': '0/0'}}

        required_set = set(required_skills)
        candidate_set = set(candidate_skills)

        # Find matched and missing skills
        matched_skills = required_set & candidate_set
        missing_skills = required_set - candidate_set

        # Calculate weighted score
        total_weight = sum(self.skill_weights.get(skill, 1.0) for skill in required_skills)
        matched_weight = sum(self.skill_weights.get(skill, 1.0) for skill in matched_skills)

        score = (matched_weight / total_weight * 100) if total_weight > 0 else 0

        return {
            'score': round(score, 2),
            'details': {
                'matched_skills': list(matched_skills),
                'missing_skills': list(missing_skills),
                'skill_coverage': f"{len(matched_skills)}/{len(required_skills)} required skills matched",
                'total_required': len(required_skills),
                'total_matched': len(matched_skills)
            }
        }

    def _calculate_semantic_similarity(self, job_text: str, resume_text: str) -> Dict:
        """Calculate semantic similarity using embeddings"""
        if not job_text or not resume_text:
            return {'score': 0, 'details': {'contextual_match': 'Insufficient data'}}

        try:
            # Generate embeddings
            job_embedding = self.model.encode([job_text])
            resume_embedding = self.model.encode([resume_text])

            # Calculate cosine similarity
            similarity = cosine_similarity(job_embedding, resume_embedding)[0][0]

            # Convert to percentage (0-100)
            score = (similarity + 1) * 50

            return {
                'score': round(score, 2),
                'details': {
                    'contextual_match': 'Strong alignment' if score > 70 else 'Moderate alignment' if score > 50 else 'Weak alignment',
                    'similarity_value': round(similarity, 4),
                    'industry_fit': 'Technical domain match' if score > 60 else 'Partial domain match'
                }
            }

        except Exception as e:
            return {'score': 0, 'details': {'contextual_match': f'Error: {str(e)}'}}

    def _calculate_experience_fit(self, required_years: int, candidate_years: int) -> Dict:
        """Calculate experience fit with logarithmic scaling"""
        if required_years <= 0:
            return {'score': 100, 'details': {'required': 'Not specified', 'candidate': str(candidate_years), 'relevance': 'Not applicable'}}

        if candidate_years >= required_years:
            # Bonus for extra experience (capped)
            bonus = min(candidate_years - required_years, required_years) * 5
            score = min(100, 80 + bonus)
            relevance = f"{candidate_years} years (exceeds requirement)"
        else:
            # Penalty for insufficient experience
            ratio = candidate_years / required_years
            score = max(0, ratio * 80)
            relevance = f"{candidate_years} years (below requirement)"

        return {
            'score': round(score, 2),
            'details': {
                'required': f"{required_years} years",
                'candidate': f"{candidate_years} years",
                'relevance': relevance,
                'gap': max(0, required_years - candidate_years)
            }
        }

    def _calculate_title_match(self, job_title: str, candidate_title: str) -> Dict:
        """Calculate job title match using fuzzy matching"""
        if not job_title or not candidate_title:
            return {'score': 0, 'details': {'match_type': 'Insufficient data'}}

        # Normalize titles
        normalized_job = self._normalize_job_title(job_title)
        normalized_candidate = self._normalize_job_title(candidate_title)

        # Fuzzy matching
        similarity = fuzz.ratio(normalized_job, normalized_candidate)

        # Apply industry-specific mappings
        if self._is_title_variant(normalized_job, normalized_candidate):
            similarity = max(similarity, 85)

        return {
            'score': round(similarity, 2),
            'details': {
                'match_type': 'Strong match' if similarity > 80 else 'Partial match' if similarity > 60 else 'Weak match',
                'similarity_value': similarity,
                'job_title_normalized': normalized_job,
                'candidate_title_normalized': normalized_candidate
            }
        }

    def _normalize_job_title(self, title: str) -> str:
        """Normalize job title for comparison"""
        # Remove common prefixes/suffixes and normalize
        title = title.lower().strip()
        prefixes = ['senior', 'lead', 'principal', 'junior', 'associate']
        for prefix in prefixes:
            if title.startswith(prefix + ' '):
                title = title[len(prefix) + 1:]
        return title

    def _is_title_variant(self, job_title: str, candidate_title: str) -> bool:
        """Check if titles are variants of each other"""
        variants = {
            'software engineer': ['software developer', 'software engineer', 'full stack developer'],
            'product manager': ['product manager', 'product owner', 'product lead'],
            'data scientist': ['data scientist', 'data analyst', 'machine learning engineer']
        }

        for canonical, variant_list in variants.items():
            if job_title in variant_list and candidate_title in variant_list:
                return True
        return False

    def _calculate_education_match(self, required_education: str, candidate_education: List) -> Dict:
        """Calculate education match"""
        education_levels = {
            'high school': 1,
            'associate': 2,
            'bachelor': 3,
            'master': 4,
            'phd': 5
        }

        if not required_education:
            return {'score': 100, 'details': {'required': 'Not specified', 'candidate': str(candidate_education)}}

        required_level = education_levels.get(required_education.lower(), 0)
        candidate_level = 0

        for edu in candidate_education:
            if isinstance(edu, str):
                edu_level = education_levels.get(edu.lower(), 0)
                candidate_level = max(candidate_level, edu_level)

        if candidate_level >= required_level:
            score = 100
            match_type = 'Meets or exceeds requirement'
        else:
            score = (candidate_level / required_level) * 100 if required_level > 0 else 0
            match_type = 'Below requirement'

        return {
            'score': round(score, 2),
            'details': {
                'required': required_education,
                'candidate': str(candidate_education),
                'match_type': match_type
            }
        }

    def _calculate_application_quality(self, resume_data: Dict, resume: Resume) -> Dict:
        """Calculate application quality score"""
        scores = []

        # Resume completeness
        resume_score = self._calculate_resume_completeness(resume_data)
        scores.append(resume_score)

        # Profile completeness
        profile_score = self._calculate_profile_completeness(resume_data)
        scores.append(profile_score)

        # Content quality
        content_score = self._calculate_content_quality(resume_data)
        scores.append(content_score)

        avg_score = sum(scores) / len(scores)

        return {
            'score': round(avg_score, 2),
            'details': {
                'resume_completeness': resume_score,
                'profile_completeness': profile_score,
                'content_quality': content_score,
                'factors': {
                    'has_resume': resume_data['has_resume'],
                    'skills_count': resume_data['skills_count'],
                    'text_length': resume_data['text_length']
                }
            }
        }

    def _calculate_resume_completeness(self, resume_data: Dict) -> float:
        """Calculate resume completeness score"""
        score = 50  # Base score

        if resume_data['has_resume']:
            score += 20

        if resume_data['skills_count'] > 0:
            score += min(20, resume_data['skills_count'] * 2)

        if resume_data['text_length'] > 100:
            score += 10

        return min(100, score)

    def _calculate_profile_completeness(self, resume_data: Dict) -> float:
        """Calculate profile completeness score"""
        score = 60  # Base score

        if resume_data['experience_years'] > 0:
            score += 15

        if resume_data['current_title']:
            score += 15

        if resume_data['education']:
            score += 10

        return min(100, score)

    def _calculate_content_quality(self, resume_data: Dict) -> float:
        """Calculate content quality score"""
        score = 40  # Base score

        if resume_data['text_length'] > 500:
            score += 20
        elif resume_data['text_length'] > 200:
            score += 10

        if resume_data['skills_count'] >= 5:
            score += 20
        elif resume_data['skills_count'] >= 3:
            score += 10

        return min(100, score)

    def _calculate_confidence_score(self, resume_data: Dict) -> float:
        """Calculate confidence score based on data quality"""
        base_confidence = 70

        # Data quality factors
        if resume_data['has_resume']:
            base_confidence += 10

        if resume_data['skills_count'] >= 5:
            base_confidence += 10
        elif resume_data['skills_count'] >= 3:
            base_confidence += 5

        if resume_data['text_length'] > 300:
            base_confidence += 10

        return min(100, base_confidence)

    def _generate_explainable_output(self, *component_results) -> Dict:
        """Generate explainable AI output"""
        strengths = []
        concerns = []
        recommendations = []

        skills_result = component_results[0]
        semantic_result = component_results[1]
        experience_result = component_results[2]

        # Analyze strengths
        if skills_result['score'] > 80:
            strengths.append("Strong technical skills alignment")
        if experience_result['score'] > 80:
            strengths.append("Exceeds experience requirements")
        if semantic_result['score'] > 70:
            strengths.append("Strong contextual match")

        # Analyze concerns
        if skills_result['score'] < 60:
            missing_skills = skills_result['details'].get('missing_skills', [])
            if missing_skills:
                concerns.append(f"Missing key skills: {', '.join(missing_skills[:3])}")

        if experience_result['score'] < 60:
            concerns.append("Insufficient experience level")

        # Generate recommendations
        if skills_result['score'] < 80:
            recommendations.append("Assess skill gaps and learning ability")
        if experience_result['score'] < 70:
            recommendations.append("Consider potential vs experience")

        recommendation = self._generate_overall_recommendation(strengths, concerns)

        return {
            'strengths': strengths,
            'concerns': concerns,
            'recommendations': recommendations,
            'recommendation': recommendation
        }

    def _generate_overall_recommendation(self, strengths: List, concerns: List) -> str:
        """Generate overall recommendation text"""
        if len(strengths) >= 3 and len(concerns) == 0:
            return "Strong candidate with excellent fit - recommend immediate interview"
        elif len(strengths) >= 2 and len(concerns) <= 1:
            return "Good candidate with solid foundation - recommend screening"
        elif len(strengths) >= 1:
            return "Potential candidate - consider for review"
        else:
            return "Limited fit - may not meet requirements"

    def _get_fit_label(self, score: float) -> str:
        """Get fit label based on score"""
        if score >= 90:
            return 'perfect'
        elif score >= 80:
            return 'excellent'
        elif score >= 70:
            return 'good'
        elif score >= 60:
            return 'fair'
        else:
            return 'poor'

    def _log_processing(self, resume: Resume, job: JobDescription, result: Dict):
        """Log AI processing for monitoring"""
        AIProcessingLog.objects.create(
            resume=resume,
            job=job,
            raw_score=result['total_score'] / 100,
            normalized_score=result['total_score'] / 100,
            model_version='2.0',
            processing_time_ms=result.get('processing_time_ms', 0),
            processed_at=datetime.now()
        )

    def _log_processing_error(self, resume: Resume, job: JobDescription, error: str):
        """Log processing errors"""
        AIProcessingLog.objects.create(
            resume=resume,
            job=job,
            model_version='2.0',
            processed_at=datetime.now()
        )

    def _get_default_result(self) -> Dict:
        """Get default result for processing errors"""
        return {
            'total_score': 0,
            'fit_label': 'poor',
            'confidence_score': 0,
            'skills_match_score': 0,
            'semantic_similarity_score': 0,
            'experience_fit_score': 0,
            'job_title_match_score': 0,
            'education_match_score': 0,
            'application_quality_score': 0,
            'skills_details': {},
            'semantic_details': {},
            'experience_details': {},
            'title_details': {},
            'education_details': {},
            'application_details': {},
            'strengths': [],
            'concerns': ['Processing error occurred'],
            'recommendations': ['Manual review required'],
            'recommendation': 'Unable to process automatically',
            'processing_time_ms': 0
        }

# Global instance
matching_engine = AIMatchingEngine()

@shared_task
def calculate_match_score_async(resume_id: str, job_id: str):
    """Async task to calculate match score"""
    try:
        resume = Resume.objects.get(id=resume_id)
        job = JobDescription.objects.get(id=job_id)

        result = matching_engine.calculate_match_score(resume, job)

        # Save to database
        with transaction.atomic():
            MatchScore.objects.update_or_create(
                resume=resume,
                job=job,
                organization=job.organization,
                defaults=result
            )

        return result

    except Exception as e:
        # Log error and re-raise
        raise Exception(f"Match calculation failed: {str(e)}")

@shared_task
def batch_update_job_matches(job_id: str):
    """Update matches for all candidates for a specific job"""
    try:
        job = JobDescription.objects.get(id=job_id)
        resumes = Resume.objects.all()

        for resume in resumes:
            calculate_match_score_async.delay(str(resume.id), str(job.id))

        return f"Started batch processing for job {job_id}"

    except Exception as e:
        raise Exception(f"Batch update failed: {str(e)}")
