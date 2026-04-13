# core/cache_keys.py
"""
Centralized cache key management for ATS system.
Ensures consistent cache key naming across the application.
"""


class CacheKeys:
    """Cache key constants and builders"""
    
    # Organization Cache Keys
    ORG_BY_SLUG = 'ats:org:slug:{slug}'
    ORG_SETTINGS = 'ats:org:settings:{org_id}'
    ORG_DETAILS = 'ats:org:details:{org_id}'
    ORG_LIST_ADMIN = 'ats:org:list:admin:{admin_id}'
    
    # User Cache Keys
    USER_PROFILE = 'ats:user:profile:{user_id}'
    USER_ORG = 'ats:user:org:{user_id}'
    USER_ROLE = 'ats:user:role:{user_id}'
    USER_PERMISSIONS = 'ats:user:perms:{user_id}:{org_id}'
    
    # Job Cache Keys
    JOB_DETAIL = 'ats:job:detail:{job_id}'
    JOB_LIST_ORG = 'ats:job:list:org:{org_id}:page:{page}'
    JOB_SKILLS = 'ats:job:skills:{job_id}'
    JOB_APPLICANT_COUNT = 'ats:job:applicants:{job_id}'
    
    # Candidate Cache Keys
    CANDIDATE_DETAIL = 'ats:candidate:detail:{candidate_id}'
    CANDIDATE_RESUME = 'ats:candidate:resume:{candidate_id}'
    
    # Application Cache Keys
    APPLICATION_DETAIL = 'ats:app:detail:{app_id}'
    APPLICATION_LIST = 'ats:app:list:job:{job_id}:page:{page}'
    
    # JWT/Session Cache Keys
    JWT_VALIDATED = 'ats:jwt:validated:{token_hash}'
    SESSION_USER = 'ats:session:user:{session_id}'
    
    # Invite Cache Keys
    INVITE_TOKEN = 'ats:invite:token:{token}'
    INVITE_LIST_ORG = 'ats:invite:list:org:{org_id}'
    
    @staticmethod
    def get_org_key(slug):
        """Get cache key for organization by slug"""
        return CacheKeys.ORG_BY_SLUG.format(slug=slug)
    
    @staticmethod
    def get_org_settings_key(org_id):
        """Get cache key for organization settings"""
        return CacheKeys.ORG_SETTINGS.format(org_id=org_id)
    
    @staticmethod
    def get_user_org_key(user_id):
        """Get cache key for user's organization"""
        return CacheKeys.USER_ORG.format(user_id=user_id)
    
    @staticmethod
    def get_user_profile_key(user_id):
        """Get cache key for user profile"""
        return CacheKeys.USER_PROFILE.format(user_id=user_id)
    
    @staticmethod
    def get_job_list_key(org_id, page=1):
        """Get cache key for job list"""
        return CacheKeys.JOB_LIST_ORG.format(org_id=org_id, page=page)
    
    @staticmethod
    def get_job_detail_key(job_id):
        """Get cache key for job detail"""
        return CacheKeys.JOB_DETAIL.format(job_id=job_id)
    
    @staticmethod
    def get_candidate_key(candidate_id):
        """Get cache key for candidate"""
        return CacheKeys.CANDIDATE_DETAIL.format(candidate_id=candidate_id)
    
    @staticmethod
    def get_application_list_key(job_id, page=1):
        """Get cache key for application list"""
        return CacheKeys.APPLICATION_LIST.format(job_id=job_id, page=page)
    
    @staticmethod
    def get_jwt_token_key(token):
        """Get cache key for JWT token validation"""
        import hashlib
        token_hash = hashlib.md5(token.encode()).hexdigest()
        return CacheKeys.JWT_VALIDATED.format(token_hash=token_hash)
    
    @staticmethod
    def get_invite_token_key(token):
        """Get cache key for invite token"""
        return CacheKeys.INVITE_TOKEN.format(token=token)
    
    @staticmethod
    def invalidate_org_keys(org_id, slug=None):
        """Invalidate all org-related cache keys"""
        from django.core.cache import cache
        
        keys_to_delete = [
            CacheKeys.ORG_DETAILS.format(org_id=org_id),
            CacheKeys.ORG_SETTINGS.format(org_id=org_id),
            CacheKeys.JOB_LIST_ORG.format(org_id=org_id, page='*'),
        ]
        
        if slug:
            keys_to_delete.append(CacheKeys.ORG_BY_SLUG.format(slug=slug))
        
        cache.delete_many(keys_to_delete)
    
    @staticmethod
    def invalidate_user_keys(user_id):
        """Invalidate all user-related cache keys"""
        from django.core.cache import cache
        
        keys_to_delete = [
            CacheKeys.USER_PROFILE.format(user_id=user_id),
            CacheKeys.USER_ORG.format(user_id=user_id),
            CacheKeys.USER_ROLE.format(user_id=user_id),
        ]
        
        cache.delete_many(keys_to_delete)
    
    @staticmethod
    def invalidate_job_keys(job_id):
        """Invalidate all job-related cache keys"""
        from django.core.cache import cache
        
        keys_to_delete = [
            CacheKeys.JOB_DETAIL.format(job_id=job_id),
            CacheKeys.JOB_SKILLS.format(job_id=job_id),
            CacheKeys.JOB_APPLICANT_COUNT.format(job_id=job_id),
        ]
        
        cache.delete_many(keys_to_delete)
