from django.urls import path
from .views import resolve_resume_access, serve_resume_file, upload_resume

urlpatterns = [
    path("upload/", upload_resume),
    path("<int:resume_id>/access/", resolve_resume_access, name="resume_access"),
    path("<int:resume_id>/file/", serve_resume_file, name="resume_file"),
]
