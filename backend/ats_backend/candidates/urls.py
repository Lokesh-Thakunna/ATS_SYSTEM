from django.urls import path
from .views import (
    get_candidate_profile,
    update_candidate_profile,
    create_or_update_candidate_profile,
    get_candidate_resumes
)

urlpatterns = [
    path("profile/", get_candidate_profile),
    path("profile/update/", update_candidate_profile),
    path("apply/", create_or_update_candidate_profile),  # For job applications
    path("resumes/", get_candidate_resumes),
]