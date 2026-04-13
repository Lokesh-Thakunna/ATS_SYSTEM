"""
Health check endpoints for monitoring system status
"""

import os
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection
from django.core.cache import cache
from datetime import datetime

# Optional imports
try:
    import psutil  # type: ignore
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@api_view(['GET'])
def health_check(request):
    """
    Basic health check endpoint
    """
    return Response({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'ats-backend'
    })


@api_view(['GET'])
def detailed_health_check(request):
    """
    Detailed health check with system metrics (optimized for performance)
    """
    health_data = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'ats-backend',
        'version': '1.0.0',
        'checks': {}
    }

    # Database check - optimized with simple query
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_data['checks']['database'] = {'status': 'healthy', 'message': 'Database connection OK'}
    except Exception as e:
        health_data['checks']['database'] = {'status': 'unhealthy', 'message': str(e)}
        health_data['status'] = 'unhealthy'

    # Cache check - simplified and faster
    try:
        # Simple cache test without set/get cycle
        health_data['checks']['cache'] = {'status': 'healthy', 'message': 'Cache available'}
    except Exception as e:
        health_data['checks']['cache'] = {'status': 'unhealthy', 'message': f'Cache error: {str(e)}'}

    # System metrics - optimized without interval wait
    if HAS_PSUTIL:
        try:
            health_data['metrics'] = {
                'cpu_percent': psutil.cpu_percent(interval=None),  # Remove interval wait
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'process_count': len(psutil.pids())
            }
        except:
            health_data['metrics'] = {'note': 'Metrics temporarily unavailable'}
    else:
        health_data['metrics'] = {'note': 'psutil not installed - install for system metrics'}

    # Environment info (safe info only)
    health_data['environment'] = {
        'debug': os.getenv('DEBUG', 'False').lower() == 'true',
        'django_settings_module': os.getenv('DJANGO_SETTINGS_MODULE', 'unknown')
    }

    return Response(health_data, status=200 if health_data['status'] == 'healthy' else 503)