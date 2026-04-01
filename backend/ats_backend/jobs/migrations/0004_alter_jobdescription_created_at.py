from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0003_jobdescription_company_job_type_requirements'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobdescription',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
