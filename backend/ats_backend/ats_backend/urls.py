"""
URL configuration for ats_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.views.generic import RedirectView

# Try to import API docs views, fallback if markdown not installed
try:
    from core.api_docs import api_documentation, api_docs_json
    HAS_API_DOCS = True
except ImportError:
    HAS_API_DOCS = False

# Import health check views
from core.health_checks import health_check, detailed_health_check


def home(request):
    return HttpResponse("ATS Backend Running")


urlpatterns = [
    # Health checks (must be first for monitoring)
    path('health/', health_check, name='health_check'),
    path('health', RedirectView.as_view(url='/health/', permanent=False)),
    path('health/detailed/', detailed_health_check, name='detailed_health_check'),
    path('health/detailed', RedirectView.as_view(url='/health/detailed/', permanent=False)),

    # API docs compatibility
    path('api/docs/', api_documentation, name='api_docs') if HAS_API_DOCS else path('api/docs/', lambda request: HttpResponse('API docs module missing or Markdown not installed', status=404)),
    path('api/docs', RedirectView.as_view(url='/api/docs/', permanent=False)),
    path('api/docs.json', api_docs_json, name='api_docs_json') if HAS_API_DOCS else path('api/docs.json', lambda request: HttpResponse('API docs module missing or Markdown not installed', status=404)),

    # API
    path('', home),
    path('admin/', admin.site.urls),
    path('api/resumes/', include('resumes.urls')),
    path('api/candidates/', include('candidates.urls')),
    path('api/jobs/', include('jobs.urls')),
    path('api/auth/', include('authentication.urls')),
    path('api/services/', include('services.parser.urls')),
    path('api/matching/', include('matching.urls')),
    # API Documentation
]


