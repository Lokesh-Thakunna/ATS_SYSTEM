from django.db import models
from resumes.models import Resume
from jobs.models import JobDescription


class MatchScore(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="match_scores")
    job = models.ForeignKey(JobDescription, on_delete=models.CASCADE, related_name="match_scores")

    score = models.DecimalField(max_digits=5, decimal_places=4)

    created_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = "match_scores"
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["resume", "job"], name="uniq_resume_job_match_score"),
            models.CheckConstraint(
                check=models.Q(score__gte=0) & models.Q(score__lte=1),
                name="match_score_between_zero_and_one",
            ),
        ]
        indexes = [
            models.Index(fields=["resume"], name="match_resume_idx"),
            models.Index(fields=["job"], name="match_job_idx"),
            models.Index(fields=["-score"], name="match_score_desc_idx"),
        ]

    def __str__(self):
        return f"Resume {self.resume_id} -> Job {self.job_id}: {self.score}"
    
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
