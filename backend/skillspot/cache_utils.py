"""
Cache key builders and TTLs for SkillSpot.
Use with django.core.cache.cache.
"""
import hashlib
from urllib.parse import urlencode

# TTLs in seconds
TAGS_LIST_TIMEOUT = 300   # 5 min – tags change rarely
JOB_LIST_TIMEOUT = 90     # 1.5 min – browse list changes more often
PROVIDER_LIST_TIMEOUT = 90   # 1.5 min – public provider directory


def _sorted_query_dict(request):
    """Build a stable key from request query params (sorted)."""
    params = request.query_params.dict()
    if not params:
        return ''
    return urlencode(sorted(params.items()))


def job_list_cache_key(request):
    """Cache key for paginated public job list (not my_jobs).

    Anonymous: job_list:anon:{query_hash}
    Authenticated: job_list:{user_id}:{query_hash} (my_application is per-user)
    """
    q = _sorted_query_dict(request)
    h = hashlib.md5(q.encode(), usedforsecurity=False).hexdigest()
    user = getattr(request, 'user', None)
    if user is not None and getattr(user, 'is_authenticated', False):
        user_id = getattr(user, 'id', None) or 'auth'
    else:
        user_id = 'anon'
    return f"job_list:{user_id}:{h}"


def provider_list_cache_key(request):
    """Cache key for public provider directory list (anonymous-safe)."""
    q = _sorted_query_dict(request)
    h = hashlib.md5(q.encode(), usedforsecurity=False).hexdigest()
    return f"provider_list:{h}"


def _tags_list_generation():
    from django.core.cache import cache
    gen = cache.get('tags_list_gen')
    if gen is None:
        cache.set('tags_list_gen', 1, timeout=None)
        return 1
    return int(gen)


def tags_list_cache_key(request):
    """Cache key for paginated tags list (category + page/page_size in query)."""
    q = _sorted_query_dict(request)
    h = hashlib.md5(q.encode(), usedforsecurity=False).hexdigest() if q else 'default'
    return f"tags_list:g{_tags_list_generation()}:{h}"


def invalidate_tags_list():
    """Invalidate all tags list pages by bumping generation."""
    from django.core.cache import cache
    try:
        cache.incr('tags_list_gen')
    except ValueError:
        cache.set('tags_list_gen', 1, timeout=None)
