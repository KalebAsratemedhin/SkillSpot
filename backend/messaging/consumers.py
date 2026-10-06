import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
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

    @database_sync_to_async
    def _user_is_participant(self, user_id):
        from .models import Conversation
        try:
            conv = Conversation.objects.get(id=self.conversation_id)
            return conv.participant1_id == user_id or conv.participant2_id == user_id
        except Conversation.DoesNotExist:
            return False

    async def disconnect(self, close_code):
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
        from .models import Conversation
        from .services import create_and_broadcast_message

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


class InboxConsumer(AsyncWebsocketConsumer):
    """
    Per-user inbox socket. Join inbox_{user_id}; receive conversation list patches
    (new messages, read receipts) without opening every chat room.
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

    async def disconnect(self, close_code):
        room = getattr(self, 'room_group_name', None)
        if not room or not self.channel_layer:
            return
        try:
            await self.channel_layer.group_discard(room, self.channel_name)
        except Exception:
            pass

    async def receive(self, text_data):
        # Inbox is push-only; ignore client frames.
        return

    async def inbox_event(self, event):
        await self.send(text_data=json.dumps(event['payload']))
