import os

from django.contrib.postgres.fields import ArrayField
from django.db import models
from pgvector.django import VectorField
from django.contrib.auth.models import User
from candidates.models import Candidate
from django.core.exceptions import ValidationError


USE_PGVECTOR = os.getenv("USE_PGVECTOR", "false").lower() == "true"


class JobDescription(models.Model):
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="posted_jobs")
    # Organization keeps recruiter job boards isolated per tenant without
    # changing the existing recruiter ownership relation.
    organization = models.ForeignKey(
        "authentication.Organization",
        on_delete=models.PROTECT,
        related_name="jobs",
    )
    title = models.CharField(max_length=150)
    company = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    requirements = models.TextField(blank=True, null=True)

    location = models.CharField(max_length=200, blank=True, null=True)
    job_type = models.CharField(max_length=50, blank=True, null=True)

    salary_min = models.IntegerField(blank=True, null=True)

    salary_max = models.IntegerField(blank=True, null=True)

    min_experience = models.IntegerField(blank=True, null=True)

    # Keep production vector support, but allow tests/environments without pgvector extension.
    embedding = (
        VectorField(null=True, blank=True)
        if USE_PGVECTOR
        else ArrayField(models.FloatField(), null=True, blank=True)
    )

    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "job_descriptions"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["posted_by", "is_active"], name="job_owner_active_idx"),
            models.Index(fields=["is_active", "created_at"], name="job_active_created_idx"),
            models.Index(fields=["location"], name="job_location_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(salary_min__gte=0) | models.Q(salary_min__isnull=True),
                name="job_salary_min_non_negative",
            ),
            models.CheckConstraint(
                check=models.Q(salary_max__gte=0) | models.Q(salary_max__isnull=True),
                name="job_salary_max_non_negative",
            ),
            models.CheckConstraint(
                check=models.Q(min_experience__gte=0) | models.Q(min_experience__isnull=True),
                name="job_min_experience_non_negative",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(salary_min__isnull=True)
                    | models.Q(salary_max__isnull=True)
                    | models.Q(salary_max__gte=models.F("salary_min"))
                ),
                name="job_salary_range_valid",
            ),
        ]

    def clean(self):
        """Validate embedding before saving"""
        if self.embedding is not None:
            if not isinstance(self.embedding, list):
                raise ValidationError("Embedding must be a list or None")
            if len(self.embedding) == 0:
                self.embedding = None  # Convert empty list to None

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class JobSkill(models.Model):
    job = models.ForeignKey(JobDescription, on_delete=models.CASCADE ,related_name="skills")
    skill = models.CharField(max_length=100)

    def __str__(self):
        return self.skill

    class Meta:
        ordering = ["skill", "id"]
        constraints = [
            models.UniqueConstraint(fields=["job", "skill"], name="uniq_job_skill"),
        ]
        indexes = [
            models.Index(fields=["skill"], name="job_skill_name_idx"),
        ]


class JobApplication(models.Model):
    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        UNDER_REVIEW = "under_review", "Under Review"
        SHORTLISTED = "shortlisted", "Shortlisted"
        INTERVIEWED = "interviewed", "Interviewed"
        REJECTED = "rejected", "Rejected"
        HIRED = "hired", "Hired"

    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="applications")
    job = models.ForeignKey(JobDescription, on_delete=models.CASCADE, related_name="applications")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPLIED, db_index=True)

    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Additional application data
    cover_letter = models.TextField(blank=True, null=True)
    expected_salary = models.IntegerField(blank=True, null=True)
    available_from = models.DateField(blank=True, null=True)

    class Meta:
        db_table = "job_applications"
        ordering = ["-applied_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["candidate", "job"], name="uniq_candidate_job_application"),
            models.CheckConstraint(
                check=models.Q(expected_salary__gte=0) | models.Q(expected_salary__isnull=True),
                name="application_expected_salary_non_negative",
            ),
        ]
        indexes = [
            models.Index(fields=["job", "status"], name="app_job_status_idx"),
            models.Index(fields=["candidate", "status"], name="app_candidate_status_idx"),
            models.Index(fields=["applied_at"], name="app_applied_at_idx"),
        ]

    def __str__(self):
        return f"{self.candidate_id}:{self.job_id}:{self.status}"
