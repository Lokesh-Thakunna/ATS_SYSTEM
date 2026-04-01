# Generated migration for Candidate model resume fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='resume_file_name',
            field=models.CharField(blank=True, help_text="Original resume file name", max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='candidate',
            name='resume_url',
            field=models.TextField(blank=True, help_text="URL to candidate's resume stored in Supabase", null=True),
        ),
    ]
