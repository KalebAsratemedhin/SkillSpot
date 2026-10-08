from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from notifications.tasks import enqueue_in_app_notification
from .models import Contract, ContractMilestone, ContractSignature, TimeEntry
from .serializers import (
    ContractSerializer,
    ContractCreateSerializer,
    ContractUpdateSerializer,
    ContractMilestoneSerializer,
    ContractSignatureSerializer,
    ContractSignatureCreateSerializer,
    TimeEntrySerializer,
    TimeEntryCreateSerializer,
    TimeEntryApproveSerializer,
)

User = get_user_model()


class ContractListCreateView(generics.ListCreateAPIView):
    serializer_class = ContractSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'start_date', 'total_amount']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Contract.objects.all()
        
        # Filter by user role
        if self.request.user.user_type in ['CLIENT', 'BOTH']:
            my_contracts = self.request.query_params.get('my_contracts', None)
            if my_contracts == 'true':
                queryset = queryset.filter(client=self.request.user)
            else:
                # Show contracts where user is either client or provider
                queryset = queryset.filter(
                    Q(client=self.request.user) | Q(provider=self.request.user)
                )
        else:
            # Providers see contracts where they are the provider
            queryset = queryset.filter(provider=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by provider
        provider_id = self.request.query_params.get('provider', None)
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        
        # Filter by client
        client_id = self.request.query_params.get('client', None)
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        return queryset.distinct()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ContractCreateSerializer
        return ContractSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['client'] = self.request.user
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        contract = serializer.instance
        response_serializer = ContractSerializer(contract, context=self.get_serializer_context())
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save()
        contract = serializer.instance
        enqueue_in_app_notification(
            str(contract.provider_id),
            'New contract',
            f'You have been added to a contract: {contract.title}',
            link=f'/contracts/{contract.id}/',
            actor_id=str(self.request.user.id),
        )


class ContractDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ContractSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        return Contract.objects.filter(
            Q(client=user) | Q(provider=user)
        )

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ContractUpdateSerializer
        return ContractSerializer

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        contract = self.get_object()
        # Only allow deletion if contract is in DRAFT or CANCELLED status
        if contract.status not in [Contract.ContractStatus.DRAFT, Contract.ContractStatus.CANCELLED]:
            return Response(
                {'error': 'Only draft or cancelled contracts can be deleted.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Only client can delete
        if contract.client != request.user:
            return Response(
                {'error': 'You can only delete your own contracts.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    def perform_update(self, serializer):
        contract = serializer.instance
        old_status = contract.status
        serializer.save()
        new_status = serializer.instance.status
        if new_status != old_status and new_status in (
            Contract.ContractStatus.COMPLETED,
            Contract.ContractStatus.TERMINATED,
        ):
            other = contract.provider if self.request.user == contract.client else contract.client
            label = 'completed' if new_status == Contract.ContractStatus.COMPLETED else 'terminated'
            enqueue_in_app_notification(
                str(other.id),
                f'Contract {label}',
                f'Contract "{contract.title}" has been {label}.',
                link=f'/contracts/{contract.id}/',
                actor_id=str(self.request.user.id),
            )


class ContractSignView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Contract.objects.all()
    lookup_field = 'id'

    def post(self, request, id):
        try:
            contract = Contract.objects.get(id=id)
        except Contract.DoesNotExist:
            return Response(
                {'error': 'Contract not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify user is authorized to sign
        if request.user not in [contract.client, contract.provider]:
            return Response(
                {'error': 'You are not authorized to sign this contract.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ContractSignatureCreateSerializer(
            data=request.data,
            context={
                'contract': contract,
                'signer': request.user,
                'request': request
            }
        )

        if serializer.is_valid():
            signature = serializer.save()
            contract.refresh_from_db()
            other = contract.provider if request.user == contract.client else contract.client
            enqueue_in_app_notification(
                str(other.id),
                'Contract signed',
                f'{request.user.email} signed the contract "{contract.title}".'
                + (' Contract is now active.' if contract.is_fully_signed() else ' Sign to activate.'),
                link=f'/contracts/{contract.id}/',
                actor_id=str(request.user.id),
            )
            if contract.is_fully_signed():
                enqueue_in_app_notification(
                    str(request.user.id),
                    'Contract active',
                    f'Contract "{contract.title}" is now active.',
                    link=f'/contracts/{contract.id}/',
                )
            return Response(
                ContractSignatureSerializer(signature).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContractMilestoneListCreateView(generics.ListCreateAPIView):
    serializer_class = ContractMilestoneSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_contract(self):
        from rest_framework.exceptions import NotFound
        contract_id = self.kwargs.get('contract_id')
        try:
            return Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            raise NotFound('Contract not found.')

    def get_queryset(self):
        contract = self.get_contract()
        from .milestone_rules import assert_party
        assert_party(self.request.user, contract)
        return ContractMilestone.objects.filter(contract=contract)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['contract'] = self.get_contract()
        return context

    def perform_create(self, serializer):
        from .milestone_rules import (
            assert_client_owns_structure,
            assert_fixed_schedule,
            assert_structure_editable,
        )
        contract = self.get_contract()
        assert_fixed_schedule(contract)
        assert_client_owns_structure(self.request.user, contract)
        assert_structure_editable(contract)
        serializer.save(contract=contract)


class ContractMilestoneDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ContractMilestoneSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        return ContractMilestone.objects.filter(
            Q(contract__client=user) | Q(contract__provider=user)
        ).select_related('contract')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        try:
            context['contract'] = self.get_object().contract
        except Exception:
            pass
        return context

    def update(self, request, *args, **kwargs):
        from .milestone_rules import (
            assert_client_owns_structure,
            assert_fixed_schedule,
            assert_party,
            assert_structure_editable,
        )
        milestone = self.get_object()
        contract = milestone.contract
        assert_party(request.user, contract)
        assert_fixed_schedule(contract)

        new_status = request.data.get('status')
        structure_keys = {'title', 'description', 'amount', 'due_date', 'order'}
        touching_structure = bool(structure_keys.intersection(request.data.keys()))

        if touching_structure:
            assert_client_owns_structure(request.user, contract)
            assert_structure_editable(contract)
            response = super().update(request, *args, **kwargs)
            if new_status == ContractMilestone.MilestoneStatus.COMPLETED:
                milestone.refresh_from_db()
                milestone.status = ContractMilestone.MilestoneStatus.COMPLETED
                milestone.completed_at = timezone.now()
                milestone.save(update_fields=['status', 'completed_at', 'updated_at'])
                self._maybe_complete_contract(contract)
                return Response(ContractMilestoneSerializer(milestone).data)
            return response

        # Status-only (either party): IN_PROGRESS / COMPLETED / CANCELLED
        if new_status:
            milestone.status = new_status
            update_fields = ['status', 'updated_at']
            if new_status == ContractMilestone.MilestoneStatus.COMPLETED:
                milestone.completed_at = timezone.now()
                update_fields.append('completed_at')
                milestone.save(update_fields=update_fields)
                self._maybe_complete_contract(contract)
            else:
                milestone.save(update_fields=update_fields)
            return Response(ContractMilestoneSerializer(milestone).data)

        return Response(
            {'detail': 'No updatable fields provided.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _maybe_complete_contract(self, contract):
        """Complete contract only after every non-cancelled milestone is paid."""
        from payments.models import Payment

        milestones = contract.milestones.exclude(
            status=ContractMilestone.MilestoneStatus.CANCELLED
        )
        if not milestones.exists():
            return
        for milestone in milestones:
            paid = milestone.payments.filter(
                status=Payment.PaymentStatus.COMPLETED
            ).exists()
            if not paid:
                return
        contract.status = Contract.ContractStatus.COMPLETED
        contract.completed_at = timezone.now()
        contract.save(update_fields=['status', 'completed_at', 'updated_at'])

    def destroy(self, request, *args, **kwargs):
        from .milestone_rules import (
            assert_client_owns_structure,
            assert_fixed_schedule,
            assert_structure_editable,
        )
        milestone = self.get_object()
        contract = milestone.contract
        assert_fixed_schedule(contract)
        assert_client_owns_structure(request.user, contract)
        assert_structure_editable(contract)
        return super().destroy(request, *args, **kwargs)


class ContractSignatureListView(generics.ListAPIView):
    serializer_class = ContractSignatureSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        contract_id = self.kwargs.get('contract_id')
        return ContractSignature.objects.filter(contract_id=contract_id)


class TimeEntryListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        contract_id = self.kwargs.get('contract_id')
        return TimeEntry.objects.filter(contract_id=contract_id).select_related(
            'contract', 'provider', 'approved_by'
        )

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TimeEntryCreateSerializer
        return TimeEntrySerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['contract_id'] = self.kwargs.get('contract_id')
        return context

    def list(self, request, *args, **kwargs):
        contract = self._get_contract()
        if contract is None:
            return Response(
                {'error': 'Contract not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        if request.user not in [contract.client, contract.provider]:
            return Response(
                {'error': 'You do not have permission to view time entries for this contract.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        contract = self._get_contract()
        if contract is None:
            return Response(
                {'error': 'Contract not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        if request.user != contract.provider:
            return Response(
                {'error': 'Only the provider can add time entries.'},
                status=status.HTTP_403_FORBIDDEN
            )
        if contract.payment_schedule != Contract.PaymentSchedule.HOURLY:
            return Response(
                {'error': 'Time entries are only for hourly contracts.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        contract = self._get_contract()
        serializer.save(contract=contract, provider=self.request.user)

    def _get_contract(self):
        try:
            return Contract.objects.get(id=self.kwargs.get('contract_id'))
        except Contract.DoesNotExist:
            return None


class TimeEntryDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = TimeEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'id'

    def get_queryset(self):
        user = self.request.user
        return TimeEntry.objects.filter(
            Q(contract__client=user) | Q(contract__provider=user)
        ).select_related(
            'contract', 'provider', 'approved_by'
        )

    def update(self, request, *args, **kwargs):
        entry = self.get_object()
        contract = entry.contract
        if request.user not in [contract.client, contract.provider]:
            return Response(
                {'error': 'You do not have permission to update this time entry.'},
                status=status.HTTP_403_FORBIDDEN
            )
        new_status = request.data.get('status')
        # Client can approve or reject
        if request.user == contract.client:
            if new_status in (TimeEntry.TimeEntryStatus.APPROVED, TimeEntry.TimeEntryStatus.REJECTED):
                if entry.status != TimeEntry.TimeEntryStatus.PENDING_APPROVAL:
                    return Response(
                        {'error': 'Only pending entries can be approved or rejected.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                entry.status = new_status
                entry.approved_by = request.user
                entry.approved_at = timezone.now()
                entry.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
                return Response(TimeEntrySerializer(entry).data)
        # Provider can only edit date/hours/description when PENDING_APPROVAL
        if request.user == contract.provider:
            if entry.status != TimeEntry.TimeEntryStatus.PENDING_APPROVAL:
                return Response(
                    {'error': 'Only pending entries can be edited by the provider.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        entry = self.get_object()
        # Restrict provider to date, hours, description only
        if self.request.user == entry.contract.provider:
            allowed = {'date', 'hours', 'description'}
            data = {k: v for k, v in serializer.validated_data.items() if k in allowed}
            for k, v in data.items():
                setattr(entry, k, v)
            entry.save(update_fields=list(data.keys()) + ['updated_at'])
        else:
            serializer.save()
