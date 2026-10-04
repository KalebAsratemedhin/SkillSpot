from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from .models import Conversation, Message, MessageAttachment
from .serializers import (
    ConversationSerializer,
    ConversationCreateSerializer,
    MessageSerializer,
    MessageCreateSerializer,
    MessageMarkReadSerializer,
)

User = get_user_model()


class ConversationListCreateView(generics.ListCreateAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['last_message_at', 'created_at', 'updated_at']
    ordering = ['-last_message_at']

    def get_queryset(self):
        user = self.request.user
        # Get all conversations where user is a participant
        queryset = Conversation.objects.filter(
            Q(participant1=user) | Q(participant2=user)
        )

        # Filter by job if provided
        job_id = self.request.query_params.get('job', None)
        if job_id:
            queryset = queryset.filter(job_id=job_id)

        # Filter by other participant
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
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs.get('conversation_id')
        user = self.request.user

        # Verify user is a participant
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            if user not in [conversation.participant1, conversation.participant2]:
                return Message.objects.none()
        except Conversation.DoesNotExist:
            return Message.objects.none()

        queryset = Message.objects.filter(conversation_id=conversation_id)

        # Mark messages as read when viewing (optional - can be done via separate endpoint)
        mark_read = self.request.query_params.get('mark_read', 'false').lower() == 'true'
        if mark_read:
            # Mark all unread messages from the other participant as read
            other_participant = conversation.get_other_participant(user)
            Message.objects.filter(
                conversation=conversation,
                sender=other_participant,
                is_read=False
            ).update(is_read=True, read_at=timezone.now())

        return queryset

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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        message = serializer.instance
        response_serializer = MessageSerializer(message, context=self.get_serializer_context())
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        conversation_id = self.kwargs.get('conversation_id')
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            # Verify user is a participant
            if self.request.user not in [conversation.participant1, conversation.participant2]:
                raise permissions.PermissionDenied(
                    'You are not a participant in this conversation.'
                )
            serializer.save()
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class MessageDetailView(generics.RetrieveAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        # Only show messages from conversations where user is a participant
        return Message.objects.filter(
            Q(conversation__participant1=user) | Q(conversation__participant2=user)
        )

    def retrieve(self, request, *args, **kwargs):
        message = self.get_object()
        # Mark as read if the current user is the recipient
        if message.sender != request.user:
            message.mark_as_read()
        return super().retrieve(request, *args, **kwargs)


class MessageMarkReadView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageMarkReadSerializer

    def post(self, request, conversation_id=None):
        try:
            conversation = None
            if conversation_id:
                conversation = Conversation.objects.get(id=conversation_id)
                # Verify user is a participant
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
                    'updated_count': updated_count
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConversationUnreadCountView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        # Count unread messages where user is a participant but not the sender
        total_unread = Message.objects.filter(
            Q(conversation__participant1=user) | Q(conversation__participant2=user),
            ~Q(sender=user),
            is_read=False
        ).count()

        return Response({
            'total_unread': total_unread
        }, status=status.HTTP_200_OK)
