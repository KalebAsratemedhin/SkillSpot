from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
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
        queryset = Job.objects.all()
        
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        job_type = self.request.query_params.get('job_type', None)
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        
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
        
        if self.request.user.user_type in ['CLIENT', 'BOTH']:
            my_jobs = self.request.query_params.get('my_jobs', None)
            if my_jobs == 'true':
                queryset = queryset.filter(client=self.request.user)
        
        return queryset.distinct()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return JobCreateSerializer
        return JobSerializer

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)


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
            return Response(
                {'message': 'Job closed successfully.'},
                status=status.HTTP_200_OK
            )
        except Job.DoesNotExist:
            return Response(
                {'error': 'Job not found or you do not have permission.'},
                status=status.HTTP_404_NOT_FOUND
            )


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

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)


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
