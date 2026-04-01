from django.urls import path
from .views import (
    create_job,
    get_jobs,
    get_recruiter_jobs,
    get_recruiter_applicants,
    get_job,
    update_job,
    delete_job,
    AddJobSkills,
    apply_for_job,
    get_my_applications,
    update_application_status,
)

urlpatterns = [

    # GET ALL JOBS
    path('', get_jobs),
    path('recruiter/mine/', get_recruiter_jobs),
    path('recruiter/applicants/', get_recruiter_applicants),

    # CREATE JOB
    path('create/', create_job),

    # GET SINGLE JOB
    path('<int:job_id>/', get_job),

    # UPDATE JOB
    path('update/<int:job_id>/', update_job),

    # DELETE JOB
    path('delete/<int:job_id>/', delete_job),

    # APPLY FOR JOB
    path('<int:job_id>/apply/', apply_for_job),

    # GET MY APPLICATIONS
    path('applications/', get_my_applications),
    path('applications/<int:application_id>/status/', update_application_status),

    # ADD SKILLS (optional)
    path('add-skills/', AddJobSkills.as_view()),
]
