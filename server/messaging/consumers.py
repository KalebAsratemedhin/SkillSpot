import json
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Conversation, Message


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for a single conversation. Join group chat_{conversation_id}; receive send_message, broadcast new message."""

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
        try:
            conv = Conversation.objects.get(id=self.conversation_id)
            return conv.participant1_id == user_id or conv.participant2_id == user_id
        except Conversation.DoesNotExist:
            return False

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

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
        message = await self._create_message(user.id, content)
        if not message:
            return
        payload = {
            'type': 'chat_message',
            'message': message,
        }
        await self.channel_layer.group_send(self.room_group_name, payload)

    @database_sync_to_async
    def _create_message(self, user_id, content):
        try:
            conv = Conversation.objects.get(id=self.conversation_id)
            from django.contrib.auth import get_user_model
            User = get_user_model()
            sender = User.objects.get(pk=user_id)
            if sender not in [conv.participant1, conv.participant2]:
                return None
            msg = Message.objects.create(
                conversation=conv,
                sender=sender,
                content=content,
            )
            conv.last_message_at = timezone.now()
            conv.save(update_fields=['last_message_at'])
            return self._serialize_message(msg)
        except Exception:
            return None

    def _serialize_message(self, msg):
        return {
            'id': str(msg.id),
            'conversation': str(msg.conversation_id),
            'sender': str(msg.sender_id),
            'content': msg.content,
            'is_read': msg.is_read,
            'created_at': msg.created_at.isoformat() if msg.created_at else None,
            'updated_at': msg.updated_at.isoformat() if msg.updated_at else None,
            'sender_email': msg.sender.email if msg.sender else None,
        }

    async def chat_message(self, event):
        """Send the message payload to the WebSocket."""
        await self.send(text_data=json.dumps(event['message']))

