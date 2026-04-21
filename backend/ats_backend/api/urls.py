"""
Complete API URL configuration for all role-based endpoints
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from authentication.views import (
    login, register_candidate, create_organization_view, list_organizations_view, delete_organization_view,
    create_recruiter_view, list_active_recruiters_view, deactivate_recruiter_view,
    organization_settings_view, organization_invites_view,
    resend_organization_invite_view, revoke_organization_invite_view,
    platform_metrics_view, system_health_view, top_organizations_view,
    recent_activity_view, organization_status_view
)

from jobs.views import (
    JobViewSet, job_applications_view, job_candidates_view,
    public_jobs_view, job_detail_view, publish_job_view, close_job_view
)

from candidates.views import (
    CandidateViewSet, candidate_profile_view, candidate_applications_view,
    candidate_saved_jobs_view, update_candidate_profile_view, upload_resume_view,
    download_resume_view, search_candidates_view, get_candidate_matches_view
)

from applications.views import (
    ApplicationViewSet, application_detail_view, update_application_status_view,
    schedule_interview_view, send_offer_view, withdraw_application_view,
    bulk_update_applications_view, get_application_pipeline_view
)

from matching.views import (
    calculate_match_view, get_matched_candidates_view, batch_calculate_matches_view,
    get_top_matches_view, refresh_job_matches_view, get_match_details_view,
    update_match_score_view
)

from interviews.views import (
    InterviewViewSet, interview_detail_view, schedule_interview_view,
    reschedule_interview_view, cancel_interview_view, update_interview_feedback_view,
    get_interview_calendar_view, get_interview_statistics_view
)

from resumes.views import (
    parse_resume_view, extract_skills_view, analyze_resume_view,
    get_resume_text_view, upload_and_parse_resume_view, validate_resume_view
)

from analytics.views import (
    platform_metrics_view, organization_metrics_view, recruiter_metrics_view,
    hiring_funnel_view, application_trends_view, time_to_hire_view,
    source_effectiveness_view, skill_demand_view, export_analytics_view
)

from system.views import (
    system_health_view, system_logs_view, system_metrics_view,
    email_queue_view, cache_status_view, performance_metrics_view,
    security_audit_view, database_status_view
)

# Create routers for ViewSets
router = DefaultRouter()
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'candidates', CandidateViewSet, basename='candidate')
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'interviews', InterviewViewSet, basename='interview')

urlpatterns = [
    # Authentication endpoints
    path('auth/', include([
        path('login/', login, name='login'),
        path('register/', register_candidate, name='register'),
        # path('refresh/', refresh_view, name='refresh'),
        # path('logout/', logout_view, name='logout'),
    ])),
    
    # Super Admin endpoints
    path('admin/', include([
        path('organizations/', include([
            path('', list_organizations_view, name='list_organizations'),
            path('create/', create_organization_view, name='create_organization'),
            path('<uuid:organization_id>/delete/', delete_organization_view, name='delete_organization'),
            path('<uuid:organization_id>/status/', organization_status_view, name='organization_status'),
        ])),
        path('platform-metrics/', platform_metrics_view, name='platform_metrics'),
        path('system-health/', system_health_view, name='system_health'),
        path('top-organizations/', top_organizations_view, name='top_organizations'),
        path('recent-activity/', recent_activity_view, name='recent_activity'),
        path('system/', include([
            path('health/', system_health_view, name='system_health'),
            path('logs/', system_logs_view, name='system_logs'),
            path('metrics/', system_metrics_view, name='system_metrics'),
            path('email-queue/', email_queue_view, name='email_queue'),
            path('cache/', cache_status_view, name='cache_status'),
            path('performance/', performance_metrics_view, name='performance_metrics'),
            path('security-audit/', security_audit_view, name='security_audit'),
            path('database/', database_status_view, name='database_status'),
        ])),
    ])),
    
    # Organization Admin endpoints
    path('org/', include([
        path('team/', include([
            path('', list_active_recruiters_view, name='list_recruiters'),
            path('create/', create_recruiter_view, name='create_recruiter'),
            path('<uuid:user_id>/deactivate/', deactivate_recruiter_view, name='deactivate_recruiter'),
            path('invites/', include([
                path('', organization_invites_view, name='org_invites'),
                path('<uuid:invite_id>/resend/', resend_organization_invite_view, name='resend_invite'),
                path('<uuid:invite_id>/revoke/', revoke_organization_invite_view, name='revoke_invite'),
            ])),
        ])),
        path('settings/', include([
            path('', organization_settings_view, name='org_settings'),
        ])),
        path('analytics/', organization_metrics_view, name='org_metrics'),
    ])),
    
    # Recruiter endpoints
    path('recruiter/', include([
        path('applications/', include([
            path('<uuid:application_id>/', include([
                path('', application_detail_view, name='application_detail'),
                path('status/', update_application_status_view, name='update_application_status'),
                path('interview/', schedule_interview_view, name='schedule_interview'),
                path('offer/', send_offer_view, name='send_offer'),
                path('withdraw/', withdraw_application_view, name='withdraw_application'),
            ])),
            path('pipeline/', get_application_pipeline_view, name='application_pipeline'),
            path('bulk-update/', bulk_update_applications_view, name='bulk_update_applications'),
        ])),
        path('candidates/', include([
            path('search/', search_candidates_view, name='search_candidates'),
            path('<uuid:candidate_id>/', include([
                path('matches/', get_candidate_matches_view, name='candidate_matches'),
            ])),
        ])),
        path('analytics/', recruiter_metrics_view, name='recruiter_metrics'),
    ])),
    
    # Candidate endpoints
    path('candidate/', include([
        path('profile/', include([
            path('', candidate_profile_view, name='candidate_profile'),
            path('update/', update_candidate_profile_view, name='update_candidate_profile'),
            path('upload-resume/', upload_resume_view, name='upload_resume'),
            path('download-resume/', download_resume_view, name='download_resume'),
        ])),
        path('applications/', candidate_applications_view, name='candidate_applications'),
        path('saved-jobs/', candidate_saved_jobs_view, name='candidate_saved_jobs'),
    ])),
    
    # AI Matching endpoints
    path('matching/', include([
        path('calculate/', calculate_match_view, name='calculate_match'),
        path('candidates/<uuid:job_id>/', get_matched_candidates_view, name='matched_candidates'),
        path('batch/', batch_calculate_matches_view, name='batch_calculate_matches'),
        path('top/<uuid:job_id>/', get_top_matches_view, name='top_matches'),
        path('refresh/<uuid:job_id>/', refresh_job_matches_view, name='refresh_matches'),
        path('details/<uuid:match_id>/', get_match_details_view, name='match_details'),
        path('update/<uuid:match_id>/', update_match_score_view, name='update_match_score'),
    ])),
    
    # Resume processing endpoints
    path('resumes/', include([
        path('parse/', parse_resume_view, name='parse_resume'),
        path('extract-skills/', extract_skills_view, name='extract_skills'),
        path('analyze/', analyze_resume_view, name='analyze_resume'),
        path('text/<uuid:resume_id>/', get_resume_text_view, name='resume_text'),
        path('upload-parse/', upload_and_parse_resume_view, name='upload_parse_resume'),
        path('validate/', validate_resume_view, name='validate_resume'),
    ])),
    
    # Interview endpoints
    path('interviews/', include([
        path('<uuid:interview_id>/', include([
            path('', interview_detail_view, name='interview_detail'),
            path('schedule/', schedule_interview_view, name='schedule_interview'),
            path('reschedule/', reschedule_interview_view, name='reschedule_interview'),
            path('cancel/', cancel_interview_view, name='cancel_interview'),
            path('feedback/', update_interview_feedback_view, name='interview_feedback'),
        ])),
        path('calendar/', get_interview_calendar_view, name='interview_calendar'),
        path('statistics/', get_interview_statistics_view, name='interview_statistics'),
    ])),
    
    # Analytics endpoints
    path('analytics/', include([
        path('hiring-funnel/', hiring_funnel_view, name='hiring_funnel'),
        path('application-trends/', application_trends_view, name='application_trends'),
        path('time-to-hire/', time_to_hire_view, name='time_to_hire'),
        path('source-effectiveness/', source_effectiveness_view, name='source_effectiveness'),
        path('skill-demand/', skill_demand_view, name='skill_demand'),
        path('export/', export_analytics_view, name='export_analytics'),
    ])),
    
    # Public endpoints
    path('public/', include([
        path('jobs/', include([
            path('', public_jobs_view, name='public_jobs'),
            path('<uuid:job_id>/', job_detail_view, name='public_job_detail'),
        ])),
    ])),
    
    # File upload/download endpoints
    path('files/', include([
        path('upload/', upload_resume_view, name='file_upload'),
        path('download/<uuid:file_id>/', download_resume_view, name='file_download'),
    ])),
    
    # Router-based endpoints
    path('', include(router.urls)),
]

# API versioning
app_name = 'api'
