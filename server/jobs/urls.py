from django.urls import path
from .views import (
    JobListCreateView,
    JobDetailView,
    JobCloseView,
    MyJobApplicationListView,
    JobApplicationListCreateView,
    JobApplicationDetailView,
    JobInvitationListCreateView,
    JobInvitationDetailView,
)

app_name = 'jobs'

urlpatterns = [
    path('', JobListCreateView.as_view(), name='job_list_create'),
    path('<uuid:id>/', JobDetailView.as_view(), name='job_detail'),
    path('<uuid:id>/close/', JobCloseView.as_view(), name='job_close'),
    path('applications/', MyJobApplicationListView.as_view(), name='my_job_application_list'),
    path('<uuid:job_id>/applications/', JobApplicationListCreateView.as_view(), name='job_application_list_create'),
    path('applications/<uuid:id>/', JobApplicationDetailView.as_view(), name='job_application_detail'),
    path('invitations/', JobInvitationListCreateView.as_view(), name='job_invitation_list_create'),
    path('invitations/<uuid:id>/', JobInvitationDetailView.as_view(), name='job_invitation_detail'),
]
