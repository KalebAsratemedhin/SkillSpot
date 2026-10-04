from django.urls import path
from .views import (
    ConversationListCreateView,
    ConversationDetailView,
    MessageListCreateView,
    MessageDetailView,
    MessageMarkReadView,
    ConversationUnreadCountView,
)

app_name = 'messaging'

urlpatterns = [
    path('conversations/', ConversationListCreateView.as_view(), name='conversation_list_create'),
    path('conversations/<uuid:id>/', ConversationDetailView.as_view(), name='conversation_detail'),
    path('conversations/<uuid:conversation_id>/messages/', MessageListCreateView.as_view(), name='message_list_create'),
    path('messages/<uuid:id>/', MessageDetailView.as_view(), name='message_detail'),
    path('conversations/<uuid:conversation_id>/mark-read/', MessageMarkReadView.as_view(), name='message_mark_read'),
    path('conversations/unread-count/', ConversationUnreadCountView.as_view(), name='conversation_unread_count'),
]
