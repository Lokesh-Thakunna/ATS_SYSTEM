import uuid
import os

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models
from pgvector.django import VectorField
from resumes.models import Resume
from jobs.models import JobDescription
from authentication.models import Organization

User = get_user_model()
USE_PGVECTOR = os.getenv("USE_PGVECTOR", "false").lower() == "true"


class MatchScore(models.Model):
    """Enhanced match scoring with explainable AI components"""
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="match_scores")
    job = models.ForeignKey(JobDescription, on_delete=models.CASCADE, related_name="match_scores")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="match_scores")
    
    # Overall scores
    total_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Overall match score (0-100)")
    fit_label = models.CharField(max_length=20, choices=[
        ('perfect', 'Perfect'),
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ])
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Confidence in match accuracy (0-100)")
    
    # Component scores (weighted scoring)
    skills_match_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Skills match score (0-100)")
    semantic_similarity_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Semantic similarity (0-100)")
    experience_fit_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Experience fit score (0-100)")
    job_title_match_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Job title match score (0-100)")
    education_match_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Education match score (0-100)")
    application_quality_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Application quality score (0-100)")
    
    # Detailed breakdown (JSON)
    skills_details = models.JSONField(default=dict, help_text="Detailed skills breakdown")
    semantic_details = models.JSONField(default=dict, help_text="Semantic similarity details")
    experience_details = models.JSONField(default=dict, help_text="Experience fit details")
    title_details = models.JSONField(default=dict, help_text="Job title match details")
    education_details = models.JSONField(default=dict, help_text="Education match details")
    application_details = models.JSONField(default=dict, help_text="Application quality details")
    
    # Explainable AI output
    strengths = models.JSONField(default=list, help_text="Candidate strengths")
    concerns = models.JSONField(default=list, help_text="Potential concerns")
    recommendations = models.JSONField(default=list, help_text="Recommendations")
    recommendation = models.TextField(help_text="Overall recommendation text")
    
    # Legacy compatibility
    score = models.DecimalField(max_digits=5, decimal_places=4, help_text="Legacy score (0-1)")

    created_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    last_calculated = models.DateTimeField(auto_now=True)
    calculation_version = models.CharField(max_length=20, default='2.0')

    class Meta:
        db_table = "match_scores"
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["resume", "job"], name="uniq_resume_job_match_score"),
            models.CheckConstraint(
                check=models.Q(total_score__gte=0) & models.Q(total_score__lte=100),
                name="total_score_between_zero_and_hundred",
            ),
            models.CheckConstraint(
                check=models.Q(confidence_score__gte=0) & models.Q(confidence_score__lte=100),
                name="confidence_score_between_zero_and_hundred",
            ),
            models.CheckConstraint(
                check=models.Q(score__gte=0) & models.Q(score__lte=1),
                name="match_score_between_zero_and_one",
            ),
        ]
        indexes = [
            models.Index(fields=["resume"], name="match_resume_idx"),
            models.Index(fields=["job"], name="match_job_idx"),
            models.Index(fields=["organization"], name="match_organization_idx"),
            models.Index(fields=["-total_score"], name="match_total_score_desc_idx"),
            models.Index(fields=["-score"], name="match_score_desc_idx"),
            models.Index(fields=["fit_label"], name="match_fit_label_idx"),
            models.Index(fields=["last_calculated"], name="match_last_calculated_idx"),
        ]

    def __str__(self):
        return f"Resume {self.resume_id} -> Job {self.job_id}: {self.total_score}% ({self.fit_label})"
    
class JobEmbedding(models.Model):
    """AI embeddings for job descriptions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.OneToOneField(JobDescription, on_delete=models.CASCADE, related_name='job_embedding')
    embedding = (
        VectorField(dimensions=768)
        if USE_PGVECTOR
        else ArrayField(models.FloatField(), size=768)
    )
    text_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'job_embeddings'
        indexes = [
            models.Index(fields=['job']),
        ]

    def __str__(self):
        return f"Job embedding for {self.job.id}"


class CandidateEmbedding(models.Model):
    """AI embeddings for candidate profiles"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, related_name='candidate_embedding')
    embedding = (
        VectorField(dimensions=768)
        if USE_PGVECTOR
        else ArrayField(models.FloatField(), size=768)
    )
    text_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'candidate_embeddings'
        indexes = [
            models.Index(fields=['resume']),
        ]

    def __str__(self):
        return f"Candidate embedding for {self.resume.id}"


class SkillAlias(models.Model):
    """Skill normalization and aliases"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    canonical_skill = models.CharField(max_length=100, help_text="Canonical skill name")
    alias = models.CharField(max_length=100, help_text="Skill alias")
    importance_weight = models.DecimalField(max_digits=3, decimal_places=2, default=1.0, help_text="Importance weight (0.1-5.0)")
    category = models.CharField(max_length=50, help_text="Skill category (e.g., programming, framework, tool)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'skill_aliases'
        unique_together = ['canonical_skill', 'alias']
        indexes = [
            models.Index(fields=['alias']),
            models.Index(fields=['canonical_skill']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.alias} -> {self.canonical_skill}"


class MatchingCache(models.Model):
    """Cache for frequently accessed match results"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cache_key = models.CharField(max_length=255, unique=True)
    cache_value = models.JSONField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'matching_cache'
        indexes = [
            models.Index(fields=['cache_key']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Cache {self.cache_key}"


class AIProcessingLog(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, null=True, blank=True, related_name="processing_logs")
    job = models.ForeignKey(JobDescription, on_delete=models.CASCADE, null=True, blank=True, related_name="processing_logs")

    raw_score = models.DecimalField(max_digits=5, decimal_places=4, null=True)
    normalized_score = models.DecimalField(max_digits=5, decimal_places=4, null=True)

    model_version = models.CharField(max_length=100, null=True)

    processing_time_ms = models.IntegerField(null=True)

    processed_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "ai_processing_logs"
        ordering = ["-processed_at", "-id"]
        constraints = [
            models.CheckConstraint(
                check=(models.Q(raw_score__gte=0) & models.Q(raw_score__lte=1)) | models.Q(raw_score__isnull=True),
                name="ai_log_raw_score_between_zero_and_one",
            ),
            models.CheckConstraint(
                check=(models.Q(normalized_score__gte=0) & models.Q(normalized_score__lte=1)) | models.Q(normalized_score__isnull=True),
                name="ai_log_normalized_score_between_zero_and_one",
            ),
            models.CheckConstraint(
                check=models.Q(processing_time_ms__gte=0) | models.Q(processing_time_ms__isnull=True),
                name="ai_log_processing_time_non_negative",
            ),
        ]
        indexes = [
            models.Index(fields=["resume"], name="ai_log_resume_idx"),
            models.Index(fields=["job"], name="ai_log_job_idx"),
            models.Index(fields=["processed_at"], name="ai_log_processed_at_idx"),
        ]

    def __str__(self):
        return f"AI log {self.id}"
