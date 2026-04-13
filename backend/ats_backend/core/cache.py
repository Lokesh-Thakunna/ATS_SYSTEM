"""
Redis caching service for AI matches and performance optimization
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import redis
from django.conf import settings
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder

logger = logging.getLogger(__name__)


class RedisCacheService:
    """Production-ready Redis caching service"""
    
    def __init__(self):
        self.redis_client = self._get_redis_client()
        self.default_ttl = 3600  # 1 hour
        self.key_prefix = getattr(settings, 'CACHE_KEY_PREFIX', 'ats:')
        
    def _get_redis_client(self):
        """Initialize Redis client"""
        try:
            redis_config = getattr(settings, 'REDIS', {})
            return redis.Redis(
                host=redis_config.get('HOST', 'localhost'),
                port=redis_config.get('PORT', 6379),
                db=redis_config.get('DB', 0),
                password=redis_config.get('PASSWORD'),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
        except Exception as e:
            logger.error(f"Redis connection failed: {str(e)}")
            # Fallback to Django cache
            return None
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        try:
            if self.redis_client:
                self.redis_client.ping()
                return True
        except Exception:
            pass
        return False
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cache value with TTL"""
        try:
            if self.redis_client:
                cache_key = f"{self.key_prefix}{key}"
                serialized_value = json.dumps(value, cls=DjangoJSONEncoder)
                return self.redis_client.setex(
                    cache_key, 
                    ttl or self.default_ttl, 
                    serialized_value
                )
            else:
                # Fallback to Django cache
                cache.set(key, value, ttl or self.default_ttl)
                return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get cache value"""
        try:
            if self.redis_client:
                cache_key = f"{self.key_prefix}{key}"
                value = self.redis_client.get(cache_key)
                if value:
                    return json.loads(value)
                return None
            else:
                # Fallback to Django cache
                return cache.get(key)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete cache key"""
        try:
            if self.redis_client:
                cache_key = f"{self.key_prefix}{key}"
                return bool(self.redis_client.delete(cache_key))
            else:
                # Fallback to Django cache
                cache.delete(key)
                return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern"""
        try:
            if self.redis_client:
                cache_pattern = f"{self.key_prefix}{pattern}"
                keys = self.redis_client.keys(cache_pattern)
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
            else:
                # Fallback to Django cache (limited pattern support)
                # This is a limitation of Django cache
                return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {str(e)}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            if self.redis_client:
                cache_key = f"{self.key_prefix}{key}"
                return bool(self.redis_client.exists(cache_key))
            else:
                # Fallback to Django cache
                return cache.has_key(key)
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {str(e)}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment numeric value"""
        try:
            if self.redis_client:
                cache_key = f"{self.key_prefix}{key}"
                return self.redis_client.incrby(cache_key, amount)
            else:
                # Fallback to Django cache (not atomic)
                current = cache.get(key, 0)
                new_value = current + amount
                cache.set(key, new_value, self.default_ttl)
                return new_value
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {str(e)}")
            return None
    
    def get_ttl(self, key: str) -> Optional[int]:
        """Get time to live for key"""
        try:
            if self.redis_client:
                cache_key = f"{self.key_prefix}{key}"
                return self.redis_client.ttl(cache_key)
            else:
                # Django cache doesn't expose TTL
                return None
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {str(e)}")
            return None


class AIMatchCache:
    """Specialized cache for AI matching results"""
    
    def __init__(self):
        self.cache_service = RedisCacheService()
        self.match_ttl = 86400  # 24 hours
        self.top_matches_ttl = 21600  # 6 hours
        
    def cache_match_result(self, job_id: str, candidate_id: str, match_data: Dict) -> bool:
        """Cache individual match result"""
        key = f"match:{job_id}:{candidate_id}"
        return self.cache_service.set(key, match_data, self.match_ttl)
    
    def get_match_result(self, job_id: str, candidate_id: str) -> Optional[Dict]:
        """Get cached match result"""
        key = f"match:{job_id}:{candidate_id}"
        return self.cache_service.get(key)
    
    def cache_top_matches(self, job_id: str, matches: List[Dict]) -> bool:
        """Cache top matches for a job"""
        key = f"top_matches:{job_id}"
        return self.cache_service.set(key, matches, self.top_matches_ttl)
    
    def get_top_matches(self, job_id: str) -> Optional[List[Dict]]:
        """Get cached top matches for a job"""
        key = f"top_matches:{job_id}"
        return self.cache_service.get(key)
    
    def cache_candidate_matches(self, candidate_id: str, matches: List[Dict]) -> bool:
        """Cache matches for a candidate"""
        key = f"candidate_matches:{candidate_id}"
        return self.cache_service.set(key, matches, self.match_ttl)
    
    def get_candidate_matches(self, candidate_id: str) -> Optional[List[Dict]]:
        """Get cached matches for a candidate"""
        key = f"candidate_matches:{candidate_id}"
        return self.cache_service.get(key)
    
    def invalidate_job_matches(self, job_id: str) -> bool:
        """Invalidate all match caches for a job"""
        patterns = [
            f"match:{job_id}:*",
            f"top_matches:{job_id}"
        ]
        deleted_count = 0
        for pattern in patterns:
            deleted_count += self.cache_service.delete_pattern(pattern)
        return deleted_count > 0
    
    def invalidate_candidate_matches(self, candidate_id: str) -> bool:
        """Invalidate all match caches for a candidate"""
        patterns = [
            f"*:{candidate_id}",
            f"candidate_matches:{candidate_id}"
        ]
        deleted_count = 0
        for pattern in patterns:
            deleted_count += self.cache_service.delete_pattern(pattern)
        return deleted_count > 0
    
    def cache_skill_analysis(self, text_hash: str, skills: List[str]) -> bool:
        """Cache skill extraction results"""
        key = f"skills:{text_hash}"
        return self.cache_service.set(key, skills, 86400)  # 24 hours
    
    def get_skill_analysis(self, text_hash: str) -> Optional[List[str]]:
        """Get cached skill extraction results"""
        key = f"skills:{text_hash}"
        return self.cache_service.get(key)
    
    def cache_embedding(self, content_hash: str, embedding: List[float]) -> bool:
        """Cache text embeddings"""
        key = f"embedding:{content_hash}"
        return self.cache_service.set(key, embedding, 604800)  # 7 days
    
    def get_embedding(self, content_hash: str) -> Optional[List[float]]:
        """Get cached text embeddings"""
        key = f"embedding:{content_hash}"
        return self.cache_service.get(key)


class AnalyticsCache:
    """Cache for analytics and metrics"""
    
    def __init__(self):
        self.cache_service = RedisCacheService()
        self.analytics_ttl = 1800  # 30 minutes
        self.metrics_ttl = 900  # 15 minutes
        
    def cache_platform_metrics(self, metrics: Dict) -> bool:
        """Cache platform-wide metrics"""
        key = "platform_metrics"
        return self.cache_service.set(key, metrics, self.analytics_ttl)
    
    def get_platform_metrics(self) -> Optional[Dict]:
        """Get cached platform metrics"""
        key = "platform_metrics"
        return self.cache_service.get(key)
    
    def cache_organization_metrics(self, org_id: str, metrics: Dict) -> bool:
        """Cache organization metrics"""
        key = f"org_metrics:{org_id}"
        return self.cache_service.set(key, metrics, self.analytics_ttl)
    
    def get_organization_metrics(self, org_id: str) -> Optional[Dict]:
        """Get cached organization metrics"""
        key = f"org_metrics:{org_id}"
        return self.cache_service.get(key)
    
    def cache_user_session(self, user_id: str, session_data: Dict) -> bool:
        """Cache user session data"""
        key = f"user_session:{user_id}"
        return self.cache_service.set(key, session_data, 3600)  # 1 hour
    
    def get_user_session(self, user_id: str) -> Optional[Dict]:
        """Get cached user session data"""
        key = f"user_session:{user_id}"
        return self.cache_service.get(key)
    
    def cache_job_stats(self, job_id: str, stats: Dict) -> bool:
        """Cache job statistics"""
        key = f"job_stats:{job_id}"
        return self.cache_service.set(key, stats, self.metrics_ttl)
    
    def get_job_stats(self, job_id: str) -> Optional[Dict]:
        """Get cached job statistics"""
        key = f"job_stats:{job_id}"
        return self.cache_service.get(key)
    
    def increment_view_count(self, resource_type: str, resource_id: str) -> Optional[int]:
        """Increment view count for resources"""
        key = f"views:{resource_type}:{resource_id}"
        return self.cache_service.increment(key)


class SearchCache:
    """Cache for search results"""
    
    def __init__(self):
        self.cache_service = RedisCacheService()
        self.search_ttl = 600  # 10 minutes
        
    def cache_search_results(self, search_query: str, results: List[Dict]) -> bool:
        """Cache search results"""
        # Create hash from search query for consistent key
        import hashlib
        query_hash = hashlib.md5(search_query.encode()).hexdigest()
        key = f"search:{query_hash}"
        return self.cache_service.set(key, results, self.search_ttl)
    
    def get_search_results(self, search_query: str) -> Optional[List[Dict]]:
        """Get cached search results"""
        import hashlib
        query_hash = hashlib.md5(search_query.encode()).hexdigest()
        key = f"search:{query_hash}"
        return self.cache_service.get(key)
    
    def cache_popular_searches(self, searches: List[str]) -> bool:
        """Cache popular search terms"""
        key = "popular_searches"
        return self.cache_service.set(key, searches, 3600)  # 1 hour
    
    def get_popular_searches(self) -> Optional[List[str]]:
        """Get cached popular search terms"""
        key = "popular_searches"
        return self.cache_service.get(key)


class PerformanceCache:
    """Cache for performance optimization"""
    
    def __init__(self):
        self.cache_service = RedisCacheService()
        self.performance_ttl = 300  # 5 minutes
        
    def cache_database_query(self, query_hash: str, results: Any) -> bool:
        """Cache database query results"""
        key = f"db_query:{query_hash}"
        return self.cache_service.set(key, results, self.performance_ttl)
    
    def get_database_query(self, query_hash: str) -> Optional[Any]:
        """Get cached database query results"""
        key = f"db_query:{query_hash}"
        return self.cache_service.get(key)
    
    def cache_api_response(self, endpoint: str, params: str, response: Dict) -> bool:
        """Cache API response"""
        key = f"api:{endpoint}:{hashlib.md5(params.encode()).hexdigest()}"
        return self.cache_service.set(key, response, self.performance_ttl)
    
    def get_api_response(self, endpoint: str, params: str) -> Optional[Dict]:
        """Get cached API response"""
        key = f"api:{endpoint}:{hashlib.md5(params.encode()).hexdigest()}"
        return self.cache_service.get(key)
    
    def cache_rate_limit(self, identifier: str, count: int, window: int) -> bool:
        """Cache rate limiting data"""
        key = f"rate_limit:{identifier}"
        return self.cache_service.set(key, {'count': count, 'window': window}, window)
    
    def get_rate_limit(self, identifier: str) -> Optional[Dict]:
        """Get rate limit data"""
        key = f"rate_limit:{identifier}"
        return self.cache_service.get(key)


# Global cache instances
ai_match_cache = AIMatchCache()
analytics_cache = AnalyticsCache()
search_cache = SearchCache()
performance_cache = PerformanceCache()
redis_cache = RedisCacheService()


# Cache warming functions
def warm_cache():
    """Warm up cache with frequently accessed data"""
    try:
        # Warm up platform metrics
        from analytics.services import get_platform_metrics
        metrics = get_platform_metrics()
        analytics_cache.cache_platform_metrics(metrics)
        
        # Warm up popular searches
        popular_searches = ['react developer', 'python engineer', 'data scientist']
        search_cache.cache_popular_searches(popular_searches)
        
        logger.info("Cache warming completed successfully")
        
    except Exception as e:
        logger.error(f"Cache warming failed: {str(e)}")


def invalidate_user_cache(user_id: str):
    """Invalidate all cache entries for a user"""
    patterns = [
        f"user_session:{user_id}",
        f"*:{user_id}",  # Matches involving user ID
        f"candidate_matches:{user_id}"
    ]
    
    deleted_count = 0
    for pattern in patterns:
        deleted_count += redis_cache.delete_pattern(pattern)
    
    logger.info(f"Invalidated {deleted_count} cache entries for user {user_id}")
    return deleted_count > 0


def invalidate_organization_cache(org_id: str):
    """Invalidate all cache entries for an organization"""
    patterns = [
        f"org_metrics:{org_id}",
        f"job_stats:*:{org_id}",  # Job stats for org
        f"top_matches:*:{org_id}"  # Top matches for org jobs
    ]
    
    deleted_count = 0
    for pattern in patterns:
        deleted_count += redis_cache.delete_pattern(pattern)
    
    logger.info(f"Invalidated {deleted_count} cache entries for organization {org_id}")
    return deleted_count > 0


# Cache monitoring
def get_cache_stats():
    """Get cache statistics for monitoring"""
    try:
        if redis_cache.is_available():
            info = redis_cache.redis_client.info()
            return {
                'redis_available': True,
                'used_memory': info.get('used_memory_human'),
                'used_memory_peak': info.get('used_memory_peak_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': _calculate_hit_rate(info)
            }
        else:
            return {
                'redis_available': False,
                'fallback_cache': 'django_cache'
            }
    except Exception as e:
        logger.error(f"Cache stats error: {str(e)}")
        return {'error': str(e)}


def _calculate_hit_rate(info):
    """Calculate cache hit rate"""
    hits = info.get('keyspace_hits', 0)
    misses = info.get('keyspace_misses', 0)
    total = hits + misses
    
    if total == 0:
        return 0.0
    
    return round((hits / total) * 100, 2)


# Cache cleanup
def cleanup_expired_cache():
    """Clean up expired cache entries"""
    try:
        if redis_cache.is_available():
            # Redis automatically handles expired keys, but we can clean up specific patterns
            patterns_to_clean = [
                "temp:*",
                "session:*",
                "rate_limit:*"
            ]
            
            total_deleted = 0
            for pattern in patterns_to_clean:
                deleted = redis_cache.delete_pattern(pattern)
                total_deleted += deleted
            
            logger.info(f"Cleaned up {total_deleted} expired cache entries")
            return total_deleted > 0
    except Exception as e:
        logger.error(f"Cache cleanup error: {str(e)}")
        return False
