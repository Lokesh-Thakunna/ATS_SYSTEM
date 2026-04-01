from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resumes', '0003_experience_project'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experience',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='project',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
