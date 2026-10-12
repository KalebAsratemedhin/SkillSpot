"""
Payment completion side effects shared by Stripe webhook + confirm endpoints.
"""
import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from contracts.models import ContractMilestone, TimeEntry
from notifications.tasks import enqueue_in_app_notification
from profiles.models import ServiceProviderProfile
from .models import Payment, PaymentTransaction

logger = logging.getLogger(__name__)


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

    if stripe_payment_intent_id:
        payment.stripe_payment_intent_id = stripe_payment_intent_id
    if stripe_charge_id is not None:
        payment.stripe_charge_id = stripe_charge_id or ''
    if stripe_transfer_id is not None:
        payment.stripe_transfer_id = stripe_transfer_id or ''

    with transaction.atomic():
        locked = Payment.objects.select_for_update().get(pk=payment.pk)

        if stripe_payment_intent_id:
            locked.stripe_payment_intent_id = stripe_payment_intent_id
        if stripe_charge_id is not None:
            locked.stripe_charge_id = stripe_charge_id or ''
        if stripe_transfer_id is not None:
            locked.stripe_transfer_id = stripe_transfer_id or ''

        if locked.status == Payment.PaymentStatus.COMPLETED:
            logger.info(
                'complete_payment: SKIP earnings (already COMPLETED) payment_id=%s recipient_id=%s',
                locked.id,
                locked.recipient_id,
            )
            locked.save()
            payment.refresh_from_db()
            return payment, False

        locked.status = Payment.PaymentStatus.COMPLETED
        locked.completed_at = timezone.now()
        locked.save()

        credit = locked.provider_amount if locked.provider_amount is not None else locked.amount
        if credit is None:
            credit = Decimal('0')
        logger.info(
            'complete_payment: about to credit total_earnings += %s '
            'payment_id=%s recipient_id=%s provider_amount=%s',
            credit,
            locked.id,
            locked.recipient_id,
            locked.provider_amount,
        )
        rows = ServiceProviderProfile.objects.filter(
            profile__user_id=locked.recipient_id,
        ).update(
            total_earnings=F('total_earnings') + credit,
        )
        logger.info(
            'complete_payment: earnings update rows=%s payment_id=%s recipient_id=%s',
            rows,
            locked.id,
            locked.recipient_id,
        )

        PaymentTransaction.objects.create(
            payment=locked,
            transaction_type=PaymentTransaction.TransactionType.COMPLETED,
            stripe_event_id=stripe_event_id or locked.stripe_payment_intent_id or '',
            details={
                'charge_id': locked.stripe_charge_id,
                'transfer_id': locked.stripe_transfer_id,
                'provider_amount': str(locked.provider_amount or ''),
                'platform_fee': str(locked.platform_fee or ''),
                'earnings_credit': str(credit),
                'earnings_rows_updated': rows,
                **details,
            },
        )

        if locked.milestone_id:
            locked.milestone.status = ContractMilestone.MilestoneStatus.COMPLETED
            locked.milestone.completed_at = timezone.now()
            locked.milestone.save(update_fields=['status', 'completed_at', 'updated_at'])

        if locked.time_entry_id:
            locked.time_entry.status = TimeEntry.TimeEntryStatus.PAID
            locked.time_entry.save(update_fields=['status', 'updated_at'])

    payment.refresh_from_db()
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
