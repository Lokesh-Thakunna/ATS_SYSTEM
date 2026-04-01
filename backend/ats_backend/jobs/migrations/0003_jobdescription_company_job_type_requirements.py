from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0002_alter_jobdescription_embedding'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobdescription',
            name='company',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='jobdescription',
            name='job_type',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='jobdescription',
            name='requirements',
            field=models.TextField(blank=True, null=True),
        ),
    ]
