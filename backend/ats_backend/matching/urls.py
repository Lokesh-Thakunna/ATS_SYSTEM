from django.urls import path
from . import views

urlpatterns = [
    path('candidate/<int:candidate_id>/jobs/', views.match_jobs_for_candidate, name='match_jobs_for_candidate'),
    path('resume/<int:resume_id>/jobs/', views.match_jobs_for_resume, name='match_jobs_for_resume'),
    path('job/<int:job_id>/candidates/', views.match_candidates_for_job, name='match_candidates_for_job'),
    path('job/<int:job_id>/applicants/', views.match_applicants_for_job, name='match_applicants_for_job'),
    path('job/<int:job_id>/shortlist/', views.shortlist_top_candidates_for_job, name='shortlist_top_candidates_for_job'),
    path('resume/<int:resume_id>/job/<int:job_id>/', views.match_resume_to_job, name='match_resume_to_job'),
]
