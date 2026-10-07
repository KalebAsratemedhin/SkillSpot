from rest_framework import generics, permissions, status, filters
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    ConversationCreateSerializer,
    MessageSerializer,
    MessageCreateSerializer,
    MessageMarkReadSerializer,
)
from .realtime import total_unread_for_user
from .services import mark_conversation_read

User = get_user_model()


class ConversationListCreateView(generics.ListCreateAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['last_message_at', 'created_at', 'updated_at']
    ordering = ['-last_message_at']

    def get_queryset(self):
        user = self.request.user
        queryset = Conversation.objects.filter(
            Q(participant1=user) | Q(participant2=user)
        ).select_related(
            'participant1',
            'participant2',
            'participant1__profile',
            'participant2__profile',
            'job',
            'last_message_sender',
        )

        job_id = self.request.query_params.get('job', None)
        if job_id:
            queryset = queryset.filter(job_id=job_id)

        participant_id = self.request.query_params.get('participant', None)
        if participant_id:
            queryset = queryset.filter(
                Q(participant1_id=participant_id) | Q(participant2_id=participant_id)
            )

        return queryset.distinct()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ConversationCreateSerializer
        return ConversationSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['participant1'] = self.request.user
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        conversation = serializer.instance
        response_serializer = ConversationSerializer(
            conversation,
            context=self.get_serializer_context()
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(participant1=self.request.user)


class ConversationDetailView(generics.RetrieveAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(
            Q(participant1=user) | Q(participant2=user)
        ).select_related(
            'participant1',
            'participant2',
            'participant1__profile',
            'participant2__profile',
            'job',
            'last_message_sender',
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class MessageListCreateView(generics.ListCreateAPIView):
    """
    Chat message history for a conversation.

    Pagination is newest-first so page 1 is the latest window (open-thread
    default). Each page's ``results`` are returned oldest → newest so clients
    can render the thread without re-sorting. Page 2+ is older history
    (prepend when implementing infinite scroll upward).
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs.get('conversation_id')
        user = self.request.user

        try:
            conversation = Conversation.objects.get(id=conversation_id)
            if user not in [conversation.participant1, conversation.participant2]:
                return Message.objects.none()
        except Conversation.DoesNotExist:
            return Message.objects.none()

        queryset = (
            Message.objects.filter(conversation_id=conversation_id)
            .select_related('sender', 'sender__profile')
            .prefetch_related('attachments')
            .order_by('-created_at', '-id')
        )

        mark_read = self.request.query_params.get('mark_read', 'false').lower() == 'true'
        if mark_read:
            mark_conversation_read(conversation=conversation, user=user)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            # DB page is newest→oldest; reverse to chronological for the thread UI.
            chronological = list(reversed(page))
            serializer = self.get_serializer(chronological, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            list(reversed(list(queryset))),
            many=True,
        )
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MessageCreateSerializer
        return MessageSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        conversation_id = self.kwargs.get('conversation_id')
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            context['conversation'] = conversation
            context['sender'] = self.request.user
        except Conversation.DoesNotExist:
            pass
        return context

    def create(self, request, *args, **kwargs):
        files = []
        if hasattr(request, 'FILES'):
            files = list(request.FILES.getlist('files')) or list(request.FILES.getlist('file'))
        serializer = self.get_serializer(data=request.data)
        # Attach files for validate/create (not model fields).
        serializer.context['files'] = files
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        message = (
            Message.objects.select_related('sender', 'sender__profile')
            .prefetch_related('attachments')
            .get(pk=serializer.instance.pk)
        )
        response_serializer = MessageSerializer(message, context=self.get_serializer_context())
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        conversation_id = self.kwargs.get('conversation_id')
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            if self.request.user not in [conversation.participant1, conversation.participant2]:
                raise permissions.PermissionDenied(
                    'You are not a participant in this conversation.'
                )
            serializer.save()
        except Conversation.DoesNotExist:
            raise NotFound('Conversation not found.')


class MessageDetailView(generics.RetrieveAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(
            Q(conversation__participant1=user) | Q(conversation__participant2=user)
        ).select_related('sender', 'conversation')

    def retrieve(self, request, *args, **kwargs):
        message = self.get_object()
        if message.sender_id != request.user.id and not message.is_read:
            from django.utils import timezone
            from .models import Conversation
            from .realtime import broadcast_inbox_update

            message.is_read = True
            message.read_at = timezone.now()
            message.save(update_fields=['is_read', 'read_at'])

            conversation = message.conversation
            remaining = (
                Message.objects.filter(conversation=conversation, is_read=False)
                .exclude(sender=request.user)
                .count()
            )
            if request.user.id == conversation.participant1_id:
                Conversation.objects.filter(pk=conversation.pk).update(
                    participant1_unread=remaining
                )
            else:
                Conversation.objects.filter(pk=conversation.pk).update(
                    participant2_unread=remaining
                )
            conversation.refresh_from_db()
            broadcast_inbox_update(
                request.user.id, conversation, event='conversation_read'
            )
        return super().retrieve(request, *args, **kwargs)


class MessageMarkReadView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageMarkReadSerializer

    def post(self, request, conversation_id=None):
        try:
            conversation = None
            if conversation_id:
                conversation = Conversation.objects.get(id=conversation_id)
                if request.user not in [conversation.participant1, conversation.participant2]:
                    return Response(
                        {'error': 'You are not a participant in this conversation.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = MessageMarkReadSerializer(
            data=request.data,
            context={
                'user': request.user,
                'conversation': conversation
            }
        )

        if serializer.is_valid():
            updated_count = serializer.save()
            return Response(
                {
                    'message': f'{updated_count} message(s) marked as read.',
                    'updated_count': updated_count,
                    'total_unread': total_unread_for_user(request.user),
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConversationUnreadCountView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            'total_unread': total_unread_for_user(request.user)
        }, status=status.HTTP_200_OK)
