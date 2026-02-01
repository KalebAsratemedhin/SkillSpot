from django.urls import path
from .views import (
    ContractListCreateView,
    ContractDetailView,
    ContractSignView,
    ContractMilestoneListCreateView,
    ContractMilestoneDetailView,
    ContractSignatureListView,
    TimeEntryListCreateView,
    TimeEntryDetailView,
)

app_name = 'contracts'

urlpatterns = [
    path('', ContractListCreateView.as_view(), name='contract_list_create'),
    path('<uuid:id>/', ContractDetailView.as_view(), name='contract_detail'),
    path('<uuid:id>/sign/', ContractSignView.as_view(), name='contract_sign'),
    path('<uuid:contract_id>/milestones/', ContractMilestoneListCreateView.as_view(), name='contract_milestone_list_create'),
    path('milestones/<uuid:id>/', ContractMilestoneDetailView.as_view(), name='contract_milestone_detail'),
    path('<uuid:contract_id>/time-entries/', TimeEntryListCreateView.as_view(), name='contract_time_entry_list_create'),
    path('time-entries/<uuid:id>/', TimeEntryDetailView.as_view(), name='contract_time_entry_detail'),
    path('<uuid:contract_id>/signatures/', ContractSignatureListView.as_view(), name='contract_signature_list'),
]
