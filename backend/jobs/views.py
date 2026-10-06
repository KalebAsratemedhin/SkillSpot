from rest_framework import generics, permissions, status, filters
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Case, IntegerField, Prefetch, Q, Value, When
from django.http import Http404
from django.utils import timezone
from skillspot.cache_utils import job_list_cache_key, JOB_LIST_TIMEOUT
from notifications.tasks import enqueue_in_app_notification
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


def _job_queryset(user):
    """Jobs with client profile, skills, and the requester's own applications prefetched."""
    qs = Job.objects.select_related('client__profile').prefetch_related('required_skills')
    if user is not None and getattr(user, 'is_authenticated', False):
        qs = qs.prefetch_related(
            Prefetch(
                'applications',
                queryset=JobApplication.objects.filter(provider=user),
                to_attr='_my_applications',
            )
        )
    return qs


def _parse_skill_ids(request):
    """Collect skill UUIDs from skill= and skills= (repeatable)."""
    ids = []
    for key in ('skill', 'skills'):
        ids.extend(request.query_params.getlist(key))
    # Also support comma-separated skills=
    for raw in list(ids):
        if ',' in raw:
            ids.remove(raw)
            ids.extend(part.strip() for part in raw.split(',') if part.strip())
    return [s for s in ids if s]


def _search_query(request):
    return (request.query_params.get('q') or request.query_params.get('search') or '').strip()


class JobListCreateView(generics.ListCreateAPIView):
    serializer_class = JobSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'budget_min', 'budget_max']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.request.method == 'GET':
            if self.request.query_params.get('my_jobs') == 'true':
                return [permissions.IsAuthenticated()]
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        my_jobs = self.request.query_params.get('my_jobs') == 'true'
        is_my_jobs = (
            my_jobs
            and getattr(user, 'is_authenticated', False)
            and user.user_type in ['CLIENT', 'BOTH']
        )
        queryset = _job_queryset(user if getattr(user, 'is_authenticated', False) else None)

        if is_my_jobs:
            queryset = queryset.filter(client=user)
        else:
            # Public browse: open jobs only (exclude completed/cancelled; also exclude draft)
            queryset = queryset.filter(status=Job.JobStatus.OPEN)

        status_filter = self.request.query_params.get('status')
        if status_filter and is_my_jobs:
            queryset = queryset.filter(status=status_filter)

        location = self.request.query_params.get('location')
        if location:
            # Text address filter (coordinates are nested under location in the API)
            queryset = queryset.filter(address__icontains=location)

        skill_ids = _parse_skill_ids(self.request)
        if skill_ids:
            queryset = queryset.filter(required_skills__id__in=skill_ids)

        budget_min = self.request.query_params.get('budget_min')
        if budget_min:
            queryset = queryset.filter(budget_max__gte=budget_min)

        budget_max = self.request.query_params.get('budget_max')
        if budget_max:
            queryset = queryset.filter(budget_min__lte=budget_max)

        payment_schedule = self.request.query_params.get('payment_schedule')
        if payment_schedule:
            queryset = queryset.filter(payment_schedule=payment_schedule.upper())

        q = _search_query(self.request)
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q)
                | Q(description__icontains=q)
                | Q(address__icontains=q)
                | Q(required_skills__name__icontains=q)
            )
            # Simple relevance: title hits first, then skill name, then other text
            queryset = queryset.annotate(
                _relevance=Case(
                    When(title__icontains=q, then=Value(3)),
                    When(required_skills__name__icontains=q, then=Value(2)),
                    When(Q(description__icontains=q) | Q(address__icontains=q), then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            )

        ordering = self.request.query_params.get('ordering')
        if q and (not ordering or ordering == 'relevance'):
            queryset = queryset.order_by('-_relevance', '-created_at')

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
            and getattr(request.user, 'is_authenticated', False)
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


class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JobSerializer
    lookup_field = 'id'

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user if getattr(self.request.user, 'is_authenticated', False) else None
        return _job_queryset(user)

    def get_object(self):
        job = super().get_object()
        user = self.request.user
        authenticated = getattr(user, 'is_authenticated', False)

        if job.status == Job.JobStatus.OPEN:
            return job

        if not authenticated:
            raise NotFound()

        if job.client_id == user.id:
            return job

        # Parties on in-progress (or completed) work: accepted provider
        if job.status in (Job.JobStatus.IN_PROGRESS, Job.JobStatus.COMPLETED):
            if job.applications.filter(
                provider=user,
                status=JobApplication.ApplicationStatus.ACCEPTED,
            ).exists():
                return job

        raise NotFound()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return JobCreateSerializer
        return JobSerializer

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
                enqueue_in_app_notification(
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
        qs = JobApplication.objects.select_related(
            'provider__profile__provider_profile',
            'job',
        ).prefetch_related('provider__profile__provider_profile__skills')
        if user.user_type in ['CLIENT', 'BOTH']:
            return qs.filter(job__client=user).order_by('-applied_at')
        return qs.filter(provider=user).order_by('-applied_at')


class JobApplicationListCreateView(generics.ListCreateAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        job_id = self.kwargs.get('job_id')
        queryset = JobApplication.objects.filter(job_id=job_id).select_related(
            'provider__profile__provider_profile',
            'job',
        ).prefetch_related('provider__profile__provider_profile__skills')
        user = self.request.user

        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            raise Http404('Job not found.')

        if job.client_id == user.id:
            my_applications = self.request.query_params.get('my_applications', None)
            if my_applications == 'true':
                return JobApplication.objects.filter(job__client=user).select_related(
                    'provider__profile__provider_profile',
                    'job',
                ).prefetch_related('provider__profile__provider_profile__skills')
            return queryset

        if user.user_type in ['PROVIDER', 'BOTH']:
            return queryset.filter(provider=user)

        return queryset.none()

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
        enqueue_in_app_notification(
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
        qs = JobApplication.objects.select_related(
            'provider__profile__provider_profile',
            'job',
        ).prefetch_related('provider__profile__provider_profile__skills')
        if self.request.user.user_type in ['CLIENT', 'BOTH']:
            return qs.filter(
                Q(job__client=self.request.user) | Q(provider=self.request.user)
            )
        return qs.filter(provider=self.request.user)

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
                    enqueue_in_app_notification(
                        str(application.provider_id),
                        'Application accepted',
                        f'Your application for "{application.job.title}" was accepted.',
                        link=f'/jobs/{application.job_id}/',
                        actor_id=str(request.user.id),
                    )
                return Response(
                    JobApplicationSerializer(application, context={'request': request}).data
                )

        if application.provider == request.user:
            if request.data.get('status') == 'WITHDRAWN':
                application.status = 'WITHDRAWN'
                application.save()
                return Response(
                    JobApplicationSerializer(application, context={'request': request}).data
                )

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
        enqueue_in_app_notification(
            str(invitation.provider_id),
            'Job invitation',
            f'You were invited to apply for "{invitation.job.title}".',
            link=f'/jobs/{invitation.job_id}/',
            actor_id=str(self.request.user.id),
        )
        # Do not auto-create a chat room on invite — messaging is explicit / per user pair.

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
