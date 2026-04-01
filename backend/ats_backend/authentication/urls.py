from django.urls import path
from .views import (
    register_candidate,
    register_recruiter,
    login,
    create_recruiter_view,
    list_active_recruiters_view,
    deactivate_recruiter_view
)

urlpatterns = [
    path('register/', register_candidate),
    path('register/recruiter/', register_recruiter),
    path('login/', login),
    path('recruiters/', list_active_recruiters_view),
    path('recruiter/create/', create_recruiter_view),
    path('recruiter/deactivate/<int:user_id>/', deactivate_recruiter_view),
]
