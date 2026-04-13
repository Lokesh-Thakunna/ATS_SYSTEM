from authentication.models import OrganizationSettings

from .models import JobDescription


def get_publicly_hidden_organization_ids():
    return OrganizationSettings.objects.filter(
        allow_public_job_board=False,
    ).values_list("organization_id", flat=True)


def is_organization_publicly_visible(organization):
    if not organization:
        return False

    settings_obj = (
        OrganizationSettings.objects
        .filter(organization=organization)
        .only("allow_public_job_board")
        .first()
    )
    if settings_obj is None:
        return True
    return bool(settings_obj.allow_public_job_board)


def get_public_job_queryset(queryset=None):
    base_queryset = queryset if queryset is not None else JobDescription.objects.all()
    return base_queryset.filter(is_active=True).exclude(
        organization_id__in=get_publicly_hidden_organization_ids(),
    )


def is_job_publicly_visible(job):
    if not job or not getattr(job, "is_active", False):
        return False
    return is_organization_publicly_visible(job.organization)
