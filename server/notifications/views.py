from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Notification
from .serializers import NotificationSerializer, NotificationMarkReadSerializer


class NotificationListView(generics.ListAPIView):
    """List notifications for the current user (recipient)."""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Notification.objects.filter(recipient=self.request.user)
            .select_related('actor')
            .order_by('-created_at')
        )


class NotificationDetailView(generics.RetrieveAPIView, generics.UpdateAPIView):
    """Retrieve a notification or mark it read (PATCH)."""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = 'id'
    lookup_field = 'id'

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related('actor')

    def get_serializer_class(self):
        if self.request.method in ('PATCH', 'PUT'):
            return NotificationMarkReadSerializer
        return NotificationSerializer

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = NotificationMarkReadSerializer(
            instance,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        instance.read = serializer.validated_data.get('read', instance.read)
        instance.read_at = timezone.now() if instance.read else None
        instance.save(update_fields=['read', 'read_at'])
        return Response(NotificationSerializer(instance).data)


class NotificationMarkAllReadView(generics.GenericAPIView):
    """Mark all notifications as read for the current user."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        updated = (
            Notification.objects.filter(recipient=request.user, read=False)
            .update(read=True, read_at=timezone.now())
        )
        return Response({'marked': updated}, status=status.HTTP_200_OK)




