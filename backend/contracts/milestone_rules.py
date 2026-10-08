"""
Rules for FIXED-price milestones vs HOURLY time entries.
"""
from decimal import Decimal

from django.db.models import Sum
from rest_framework.exceptions import PermissionDenied, ValidationError


def milestone_sum(contract) -> Decimal:
    total = contract.milestones.aggregate(s=Sum('amount'))['s']
    return total if total is not None else Decimal('0')


def contract_has_paid_milestone(contract) -> bool:
    """True once any milestone on this contract has a COMPLETED payment."""
    from payments.models import Payment

    return Payment.objects.filter(
        contract=contract,
        milestone__isnull=False,
        status=Payment.PaymentStatus.COMPLETED,
    ).exists()


def assert_fixed_schedule(contract):
    from .models import Contract

    if contract.payment_schedule != Contract.PaymentSchedule.FIXED:
        raise ValidationError({
            'detail': 'Milestones are only allowed on fixed-price (FIXED) contracts. '
                      'Use time entries for hourly contracts.',
        })


def assert_client_owns_structure(user, contract):
    if user != contract.client:
        raise PermissionDenied(
            'Only the client can create, edit amounts, or delete milestones.'
        )


def assert_party(user, contract):
    if user not in (contract.client, contract.provider):
        raise PermissionDenied('You are not a party to this contract.')


def assert_structure_editable(contract):
    from .models import Contract

    if contract.status not in (
        Contract.ContractStatus.DRAFT,
        Contract.ContractStatus.PENDING_SIGNATURES,
    ):
        raise ValidationError({
            'detail': 'Milestone amounts and structure can only be changed while the '
                      'contract is DRAFT or PENDING_SIGNATURES.',
        })
    if contract_has_paid_milestone(contract):
        raise ValidationError({
            'detail': 'Milestone structure is frozen after the first milestone payment.',
        })


def assert_milestones_allocated_for_signing(contract):
    """If milestones exist on a FIXED contract, they must sum exactly to total_amount."""
    from .models import Contract

    if contract.payment_schedule != Contract.PaymentSchedule.FIXED:
        return
    if not contract.milestones.exists():
        # Legacy single-shot FIXED (no milestones) — allowed.
        return
    allocated = milestone_sum(contract)
    if allocated != contract.total_amount:
        raise ValidationError({
            'detail': (
                f'Milestone amounts must sum to the contract total '
                f'({contract.total_amount}) before signing. '
                f'Currently allocated: {allocated}.'
            ),
        })
