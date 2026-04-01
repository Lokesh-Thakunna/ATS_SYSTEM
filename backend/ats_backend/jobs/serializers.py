from rest_framework import serializers
from .models import JobDescription, JobSkill, JobApplication


class JobDescriptionSerializer(serializers.ModelSerializer):
    company = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    type = serializers.CharField(source="job_type", required=False, allow_blank=True, allow_null=True)
    requirements = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    applicant_count = serializers.SerializerMethodField()

    skills = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )

    skills_list = serializers.SerializerMethodField()

    class Meta:
        model = JobDescription
        fields = [
            "id",
            "title",
            "company",
            "description",
            "requirements",
            "location",
            "type",
            "salary_min",
            "salary_max",
            "min_experience",
            "embedding",
            "skills",
            "skills_list",
            "applicant_count",
            "created_at",
        ]

        read_only_fields = ["embedding", "created_at", "applicant_count"]

    def get_skills_list(self, obj):
        skills = JobSkill.objects.filter(job=obj)
        return [skill.skill for skill in skills]

    def get_applicant_count(self, obj):
        return getattr(obj, "applicant_count", obj.applications.count())

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["skills"] = data.pop("skills_list", [])
        return data


    def create(self, validated_data):
        validated_data.setdefault('salary_min', 0)
        validated_data.setdefault('salary_max', 0)
        validated_data.setdefault('min_experience', 0)

        if validated_data.get('salary_min') is None:
            validated_data['salary_min'] = 0
        if validated_data.get('salary_max') is None:
            validated_data['salary_max'] = 0
        if validated_data.get('min_experience') is None:
            validated_data['min_experience'] = 0

        skills = validated_data.pop("skills", [])

        job = JobDescription.objects.create(**validated_data)

        for skill in skills:
            JobSkill.objects.create(
                job=job,
                skill=skill
            )

        return job


    def update(self, instance, validated_data):
        request = self.context.get("request")

        skills = request.data.get("skills")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if skills is not None:
            JobSkill.objects.filter(job=instance).delete()

            for skill in skills:
                JobSkill.objects.create(
                    job=instance,
                    skill=skill
                )

        return instance


class JobSkillSerializer(serializers.ModelSerializer):

    class Meta:
        model = JobSkill
        fields = "__all__"


class AddJobSkillsSerializer(serializers.Serializer):

    job_id = serializers.IntegerField()

    skills = serializers.ListField(
        child=serializers.CharField()
    )


class JobApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = [
            "id",
            "candidate",
            "job",
            "status",
            "applied_at",
            "updated_at",
            "cover_letter",
            "expected_salary",
            "available_from",
        ]
        read_only_fields = ["id", "status", "applied_at", "updated_at"]


class UpdateJobApplicationStatusSerializer(serializers.Serializer):
    status = serializers.CharField()

    def validate_status(self, value):
        normalized = str(value or "").strip().lower()
        aliases = {
            "review": JobApplication.Status.UNDER_REVIEW,
            "reviewing": JobApplication.Status.UNDER_REVIEW,
            "approved": JobApplication.Status.SHORTLISTED,
        }
        normalized = aliases.get(normalized, normalized)
        if normalized not in JobApplication.Status.values:
            raise serializers.ValidationError("Invalid application status")
        return normalized
