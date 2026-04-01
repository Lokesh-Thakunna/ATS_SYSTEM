from django.db import models
from django.contrib.auth.models import User


class Candidate(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="candidate_profile",
    )
    full_name = models.CharField(max_length=150)
    email = models.EmailField(max_length=150, unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    total_experience_years = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)

    # Resume URL from Supabase (Candidate_resume bucket)
    resume_url = models.TextField(blank=True, null=True, help_text="URL to candidate's resume stored in Supabase")
    resume_file_name = models.CharField(max_length=255, blank=True, null=True, help_text="Original resume file name")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "candidates"
        ordering = ["-updated_at", "-id"]
        indexes = [
            models.Index(fields=["is_active", "updated_at"], name="cand_active_updated_idx"),
            models.Index(fields=["created_at"], name="cand_created_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(total_experience_years__gte=0) | models.Q(total_experience_years__isnull=True),
                name="candidate_experience_non_negative",
            ),
        ]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

    @classmethod
    def get_for_user(cls, user):
        candidate = cls.objects.filter(user=user).first()
        if candidate:
            return candidate
        return cls.objects.get(email=user.email)
