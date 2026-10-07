"""
User presence: Redis for live online, Profile.last_seen_at when offline.

Connection refcount so inbox + chat (or multiple tabs) share one online state.
Short grace on last disconnect avoids flicker on refresh.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone as dt_timezone

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

logger = logging.getLogger(__name__)

PRESENCE_TTL_SECONDS = 90
OFFLINE_GRACE_SECONDS = 12

_redis = None


def _client():
    global _redis
    if _redis is None:
        import redis

        _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


def _conns_key(user_id) -> str:
    return f'presence:conns:{user_id}'


def _online_key(user_id) -> str:
    return f'presence:online:{user_id}'


def _generation_key(user_id) -> str:
    return f'presence:gen:{user_id}'


def is_online(user_id) -> bool:
    try:
        return bool(_client().exists(_online_key(user_id)))
    except Exception:
        logger.exception('presence is_online failed for %s', user_id)
        return False


def get_last_seen_at(user) -> datetime | None:
    profile = getattr(user, 'profile', None)
    if profile is None:
        return None
    return profile.last_seen_at


def presence_payload(user_id, *, online: bool, last_seen_at=None) -> dict:
    ts = None
    if not online and last_seen_at is not None:
        if isinstance(last_seen_at, str):
            parsed = parse_datetime(last_seen_at)
            last_seen_at = parsed
        if last_seen_at is not None:
            if timezone.is_naive(last_seen_at):
                last_seen_at = timezone.make_aware(last_seen_at, dt_timezone.utc)
            ts = last_seen_at.isoformat()
    return {
        'type': 'presence_update',
        'user_id': str(user_id),
        'is_online': bool(online),
        'last_seen_at': ts,
    }


def register_connection(user_id, connection_id: str) -> bool:
    """
    Add a socket to the user's connection set.
    Returns True if this transitioned the user to online (0 → 1).
    """
    r = _client()
    key = _conns_key(user_id)
    pipe = r.pipeline()
    pipe.sadd(key, connection_id)
    pipe.scard(key)
    pipe.expire(key, PRESENCE_TTL_SECONDS)
    pipe.set(_online_key(user_id), '1', ex=PRESENCE_TTL_SECONDS)
    # Bump generation so any pending offline-grace task aborts.
    pipe.incr(_generation_key(user_id))
    pipe.expire(_generation_key(user_id), PRESENCE_TTL_SECONDS * 2)
    results = pipe.execute()
    count = int(results[1] or 0)
    return count == 1


def unregister_connection(user_id, connection_id: str) -> tuple[bool, int]:
    """
    Remove a socket. Returns (became_fully_offline, generation_at_disconnect).
    Caller should wait grace then finalize if still offline at same/ later gen check.
    """
    r = _client()
    key = _conns_key(user_id)
    pipe = r.pipeline()
    pipe.srem(key, connection_id)
    pipe.scard(key)
    results = pipe.execute()
    count = int(results[1] or 0)
    gen = int(r.get(_generation_key(user_id)) or 0)
    if count <= 0:
        r.delete(key)
        return True, gen
    r.expire(key, PRESENCE_TTL_SECONDS)
    r.expire(_online_key(user_id), PRESENCE_TTL_SECONDS)
    return False, gen


def touch_connection(user_id, connection_id: str) -> None:
    """Refresh TTLs (optional heartbeat)."""
    r = _client()
    key = _conns_key(user_id)
    if r.sismember(key, connection_id):
        r.expire(key, PRESENCE_TTL_SECONDS)
        r.set(_online_key(user_id), '1', ex=PRESENCE_TTL_SECONDS)


def connection_count(user_id) -> int:
    try:
        return int(_client().scard(_conns_key(user_id)) or 0)
    except Exception:
        return 0


def current_generation(user_id) -> int:
    try:
        return int(_client().get(_generation_key(user_id)) or 0)
    except Exception:
        return 0


def finalize_offline(user_id) -> dict:
    """
    Persist last_seen_at, clear online key. Returns presence_update payload.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    r = _client()
    r.delete(_online_key(user_id))
    r.delete(_conns_key(user_id))

    now = timezone.now()
    try:
        user = User.objects.select_related('profile').get(pk=user_id)
        profile = getattr(user, 'profile', None)
        if profile is not None:
            profile.last_seen_at = now
            profile.save(update_fields=['last_seen_at', 'updated_at'])
    except User.DoesNotExist:
        pass

    return presence_payload(user_id, online=False, last_seen_at=now)


def online_payload(user_id) -> dict:
    return presence_payload(user_id, online=True, last_seen_at=None)


def snapshot_for_user(user) -> dict:
    """REST-friendly presence fields for a peer."""
    online = is_online(user.id)
    last_seen = None if online else get_last_seen_at(user)
    return {
        'is_online': online,
        'last_seen_at': last_seen.isoformat() if last_seen else None,
    }


def broadcast_presence_to_conversation(conversation_id, payload: dict) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        f'chat_{conversation_id}',
        {
            'type': 'presence_update',
            'payload': payload,
        },
    )


def broadcast_presence_for_user(user_id, payload: dict) -> None:
    """
    Notify every open chat room this user participates in, and each peer's inbox
    (so list dots can update without opening the thread).
    """
    from django.db.models import Q
    from .models import Conversation

    channel_layer = get_channel_layer()
    uid = str(user_id)
    for conv in Conversation.objects.filter(
        Q(participant1_id=user_id) | Q(participant2_id=user_id)
    ).only('id', 'participant1_id', 'participant2_id'):
        broadcast_presence_to_conversation(conv.id, payload)
        if channel_layer is None:
            continue
        other_id = (
            conv.participant2_id
            if str(conv.participant1_id) == uid
            else conv.participant1_id
        )
        async_to_sync(channel_layer.group_send)(
            f'inbox_{other_id}',
            {
                'type': 'inbox_event',
                'payload': payload,
            },
        )
