import logging
from functools import lru_cache

from django.conf import settings
from supabase import create_client


logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_supabase_client():
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        logger.warning("Supabase credentials are not configured; local storage fallback will be used.")
        return None

    try:
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    except Exception as error:
        logger.error("Failed to initialize Supabase client: %s", error)
        return None
