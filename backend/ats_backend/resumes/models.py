from django.db import models
from pgvector.django import VectorField
from candidates.models import Candidate
from django.core.exceptions import ValidationError


class Resume(models.Model):
    class StorageBackend(models.TextChoices):
        SUPABASE = "supabase", "Supabase"
        LOCAL = "local", "Local"

    class ParsingStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="resumes"
    )

    file_name = models.CharField(max_length=255)

    cloud_url = models.TextField(blank=True, null=True)
    storage_backend = models.CharField(
        max_length=20,
        choices=StorageBackend.choices,
        default=StorageBackend.SUPABASE,
        db_index=True,
    )
    storage_path = models.CharField(max_length=500, blank=True, null=True)
    checksum_sha256 = models.CharField(max_length=64, blank=True, null=True, db_index=True)

    file_size = models.PositiveIntegerField(blank=True, null=True)

    mime_type = models.CharField(max_length=100, blank=True, null=True)

    raw_text = models.TextField(blank=True, null=True)

    embedding = VectorField(null=True, blank=True)

    parsing_status = models.CharField(
        max_length=50,
        choices=ParsingStatus.choices,
        blank=True,
        null=True,
        db_index=True,
    )

    parsing_error = models.TextField(blank=True, null=True)

    parsed_at = models.DateTimeField(blank=True, null=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    category = models.CharField(max_length=50, blank=True, null=True)
    is_primary = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "resumes"
        ordering = ["-uploaded_at", "-id"]
        indexes = [
            models.Index(fields=["candidate", "is_active"], name="resume_candidate_active_idx"),
            models.Index(fields=["candidate", "uploaded_at"], name="resume_candidate_uploaded_idx"),
            models.Index(fields=["parsing_status"], name="resume_parsing_status_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(file_size__gte=0) | models.Q(file_size__isnull=True),
                name="resume_file_size_non_negative",
            ),
            models.UniqueConstraint(
                fields=["candidate"],
                condition=models.Q(is_primary=True, is_active=True),
                name="uniq_active_primary_resume_per_candidate",
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
        return self.file_name


class Skill(models.Model):

    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="skills"
    )

    skill_name = models.CharField(max_length=150)

    skill_category = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "skills"
        ordering = ["skill_name", "id"]
        indexes = [
            models.Index(fields=["skill_name"], name="resume_skill_name_idx"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["resume", "skill_name"], name="uniq_resume_skill_name"),
        ]

    def __str__(self):
        return self.skill_name


class Education(models.Model):

    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="education"
    )

    degree = models.CharField(max_length=150, blank=True, null=True)

    institution = models.CharField(max_length=200, blank=True, null=True)

    field_of_study = models.CharField(max_length=150, blank=True, null=True)

    start_year = models.IntegerField(blank=True, null=True)

    end_year = models.IntegerField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "education"
        ordering = ["-end_year", "-start_year", "-id"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_year__gte=models.F("start_year")) | models.Q(end_year__isnull=True) | models.Q(start_year__isnull=True),
                name="education_year_range_valid",
            ),
        ]

    def __str__(self):
        return f"{self.degree} from {self.institution}"


class Experience(models.Model):
    id = models.AutoField(primary_key=True)

    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="experiences"
    )

    job_title = models.CharField(max_length=150, blank=True, null=True)

    company = models.CharField(max_length=200, blank=True, null=True)

    start_date = models.DateField(blank=True, null=True)

    end_date = models.DateField(blank=True, null=True)

    is_current = models.BooleanField(default=False)

    description = models.TextField(blank=True, null=True)

    duration_months = models.IntegerField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "experiences"
        ordering = ['-start_date']
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gte=models.F("start_date")) | models.Q(end_date__isnull=True) | models.Q(start_date__isnull=True),
                name="experience_date_range_valid",
            ),
            models.CheckConstraint(
                check=models.Q(duration_months__gte=0) | models.Q(duration_months__isnull=True),
                name="experience_duration_non_negative",
            ),
        ]

    def __str__(self):
        return f"{self.job_title} at {self.company}"


class Project(models.Model):
    id = models.AutoField(primary_key=True)

    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="projects"
    )

    name = models.CharField(max_length=200)

    description = models.TextField(blank=True, null=True)

    technologies = models.TextField(blank=True, null=True)  # Comma-separated

    start_date = models.DateField(blank=True, null=True)

    end_date = models.DateField(blank=True, null=True)

    project_url = models.URLField(blank=True, null=True)

    is_current = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects"
        ordering = ['-start_date']
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gte=models.F("start_date")) | models.Q(end_date__isnull=True) | models.Q(start_date__isnull=True),
                name="project_date_range_valid",
            ),
        ]

    def __str__(self):
        return self.name
