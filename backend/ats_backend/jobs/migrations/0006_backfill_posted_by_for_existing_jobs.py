from django.db import migrations


def backfill_posted_by_for_existing_jobs(apps, schema_editor):
    JobDescription = apps.get_model("jobs", "JobDescription")
    UserProfile = apps.get_model("authentication", "UserProfile")

    recruiter_user_ids = list(
        UserProfile.objects.filter(
            role="recruiter",
            user__is_active=True,
        ).values_list("user_id", flat=True)
    )

    if len(recruiter_user_ids) != 1:
        return

    JobDescription.objects.filter(posted_by__isnull=True).update(
        posted_by_id=recruiter_user_ids[0]
    )


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0001_initial"),
        ("jobs", "0005_jobdescription_posted_by"),
    ]

    operations = [
        migrations.RunPython(
            backfill_posted_by_for_existing_jobs,
            migrations.RunPython.noop,
        ),
    ]
