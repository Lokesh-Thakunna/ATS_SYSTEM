from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'

    def ready(self):
        from django.contrib.auth.models import User

        from .organization import get_user_organization

        if not hasattr(User, "organization"):
            User.add_to_class("organization", property(lambda user: get_user_organization(user)))

        if not hasattr(User, "organization_id"):
            User.add_to_class(
                "organization_id",
                property(lambda user: getattr(get_user_organization(user), "id", None)),
            )
