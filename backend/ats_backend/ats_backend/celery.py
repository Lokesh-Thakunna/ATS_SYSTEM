import os

try:
    from celery import Celery
except ImportError:  # pragma: no cover
    Celery = None


if Celery is not None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ats_backend.settings")

    app = Celery("ats_backend")
    app.config_from_object("django.conf:settings", namespace="CELERY")
    app.autodiscover_tasks()
else:  # pragma: no cover
    class _FallbackCeleryApp:
        def task(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

    app = _FallbackCeleryApp()
