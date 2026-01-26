from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from .models import Contract, ContractMilestone, ContractSignature
from .serializers import (
    ContractSerializer,
    ContractCreateSerializer,
    ContractUpdateSerializer,
    ContractMilestoneSerializer,
    ContractSignatureSerializer,
    ContractSignatureCreateSerializer,
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

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)


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
            return Response(
                ContractSignatureSerializer(signature).data,
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContractMilestoneListCreateView(generics.ListCreateAPIView):
    serializer_class = ContractMilestoneSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        contract_id = self.kwargs.get('contract_id')
        return ContractMilestone.objects.filter(contract_id=contract_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        contract_id = self.kwargs.get('contract_id')
        try:
            contract = Contract.objects.get(id=contract_id)
            context['contract'] = contract
        except Contract.DoesNotExist:
            pass
        return context

    def perform_create(self, serializer):
        contract_id = self.kwargs.get('contract_id')
        contract_id = self.kwargs.get('contract_id')
        try:
            contract = Contract.objects.get(id=contract_id)
            # Verify user has permission
            if self.request.user not in [contract.client, contract.provider]:
                return Response(
                    {'error': 'You do not have permission to add milestones to this contract.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer.save(contract=contract)
        except Contract.DoesNotExist:
            return Response(
                {'error': 'Contract not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class ContractMilestoneDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ContractMilestoneSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return ContractMilestone.objects.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.instance:
            context['contract'] = self.instance.contract
        return context

    def update(self, request, *args, **kwargs):
        milestone = self.get_object()
        contract = milestone.contract

        # Verify user has permission
        if request.user not in [contract.client, contract.provider]:
            return Response(
                {'error': 'You do not have permission to update this milestone.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Handle status updates
        new_status = request.data.get('status')
        if new_status == ContractMilestone.MilestoneStatus.COMPLETED:
            milestone.status = new_status
            milestone.completed_at = timezone.now()
            milestone.save()

            # Check if all milestones are completed
            all_completed = not contract.milestones.exclude(
                status=ContractMilestone.MilestoneStatus.COMPLETED
            ).exists()

            if all_completed and contract.milestones.exists():
                contract.status = Contract.ContractStatus.COMPLETED
                contract.completed_at = timezone.now()
                contract.save()

            return Response(ContractMilestoneSerializer(milestone).data)

        return super().update(request, *args, **kwargs)


class ContractSignatureListView(generics.ListAPIView):
    serializer_class = ContractSignatureSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        contract_id = self.kwargs.get('contract_id')
        return ContractSignature.objects.filter(contract_id=contract_id)
