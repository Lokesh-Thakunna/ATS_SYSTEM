try:
    from celery import shared_task
except ImportError:  # pragma: no cover
    def shared_task(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from .processing import process_uploaded_resume


@shared_task(name="resumes.process_uploaded_resume")
def process_uploaded_resume_task(resume_id):
    return process_uploaded_resume(resume_id)
