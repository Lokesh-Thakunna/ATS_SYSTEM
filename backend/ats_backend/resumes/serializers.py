from rest_framework import serializers


class ResumeUploadSerializer(serializers.Serializer):
    candidate_id = serializers.IntegerField(required=False)
    resume = serializers.FileField()

