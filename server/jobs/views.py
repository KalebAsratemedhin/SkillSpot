from rest_framework import generics, permissions, status, filters
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Q
from django.http import Http404
from django.utils import timezone
from skillspot.cache_utils import job_list_cache_key, JOB_LIST_TIMEOUT
from notifications.tasks import send_in_app_notification
from .models import Job, JobApplication, JobInvitation
from .serializers import (
    JobSerializer,
    JobCreateSerializer,
    JobApplicationSerializer,
    JobApplicationCreateSerializer,
    JobInvitationSerializer,
    JobInvitationCreateSerializer,
)

User = get_user_model()


class JobListCreateView(generics.ListCreateAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['created_at', 'budget_min', 'budget_max']
    ordering = ['-created_at']

    def get_queryset(self):
        my_jobs = self.request.query_params.get('my_jobs', None)
        is_my_jobs = (
            my_jobs == 'true'
            and self.request.user.user_type in ['CLIENT', 'BOTH']
        )
        if is_my_jobs:
            queryset = Job.objects.all()
        else:
            queryset = Job.objects.exclude(
                status__in=[Job.JobStatus.COMPLETED, Job.JobStatus.CANCELLED]
            )

        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        location = self.request.query_params.get('location', None)
        if location:
            queryset = queryset.filter(location__icontains=location)

        skill_id = self.request.query_params.get('skill', None)
        if skill_id:
            queryset = queryset.filter(required_skills__id=skill_id)

        budget_min = self.request.query_params.get('budget_min', None)
        if budget_min:
            queryset = queryset.filter(budget_max__gte=budget_min)

        budget_max = self.request.query_params.get('budget_max', None)
        if budget_max:
            queryset = queryset.filter(budget_min__lte=budget_max)

        if is_my_jobs:
            queryset = queryset.filter(client=self.request.user)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return JobCreateSerializer
        return JobSerializer

    def list(self, request, *args, **kwargs):
        if request.method != 'GET':
            return super().list(request, *args, **kwargs)
        is_my_jobs = (
            request.query_params.get('my_jobs') == 'true'
            and request.user.user_type in ['CLIENT', 'BOTH']
        )
        if is_my_jobs:
            return super().list(request, *args, **kwargs)
        key = job_list_cache_key(request)
        data = cache.get(key)
        if data is not None:
            return Response(data)
        response = super().list(request, *args, **kwargs)
        cache.set(key, response.data, timeout=JOB_LIST_TIMEOUT)
        return response

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)
        job = serializer.instance
        print(
            '[Job Create] Backend saved job:',
            'id=', getattr(job, 'id', None),
            'latitude=', getattr(job, 'latitude', None),
            'longitude=', getattr(job, 'longitude', None),
            'has_lat_lng=', job.latitude is not None and job.longitude is not None,
        )


class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Job.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return JobCreateSerializer
        return JobSerializer

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        job = self.get_object()
        if job.client != request.user:
            return Response(
                {'error': 'You can only delete your own jobs.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    def perform_update(self, serializer):
        job = self.get_object()
        if job.client != self.request.user:
            raise PermissionDenied('You can only update your own jobs.')
        serializer.save()

class JobCloseView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Job.objects.all()
    lookup_field = 'id'

    def post(self, request, id):
        try:
            job = Job.objects.get(id=id, client=request.user)
            if job.status == Job.JobStatus.COMPLETED:
                return Response(
                    {'error': 'Job is already completed.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            job.status = Job.JobStatus.COMPLETED
            job.closed_at = timezone.now()
            job.save()
            for app in job.applications.filter(status=JobApplication.ApplicationStatus.ACCEPTED):
                send_in_app_notification.delay(
                    str(app.provider_id),
                    'Job completed',
                    f'Job "{job.title}" has been marked as completed.',
                    link=f'/jobs/{job.id}/',
                    actor_id=str(request.user.id),
                )
            return Response(
                {'message': 'Job closed successfully.'},
                status=status.HTTP_200_OK
            )
        except Job.DoesNotExist:
            return Response(
                {'error': 'Job not found or you do not have permission.'},
                status=status.HTTP_404_NOT_FOUND
            )


class MyJobApplicationListView(generics.ListAPIView):
    """List applications: as provider = ones I submitted; as client = ones to my jobs."""
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['CLIENT', 'BOTH']:
            return JobApplication.objects.filter(job__client=user).order_by('-applied_at')
        return JobApplication.objects.filter(provider=user).order_by('-applied_at')


class JobApplicationListCreateView(generics.ListCreateAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        job_id = self.kwargs.get('job_id')
        queryset = JobApplication.objects.filter(job_id=job_id)
        
        if self.request.user.user_type in ['CLIENT', 'BOTH']:
            my_applications = self.request.query_params.get('my_applications', None)
            if my_applications == 'true':
                queryset = JobApplication.objects.filter(
                    job__client=self.request.user
                )
        else:
            queryset = JobApplication.objects.filter(provider=self.request.user)
        
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return JobApplicationCreateSerializer
        return JobApplicationSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method == 'POST':
            job_id = self.kwargs.get('job_id')
            try:
                context['job'] = Job.objects.get(id=job_id)
            except Job.DoesNotExist:
                raise Http404('Job not found.')
            context['provider'] = self.request.user
        return context

    def perform_create(self, serializer):
        job_id = self.kwargs.get('job_id')
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            raise Response(
                {'error': 'Job not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer.save(
            job=job,
            provider=self.request.user
        )
        # Notify job owner (client) about the new application
        send_in_app_notification.delay(
            str(job.client_id),
            'New application',
            f'Someone applied to your job: {job.title}',
            link=f'/jobs/{job.id}/',
            actor_id=str(self.request.user.id),
        )


class JobApplicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        if self.request.user.user_type in ['CLIENT', 'BOTH']:
            return JobApplication.objects.filter(job__client=self.request.user)
        return JobApplication.objects.filter(provider=self.request.user)

    def update(self, request, *args, **kwargs):
        application = self.get_object()
        
        if request.user.user_type in ['CLIENT', 'BOTH']:
            if application.job.client != request.user:
                return Response(
                    {'error': 'You can only update applications for your jobs.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            new_status = request.data.get('status')
            if new_status in ['ACCEPTED', 'REJECTED']:
                application.status = new_status
                application.reviewed_at = timezone.now()
                application.save()
                
                if new_status == 'ACCEPTED':
                    application.job.status = Job.JobStatus.IN_PROGRESS
                    application.job.save()
                    # Notify provider their application was accepted
                    send_in_app_notification.delay(
                        str(application.provider_id),
                        'Application accepted',
                        f'Your application for "{application.job.title}" was accepted.',
                        link=f'/jobs/{application.job_id}/',
                        actor_id=str(request.user.id),
                    )
                return Response(JobApplicationSerializer(application).data)
        
        if application.provider == request.user:
            if request.data.get('status') == 'WITHDRAWN':
                application.status = 'WITHDRAWN'
                application.save()
                return Response(JobApplicationSerializer(application).data)
        
        return Response(
            {'error': 'You do not have permission to update this application.'},
            status=status.HTTP_403_FORBIDDEN
        )


class JobInvitationListCreateView(generics.ListCreateAPIView):
    serializer_class = JobInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.user_type in ['CLIENT', 'BOTH']:
            return JobInvitation.objects.filter(client=self.request.user)
        return JobInvitation.objects.filter(provider=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return JobInvitationCreateSerializer
        return JobInvitationSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['client'] = self.request.user
        return context

    def perform_create(self, serializer):
        invitation = serializer.save(client=self.request.user)
        # Notify provider they were invited to the job
        send_in_app_notification.delay(
            str(invitation.provider_id),
            'Job invitation',
            f'You were invited to apply for "{invitation.job.title}".',
            link=f'/jobs/{invitation.job_id}/',
            actor_id=str(self.request.user.id),
        )
        # Auto-create a conversation between client and provider for this job
        from messaging.models import Conversation
        client = self.request.user
        provider = invitation.provider
        job = invitation.job
        if job and client and provider:
            if client.id > provider.id:
                p1, p2 = provider, client
            else:
                p1, p2 = client, provider
            Conversation.objects.get_or_create(
                participant1=p1,
                participant2=p2,
                job=job,
                defaults={}
            )


class JobInvitationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JobInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        if self.request.user.user_type in ['CLIENT', 'BOTH']:
            return JobInvitation.objects.filter(
                Q(client=self.request.user) | Q(provider=self.request.user)
            )
        return JobInvitation.objects.filter(provider=self.request.user)

    def update(self, request, *args, **kwargs):
        invitation = self.get_object()
        
        if invitation.provider != request.user:
            return Response(
                {'error': 'You can only respond to invitations sent to you.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_status = request.data.get('status')
        if new_status in ['ACCEPTED', 'DECLINED']:
            invitation.status = new_status
            invitation.responded_at = timezone.now()
            invitation.save()
            
            if new_status == 'ACCEPTED' and invitation.job:
                invitation.job.status = Job.JobStatus.IN_PROGRESS
                invitation.job.save()
            
            return Response(JobInvitationSerializer(invitation).data)
        
        return Response(
            {'error': 'Invalid status. Use ACCEPTED or DECLINED.'},
            status=status.HTTP_400_BAD_REQUEST
        )
