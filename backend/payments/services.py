"""
Payment completion side effects shared by Stripe webhook + confirm endpoints.
"""
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from contracts.models import ContractMilestone, TimeEntry
from notifications.tasks import enqueue_in_app_notification
from .models import Payment, PaymentTransaction


def complete_payment(
    payment,
    *,
    stripe_payment_intent_id=None,
    stripe_charge_id=None,
    stripe_transfer_id=None,
    stripe_event_id=None,
    details=None,
):
    """
    Mark a payment COMPLETED and apply once-only side effects:
    provider total_earnings, COMPLETED transaction row, milestone/time entry, notification.

    Idempotent: if already COMPLETED, only fills missing Stripe ids; does not re-credit earnings.
    Returns (payment, newly_completed: bool).
    """
    details = details or {}
    already_done = payment.status == Payment.PaymentStatus.COMPLETED

    if stripe_payment_intent_id:
        payment.stripe_payment_intent_id = stripe_payment_intent_id
    if stripe_charge_id is not None:
        payment.stripe_charge_id = stripe_charge_id or ''
    if stripe_transfer_id is not None:
        payment.stripe_transfer_id = stripe_transfer_id or ''

    if already_done:
        payment.save()
        return payment, False

    with transaction.atomic():
        payment.status = Payment.PaymentStatus.COMPLETED
        payment.completed_at = timezone.now()
        payment.save()

        credit = payment.provider_amount if payment.provider_amount is not None else payment.amount
        profile = getattr(getattr(payment.recipient, 'profile', None), 'provider_profile', None)
        if profile is not None and credit is not None:
            type(profile).objects.filter(pk=profile.pk).update(
                total_earnings=F('total_earnings') + credit,
            )

        PaymentTransaction.objects.create(
            payment=payment,
            transaction_type=PaymentTransaction.TransactionType.COMPLETED,
            stripe_event_id=stripe_event_id or payment.stripe_payment_intent_id or '',
            details={
                'charge_id': payment.stripe_charge_id,
                'transfer_id': payment.stripe_transfer_id,
                'provider_amount': str(payment.provider_amount or ''),
                'platform_fee': str(payment.platform_fee or ''),
                **details,
            },
        )

        if payment.milestone_id:
            payment.milestone.status = ContractMilestone.MilestoneStatus.COMPLETED
            payment.milestone.completed_at = timezone.now()
            payment.milestone.save(update_fields=['status', 'completed_at', 'updated_at'])

        if payment.time_entry_id:
            payment.time_entry.status = TimeEntry.TimeEntryStatus.PAID
            payment.time_entry.save(update_fields=['status', 'updated_at'])

    enqueue_in_app_notification(
        str(payment.recipient_id),
        'Payment received',
        (
            f'You received a payment of {payment.amount} '
            f'{payment.currency or "USD"} for "{payment.contract.title}".'
        ),
        link=f'/contracts/{payment.contract_id}/',
        actor_id=str(payment.payer_id),
    )
    return payment, True
