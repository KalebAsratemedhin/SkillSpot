"""
Cache key builders and TTLs for SkillSpot.
Use with django.core.cache.cache.
"""
import hashlib
from urllib.parse import urlencode

# TTLs in seconds
TAGS_LIST_TIMEOUT = 300   # 5 min – tags change rarely
JOB_LIST_TIMEOUT = 90    # 1.5 min – browse list changes more often


def _sorted_query_dict(request):
    """Build a stable key from request query params (sorted)."""
    params = request.query_params.dict()
    if not params:
        return ''
    return urlencode(sorted(params.items()))


def job_list_cache_key(request):
    """Cache key for paginated job list (browse, not my_jobs)."""
    q = _sorted_query_dict(request)
    h = hashlib.md5(q.encode(), usedforsecurity=False).hexdigest()
    return f"job_list:{h}"


def tags_list_cache_key(category=None):
    """Cache key for tags list, optionally filtered by category."""
    return f"tags_list:{category or 'all'}"


def invalidate_tags_list():
    """Clear all tags list cache variants (call when tags are created/updated/deleted)."""
    from django.core.cache import cache
    for cat in (None, "SKILL", "CERTIFICATION", "LANGUAGE"):
        cache.delete(tags_list_cache_key(cat))



