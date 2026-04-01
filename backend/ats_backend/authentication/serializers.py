from rest_framework import serializers
from django.contrib.auth.models import User


class CandidateRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)