import asyncio
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .presence import (
    OFFLINE_GRACE_SECONDS,
    broadcast_presence_for_user,
    connection_count,
    current_generation,
    finalize_offline,
    online_payload,
    presence_payload,
    register_connection,
    unregister_connection,
    is_online,
    get_last_seen_at,
)


class PresenceMixin:
    """Shared online/offline tracking for chat + inbox sockets."""

    async def _presence_on_connect(self, user_id):
        self.presence_user_id = str(user_id)
        self.presence_connection_id = self.channel_name
        became_online = await database_sync_to_async(register_connection)(
            self.presence_user_id,
            self.presence_connection_id,
        )
        if became_online:
            payload = online_payload(self.presence_user_id)
            await database_sync_to_async(broadcast_presence_for_user)(
                self.presence_user_id,
                payload,
            )

    async def _presence_on_disconnect(self):
        user_id = getattr(self, 'presence_user_id', None)
        conn_id = getattr(self, 'presence_connection_id', None)
        if not user_id or not conn_id:
            return
        became_offline, gen = await database_sync_to_async(unregister_connection)(
            user_id,
            conn_id,
        )
        if became_offline:
            asyncio.create_task(self._finalize_offline_after_grace(user_id, gen))

    async def _finalize_offline_after_grace(self, user_id, gen_at_disconnect):
        await asyncio.sleep(OFFLINE_GRACE_SECONDS)

        def _maybe_offline():
            if connection_count(user_id) > 0:
                return None
            if current_generation(user_id) != gen_at_disconnect:
                return None
            return finalize_offline(user_id)

        payload = await database_sync_to_async(_maybe_offline)()
        if payload:
            await database_sync_to_async(broadcast_presence_for_user)(user_id, payload)


class ChatConsumer(PresenceMixin, AsyncWebsocketConsumer):
    """WebSocket for one conversation: join chat_{id}; send_message creates + fans out."""

    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        user = self.scope.get('user')
        if not user or user.is_anonymous:
            await self.close(code=4401)
            return
        allowed = await self._user_is_participant(user.id)
        if not allowed:
            await self.close(code=4403)
            return
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self._presence_on_connect(user.id)
        # Tell this client the peer's current presence immediately.
        peer = await self._peer_presence(user.id)
        if peer:
            await self.send(text_data=json.dumps(peer))

    @database_sync_to_async
    def _user_is_participant(self, user_id):
        from django.db import close_old_connections
        from .models import Conversation

        close_old_connections()
        try:
            conv = Conversation.objects.get(id=self.conversation_id)
            return conv.participant1_id == user_id or conv.participant2_id == user_id
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def _peer_presence(self, user_id):
        from django.contrib.auth import get_user_model
        from django.db import close_old_connections
        from .models import Conversation

        close_old_connections()
        User = get_user_model()
        try:
            conv = Conversation.objects.select_related(
                'participant1__profile',
                'participant2__profile',
            ).get(id=self.conversation_id)
        except Conversation.DoesNotExist:
            return None
        peer_id = (
            conv.participant2_id
            if conv.participant1_id == user_id
            else conv.participant1_id
        )
        try:
            peer = User.objects.select_related('profile').get(pk=peer_id)
        except User.DoesNotExist:
            return None
        online = is_online(peer_id)
        last_seen = None if online else get_last_seen_at(peer)
        return presence_payload(peer_id, online=online, last_seen_at=last_seen)

    async def disconnect(self, close_code):
        await self._presence_on_disconnect()
        room = getattr(self, 'room_group_name', None)
        if not room or not self.channel_layer:
            return
        try:
            await self.channel_layer.group_discard(room, self.channel_name)
        except Exception:
            pass

    async def receive(self, text_data):
        user = self.scope.get('user')
        if not user or user.is_anonymous:
            return
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return
        if data.get('type') != 'send_message':
            return
        content = (data.get('content') or '').strip()
        if not content:
            return
        ok = await self._create_message(user.id, content)
        if not ok:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'detail': 'Could not send message.',
            }))

    @database_sync_to_async
    def _create_message(self, user_id, content):
        from django.contrib.auth import get_user_model
        from django.db import close_old_connections
        from .models import Conversation
        from .services import create_and_broadcast_message

        close_old_connections()
        User = get_user_model()
        try:
            conv = Conversation.objects.get(id=self.conversation_id)
            sender = User.objects.get(pk=user_id)
            create_and_broadcast_message(
                conversation=conv,
                sender=sender,
                content=content,
            )
            return True
        except Exception:
            return False

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

    async def presence_update(self, event):
        await self.send(text_data=json.dumps(event['payload']))


class InboxConsumer(PresenceMixin, AsyncWebsocketConsumer):
    """
    Per-user inbox socket. Join inbox_{user_id}; receive conversation list patches,
    presence_update, and notification_* frames (see frontend practices contracts).
    """

    async def connect(self):
        user = self.scope.get('user')
        if not user or user.is_anonymous:
            await self.close(code=4401)
            return
        self.user_id = str(user.id)
        self.room_group_name = f'inbox_{self.user_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self._presence_on_connect(user.id)

    async def disconnect(self, close_code):
        await self._presence_on_disconnect()
        room = getattr(self, 'room_group_name', None)
        if not room or not self.channel_layer:
            return
        try:
            await self.channel_layer.group_discard(room, self.channel_name)
        except Exception:
            pass

    async def receive(self, text_data):
        return

    async def inbox_event(self, event):
        await self.send(text_data=json.dumps(event['payload']))
