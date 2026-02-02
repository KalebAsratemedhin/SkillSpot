import stripe
from decimal import Decimal
from django.conf import settings
from django.db import models
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.utils import timezone
from .models import Payment, PaymentTransaction
from contracts.models import Contract, ContractMilestone, TimeEntry
from .serializers import (
    PaymentSerializer,
    PaymentCreateSerializer,
    PaymentTransactionSerializer,
    StripePaymentIntentSerializer,
    StripeCheckoutSessionSerializer,
)

# Initialize Stripe (will use settings.STRIPE_SECRET_KEY)
# Make sure to set STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY in settings


class PaymentListCreateView(generics.ListCreateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Payment.objects.all()

        # Filter by user role
        if self.request.user.user_type in ['CLIENT', 'BOTH']:
            my_payments = self.request.query_params.get('my_payments', None)
            if my_payments == 'true':
                queryset = queryset.filter(payer=user)
            else:
                # Show payments where user is either payer or recipient
                queryset = queryset.filter(
                    models.Q(payer=user) | models.Q(recipient=user)
                )
        else:
            # Providers see payments where they are the recipient
            queryset = queryset.filter(recipient=user)

        # Filter by contract
        contract_id = self.request.query_params.get('contract', None)
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)

        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by milestone
        milestone_id = self.request.query_params.get('milestone', None)
        if milestone_id:
            queryset = queryset.filter(milestone_id=milestone_id)

        # Filter by time_entry
        time_entry_id = self.request.query_params.get('time_entry', None)
        if time_entry_id:
            queryset = queryset.filter(time_entry_id=time_entry_id)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PaymentCreateSerializer
        return PaymentSerializer

    def get_serializer_context(self):
        """Add payer to context for serializer validation."""
        context = super().get_serializer_context()
        context['payer'] = self.request.user
        return context

    def perform_create(self, serializer):
        serializer.save()


class PaymentDetailView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        return Payment.objects.filter(
            models.Q(payer=user) | models.Q(recipient=user)
        )


class CreateStripePaymentIntentView(generics.GenericAPIView):
    """
    Create a Stripe PaymentIntent for a payment
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StripePaymentIntentSerializer

    def post(self, request):
        serializer = StripePaymentIntentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        payment_id = serializer.validated_data['payment_id']
        return_url = serializer.validated_data.get('return_url', '')

        try:
            payment = Payment.objects.get(id=payment_id)

            # Verify user is the payer
            if payment.payer != request.user:
                return Response(
                    {'error': 'You can only create payment intents for your own payments.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Initialize Stripe
            stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
            if not stripe.api_key:
                return Response(
                    {'error': 'Stripe is not configured.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Check if provider has Stripe Connect account
            provider_profile = None
            if hasattr(payment.recipient, 'profile') and hasattr(payment.recipient.profile, 'provider_profile'):
                provider_profile = payment.recipient.profile.provider_profile
            
            # Calculate platform fee (e.g., 5% - adjust as needed)
            platform_fee_percent = Decimal(str(getattr(settings, 'STRIPE_PLATFORM_FEE_PERCENT', 5.0) / 100))
            platform_fee = payment.amount * platform_fee_percent
            provider_amount = payment.amount - platform_fee
            
            payment.platform_fee = platform_fee
            payment.provider_amount = provider_amount
            payment.save()

            # Create PaymentIntent with destination charge if provider has Stripe account
            payment_intent_params = {
                'amount': int(payment.amount * 100),  # Convert to cents
                'currency': payment.currency.lower(),
                'metadata': {
                    'payment_id': str(payment.id),
                    'contract_id': str(payment.contract.id),
                    'payer_id': str(payment.payer.id),
                    'recipient_id': str(payment.recipient.id),
                },
                'description': payment.description or f"Payment for contract: {payment.contract.title}",
            }

            # If provider has Stripe Connect account, use destination charge
            if provider_profile and provider_profile.stripe_account_id and provider_profile.stripe_account_enabled:
                payment_intent_params['application_fee_amount'] = int(platform_fee * 100)
                payment_intent_params['on_behalf_of'] = provider_profile.stripe_account_id
                payment_intent_params['transfer_data'] = {
                    'destination': provider_profile.stripe_account_id,
                }
            # Otherwise, money goes to platform account (will need manual transfer later)

            payment_intent = stripe.PaymentIntent.create(**payment_intent_params)

            # Update payment with Stripe PaymentIntent ID
            payment.stripe_payment_intent_id = payment_intent.id
            payment.status = Payment.PaymentStatus.PROCESSING
            payment.save()

            # Create transaction record
            PaymentTransaction.objects.create(
                payment=payment,
                transaction_type=PaymentTransaction.TransactionType.PROCESSING,
                stripe_event_id=payment_intent.id,
                details={'payment_intent': payment_intent.id}
            )

            return Response({
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'payment_id': str(payment.id),
            }, status=status.HTTP_200_OK)

        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except stripe.error.StripeError as e:
            return Response(
                {'error': f'Stripe error: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class CreateStripeCheckoutSessionView(generics.GenericAPIView):
    """
    Create a Stripe Checkout Session for a payment. Client is redirected to Stripe's hosted page.
    When the provider has connected their Stripe account (profile), the charge is created on behalf
    of the provider: platform takes a fee, the rest is transferred to the provider's connected account.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StripeCheckoutSessionSerializer

    def post(self, request):
        serializer = StripeCheckoutSessionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        payment_id = serializer.validated_data['payment_id']
        success_url = serializer.validated_data.get('success_url', '').strip()
        cancel_url = serializer.validated_data.get('cancel_url', '').strip()

        try:
            payment = Payment.objects.get(id=payment_id)

            if payment.payer != request.user:
                return Response(
                    {'error': 'You can only create checkout sessions for your own payments.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
            if not stripe.api_key:
                return Response(
                    {'error': 'Stripe is not configured.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            provider_profile = None
            if hasattr(payment.recipient, 'profile') and hasattr(payment.recipient.profile, 'provider_profile'):
                provider_profile = payment.recipient.profile.provider_profile

            # Platform minimum: 25 ETB; Stripe also requires ~50 cents USD equivalent per session
            currency_code = (payment.currency or 'ETB').strip().upper()
            min_amounts = getattr(settings, 'STRIPE_CHECKOUT_MIN_AMOUNT_BY_CURRENCY', None) or {
                'USD': Decimal('0.50'),
                'ETB': Decimal('25'),   # Platform minimum 25 ETB
                'EUR': Decimal('0.50'),
                'GBP': Decimal('0.30'),
            }
            min_for_currency = min_amounts.get(currency_code)
            if min_for_currency is not None and payment.amount < min_for_currency:
                return Response(
                    {
                        'error': (
                            f'Payment amount must be at least {min_for_currency} {payment.currency}. '
                            'Please add more hours or wait until the total is higher.'
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            platform_fee_percent = Decimal(str(getattr(settings, 'STRIPE_PLATFORM_FEE_PERCENT', 5.0) / 100))
            platform_fee = payment.amount * platform_fee_percent
            provider_amount = payment.amount - platform_fee
            payment.platform_fee = platform_fee
            payment.provider_amount = provider_amount
            payment.status = Payment.PaymentStatus.PROCESSING
            payment.save()

            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            if not success_url:
                success_url = f"{frontend_url}/contracts/{payment.contract.id}?payment=success"
            if not cancel_url:
                cancel_url = f"{frontend_url}/payments/contract/{payment.contract.id}"

            line_items = [{
                'price_data': {
                    'currency': payment.currency.lower(),
                    'unit_amount': int(payment.amount * 100),
                    'product_data': {
                        'name': payment.description or f'Payment for contract',
                        'description': payment.contract.title[:500] if payment.contract else '',
                    },
                },
                'quantity': 1,
            }]

            payment_intent_data = {
                'metadata': {
                    'payment_id': str(payment.id),
                    'contract_id': str(payment.contract.id),
                    'payer_id': str(payment.payer.id),
                    'recipient_id': str(payment.recipient.id),
                },
            }
            if provider_profile and provider_profile.stripe_account_id and provider_profile.stripe_account_enabled:
                payment_intent_data['application_fee_amount'] = int(platform_fee * 100)
                payment_intent_data['transfer_data'] = {
                    'destination': provider_profile.stripe_account_id,
                }

            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                client_reference_id=str(payment.id),
                metadata={'payment_id': str(payment.id)},
                payment_intent_data=payment_intent_data,
            )

            PaymentTransaction.objects.create(
                payment=payment,
                transaction_type=PaymentTransaction.TransactionType.PROCESSING,
                stripe_event_id=session.id,
                details={'checkout_session_id': session.id}
            )

            return Response({
                'url': session.url,
                'session_id': session.id,
                'payment_id': str(payment.id),
            }, status=status.HTTP_200_OK)

        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except stripe.error.StripeError as e:
            err_msg = str(e)
            if '50 cents' in err_msg or 'total amount must convert' in err_msg.lower():
                return Response(
                    {
                        'error': (
                            'Payment amount must be at least 25 ETB. '
                            'Please add more hours or wait until the total is higher.'
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'error': err_msg},
                status=status.HTTP_400_BAD_REQUEST
            )


class CreateStripeCheckoutSessionForTimeEntriesView(generics.GenericAPIView):
    """
    Create a single Stripe Checkout Session for all approved, unpaid time entries of an hourly contract.
    One session with one line item per time entry; on completion all linked payments are marked COMPLETED.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        contract_id = request.data.get('contract_id')
        if not contract_id:
            return Response(
                {'error': 'contract_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            contract = Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            return Response(
                {'error': 'Contract not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        if contract.client != request.user:
            return Response(
                {'error': 'You can only create checkout for your own contract as client.'},
                status=status.HTTP_403_FORBIDDEN
            )
        if contract.payment_schedule != Contract.PaymentSchedule.HOURLY:
            return Response(
                {'error': 'This endpoint is for hourly contracts only.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from .models import Payment as PaymentModel
        entries = list(
            TimeEntry.objects.filter(
                contract=contract,
                status=TimeEntry.TimeEntryStatus.APPROVED
            ).select_related('contract')
        )
        # Exclude already paid
        paid_ids = set(
            PaymentModel.objects.filter(
                contract=contract,
                time_entry__isnull=False,
                status=PaymentModel.PaymentStatus.COMPLETED
            ).values_list('time_entry_id', flat=True)
        )
        entries = [e for e in entries if e.id not in paid_ids]
        if not entries:
            return Response(
                {'error': 'No approved unpaid time entries to pay.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        currency = (contract.currency or 'ETB').strip().upper()
        min_etb = Decimal('25')
        total_amount = sum((e.amount or Decimal('0')) for e in entries)
        if currency == 'ETB' and total_amount < min_etb:
            return Response(
                {
                    'error': (
                        f'Total payment must be at least {min_etb} ETB (current total: {total_amount} ETB). '
                        'Please add more hours or wait until the total is higher.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
        if not stripe.api_key:
            return Response(
                {'error': 'Stripe is not configured.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        platform_fee_percent = Decimal(str(getattr(settings, 'STRIPE_PLATFORM_FEE_PERCENT', 5.0) / 100))
        payments_created = []
        line_items = []
        for entry in entries:
            amount = entry.amount or Decimal('0')
            if amount <= 0:
                continue
            platform_fee = amount * platform_fee_percent
            provider_amount = amount - platform_fee
            desc = f'Time entry {entry.date} – {entry.hours}h'
            payment = PaymentModel.objects.create(
                contract=contract,
                payer=request.user,
                recipient=contract.provider,
                amount=amount,
                currency=currency,
                payment_method=PaymentModel.PaymentMethod.STRIPE,
                status=PaymentModel.PaymentStatus.PROCESSING,
                time_entry=entry,
                description=desc,
                platform_fee=platform_fee,
                provider_amount=provider_amount,
            )
            payments_created.append(payment)
            # Stripe unit_amount: for ETB use smallest unit (cents equivalent; Stripe expects integer)
            unit_amount = int(amount * 100)
            line_items.append({
                'price_data': {
                    'currency': currency.lower(),
                    'unit_amount': unit_amount,
                    'product_data': {
                        'name': f'Time entry: {entry.date} – {entry.hours}h',
                        'description': (contract.title or 'Contract')[:500],
                    },
                },
                'quantity': 1,
            })

        if not payments_created or not line_items:
            return Response(
                {'error': 'No valid time entries to pay.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment_ids_str = ','.join(str(p.id) for p in payments_created)
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        success_url = request.data.get('success_url', '').strip() or f"{frontend_url}/contracts/{contract.id}?payment=success"
        cancel_url = request.data.get('cancel_url', '').strip() or f"{frontend_url}/contracts/{contract.id}"

        provider_profile = None
        if hasattr(contract.provider, 'profile') and hasattr(contract.provider.profile, 'provider_profile'):
            provider_profile = contract.provider.profile.provider_profile
        payment_intent_data = {
            'metadata': {
                'payment_ids': payment_ids_str,
                'contract_id': str(contract.id),
                'payer_id': str(request.user.id),
                'recipient_id': str(contract.provider.id),
            },
        }
        if provider_profile and provider_profile.stripe_account_id and provider_profile.stripe_account_enabled:
            total_fee = sum((p.platform_fee or Decimal('0')) for p in payments_created)
            payment_intent_data['application_fee_amount'] = int(total_fee * 100)
            payment_intent_data['transfer_data'] = {
                'destination': provider_profile.stripe_account_id,
            }

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=payment_ids_str,
            metadata={'payment_ids': payment_ids_str},
            payment_intent_data=payment_intent_data,
        )

        for p in payments_created:
            PaymentTransaction.objects.create(
                payment=p,
                transaction_type=PaymentTransaction.TransactionType.PROCESSING,
                stripe_event_id=session.id,
                details={'checkout_session_id': session.id}
            )

        return Response({
            'url': session.url,
            'session_id': session.id,
            'payment_ids': payment_ids_str,
        }, status=status.HTTP_200_OK)


class ConfirmStripePaymentView(generics.GenericAPIView):
    """
    Confirm a Stripe payment after client completes payment
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)

            # Verify user is the payer
            if payment.payer != request.user:
                return Response(
                    {'error': 'You can only confirm your own payments.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Initialize Stripe
            stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
            if not stripe.api_key:
                return Response(
                    {'error': 'Stripe is not configured.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Retrieve PaymentIntent
            if not payment.stripe_payment_intent_id:
                return Response(
                    {'error': 'Payment intent not found.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            payment_intent = stripe.PaymentIntent.retrieve(
                payment.stripe_payment_intent_id
            )

            # Update payment status based on PaymentIntent status
            if payment_intent.status == 'succeeded':
                payment.status = Payment.PaymentStatus.COMPLETED
                payment.stripe_charge_id = payment_intent.latest_charge
                payment.completed_at = timezone.now()
                
                # Handle transfer if not using destination charge
                if payment_intent.get('transfer_data') and payment_intent['transfer_data'].get('destination'):
                    # Transfer already happened via destination charge
                    payment.stripe_transfer_id = payment_intent['transfer_data'].get('transfer', '')
                else:
                    # Manual transfer needed (provider doesn't have Stripe Connect)
                    # In production, you'd create a Transfer here or queue it
                    # For now, we'll mark it for manual processing
                    pass
                
                payment.save()

                # Update provider earnings if they have a profile
                if hasattr(payment.recipient, 'profile') and hasattr(payment.recipient.profile, 'provider_profile'):
                    provider_profile = payment.recipient.profile.provider_profile
                    provider_profile.total_earnings += payment.provider_amount or payment.amount
                    provider_profile.save()

                # Create transaction record
                PaymentTransaction.objects.create(
                    payment=payment,
                    transaction_type=PaymentTransaction.TransactionType.COMPLETED,
                    stripe_event_id=payment_intent.id,
                    details={
                        'charge_id': payment_intent.latest_charge,
                        'transfer_id': payment.stripe_transfer_id,
                        'provider_amount': str(payment.provider_amount),
                        'platform_fee': str(payment.platform_fee),
                    }
                )

                # Update milestone status if linked (legacy)
                if payment.milestone:
                    payment.milestone.status = ContractMilestone.MilestoneStatus.COMPLETED
                    payment.milestone.completed_at = timezone.now()
                    payment.milestone.save()
                # Update time entry status if linked (hourly)
                if payment.time_entry:
                    payment.time_entry.status = TimeEntry.TimeEntryStatus.PAID
                    payment.time_entry.save(update_fields=['status', 'updated_at'])

                return Response(
                    PaymentSerializer(payment).data,
                    status=status.HTTP_200_OK
                )
            elif payment_intent.status == 'requires_payment_method':
                return Response(
                    {'error': 'Payment requires a payment method.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {'error': f'Payment status: {payment_intent.status}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except stripe.error.StripeError as e:
            return Response(
                {'error': f'Stripe error: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['POST'])
@permission_classes([])  # No authentication required for webhooks
@csrf_exempt
def stripe_webhook(request):
    """
    Handle Stripe webhook events. For local testing use:
    stripe listen --forward-to localhost:8000/api/v1/payments/webhook/stripe/
    and set STRIPE_WEBHOOK_SECRET to the signing secret printed by the CLI.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info('[Stripe webhook] Request received')

    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)

    if not stripe.api_key:
        return JsonResponse({'error': 'Stripe is not configured.'}, status=500)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        else:
            # For development only: skip signature verification if no secret set
            import json
            event = json.loads(payload)
            logger.warning('[Stripe webhook] No STRIPE_WEBHOOK_SECRET set; signature not verified')
    except ValueError as e:
        logger.exception('[Stripe webhook] Invalid payload')
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.exception('[Stripe webhook] Invalid signature - check STRIPE_WEBHOOK_SECRET matches stripe listen secret')
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    logger.info('[Stripe webhook] Event type: %s', event.get('type'))

    # Handle the event
    event_type = event.get('type')
    data = event.get('data', {}).get('object', {})

    try:
        if event_type == 'checkout.session.completed':
            # Checkout Session completed: payment was made on Stripe's hosted page (on behalf of provider when Connect is used)
            session = data
            metadata = session.get('metadata') or {}
            payment_ids_str = (metadata.get('payment_ids') or '').strip()
            payment_id = (session.get('client_reference_id') or '').strip() or None
            if not payment_id:
                payment_id = metadata.get('payment_id') or ''
                payment_id = (payment_id or '').strip() or None
            # Bulk time-entry checkout: client_reference_id and metadata.payment_ids contain comma-separated payment ids
            payment_ids_list = [pid.strip() for pid in payment_ids_str.split(',') if pid.strip()] if payment_ids_str else []
            if not payment_ids_list and payment_id and ',' not in payment_id:
                payment_ids_list = [payment_id]
            elif payment_id and ',' in payment_id:
                payment_ids_list = [pid.strip() for pid in payment_id.split(',') if pid.strip()]
            payment_intent_id = session.get('payment_intent')
            if isinstance(payment_intent_id, dict):
                payment_intent_id = payment_intent_id.get('id')
            if isinstance(payment_intent_id, str):
                payment_intent_id = payment_intent_id.strip() or None
            print('[Stripe webhook] checkout.session.completed payment_ids=%r payment_intent=%s' % (payment_ids_list, payment_intent_id))
            logger.info('[Stripe webhook] checkout.session.completed payment_ids=%s payment_intent=%s', payment_ids_list, payment_intent_id)
            completed_any = False
            for pid in payment_ids_list:
                try:
                    payment = Payment.objects.filter(id=pid).first()
                except Exception:
                    payment = None
                if not payment:
                    continue
                payment.stripe_payment_intent_id = payment_intent_id or ''
                payment.status = Payment.PaymentStatus.COMPLETED
                payment.completed_at = timezone.now()
                if payment_intent_id:
                    try:
                        pi = stripe.PaymentIntent.retrieve(payment_intent_id)
                        payment.stripe_charge_id = pi.get('latest_charge') or ''
                    except Exception:
                        pass
                payment.save()
                PaymentTransaction.objects.create(
                    payment=payment,
                    transaction_type=PaymentTransaction.TransactionType.COMPLETED,
                    stripe_event_id=event.get('id'),
                    details={'checkout_session': session.get('id'), 'payment_intent': payment_intent_id}
                )
                if payment.milestone:
                    payment.milestone.status = ContractMilestone.MilestoneStatus.COMPLETED
                    payment.milestone.completed_at = timezone.now()
                    payment.milestone.save()
                if payment.time_entry:
                    payment.time_entry.status = TimeEntry.TimeEntryStatus.PAID
                    payment.time_entry.save(update_fields=['status', 'updated_at'])
                completed_any = True
                logger.info('[Stripe webhook] checkout.session.completed updated Payment id=%s to COMPLETED', payment.id)
            if not completed_any and not payment_ids_list:
                print('[Stripe webhook] checkout.session.completed WARNING: could not find Payment client_reference_id=%s' % payment_id)
                logger.warning('[Stripe webhook] checkout.session.completed could not find Payment client_reference_id=%s', payment_id)

        elif event_type == 'payment_intent.succeeded':
            payment_intent_id = data.get('id')
            metadata = data.get('metadata') or {}
            payment_id_from_metadata = (metadata.get('payment_id') or '').strip() or None
            payment = Payment.objects.filter(
                stripe_payment_intent_id=payment_intent_id
            ).first()
            # Checkout flow: PaymentIntent was created by Checkout Session; our Payment may not have stripe_payment_intent_id set yet. Find by metadata.
            if not payment and payment_id_from_metadata:
                payment = Payment.objects.filter(id=payment_id_from_metadata).first()
                if payment:
                    payment.stripe_payment_intent_id = payment_intent_id
                    logger.info('[Stripe webhook] payment_intent.succeeded found Payment via metadata payment_id=%s', payment_id_from_metadata)
            if not payment:
                print('[Stripe webhook] payment_intent.succeeded WARNING: could not find Payment pi=%s metadata.payment_id=%s' % (payment_intent_id, payment_id_from_metadata))
                logger.warning('[Stripe webhook] payment_intent.succeeded could not find Payment pi=%s metadata.payment_id=%s', payment_intent_id, payment_id_from_metadata)

            if payment:
                payment.status = Payment.PaymentStatus.COMPLETED
                payment.stripe_charge_id = data.get('latest_charge') or ''
                payment.completed_at = timezone.now()
                payment.save()

                PaymentTransaction.objects.create(
                    payment=payment,
                    transaction_type=PaymentTransaction.TransactionType.COMPLETED,
                    stripe_event_id=event.get('id'),
                    details={'charge_id': data.get('latest_charge')}
                )

                # Update milestone if linked (legacy)
                if payment.milestone:
                    payment.milestone.status = ContractMilestone.MilestoneStatus.COMPLETED
                    payment.milestone.completed_at = timezone.now()
                    payment.milestone.save()
                # Update time entry if linked (hourly)
                if payment.time_entry:
                    payment.time_entry.status = TimeEntry.TimeEntryStatus.PAID
                    payment.time_entry.save(update_fields=['status', 'updated_at'])
                logger.info('[Stripe webhook] payment_intent.succeeded updated Payment id=%s to COMPLETED', payment.id)

        elif event_type == 'payment_intent.payment_failed':
            payment_intent_id = data.get('id')
            payment = Payment.objects.filter(
                stripe_payment_intent_id=payment_intent_id
            ).first()

            if payment:
                payment.status = Payment.PaymentStatus.FAILED
                payment.failed_at = timezone.now()
                payment.save()

                PaymentTransaction.objects.create(
                    payment=payment,
                    transaction_type=PaymentTransaction.TransactionType.FAILED,
                    stripe_event_id=event.get('id'),
                    details={'error': data.get('last_payment_error', {})}
                )

        elif event_type == 'charge.refunded':
            charge_id = data.get('id')
            payment = Payment.objects.filter(stripe_charge_id=charge_id).first()

            if payment:
                payment.status = Payment.PaymentStatus.REFUNDED
                payment.stripe_refund_id = data.get('refunds', {}).get('data', [{}])[0].get('id', '')
                payment.save()

                PaymentTransaction.objects.create(
                    payment=payment,
                    transaction_type=PaymentTransaction.TransactionType.REFUNDED,
                    stripe_event_id=event.get('id'),
                    details={'refund_id': payment.stripe_refund_id}
                )

    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Error processing webhook: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'status': 'success'})


class PaymentHistoryView(generics.ListAPIView):
    """
    Get payment history for a user
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Payment.objects.filter(
            models.Q(payer=user) | models.Q(recipient=user)
        ).order_by('-created_at')


class StripeConnectOnboardView(generics.GenericAPIView):
    """
    Create Stripe Connect account and get onboarding link for provider
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        # Verify user is a provider
        if user.user_type not in ['PROVIDER', 'BOTH']:
            return Response(
                {'error': 'Only service providers can create Stripe Connect accounts.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if provider profile exists
        if not hasattr(user, 'profile') or not hasattr(user.profile, 'provider_profile'):
            return Response(
                {'error': 'Provider profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        provider_profile = user.profile.provider_profile

        # Check if already has Stripe account
        if provider_profile.stripe_account_id:
            return Response(
                {'error': 'Stripe account already exists. Use status endpoint to check status.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from .stripe_connect import create_stripe_connect_account
            result = create_stripe_connect_account(user)

            # Save account ID to provider profile
            provider_profile.stripe_account_id = result['account_id']
            provider_profile.save()

            return Response({
                'account_id': result['account_id'],
                'onboarding_url': result['onboarding_url'],
                'message': 'Redirect user to onboarding_url to complete setup'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            err_msg = str(e)
            # Only show friendly message for the specific "Connect not signed up" error
            if 'signed up for Connect' in err_msg:
                err_msg = (
                    'Stripe Connect is not enabled for this platform. '
                    'The platform owner must enable Connect in the Stripe Dashboard (https://dashboard.stripe.com/connect) '
                    'before providers can link their payout accounts.'
                )
            return Response(
                {'error': err_msg},
                status=status.HTTP_400_BAD_REQUEST
            )


class StripeConnectStatusView(generics.GenericAPIView):
    """
    Get Stripe Connect account status
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Check if provider profile exists
        if not hasattr(user, 'profile') or not hasattr(user.profile, 'provider_profile'):
            return Response(
                {'error': 'Provider profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        provider_profile = user.profile.provider_profile

        if not provider_profile.stripe_account_id:
            return Response({
                'has_account': False,
                'message': 'No Stripe account found. Use onboard endpoint to create one.'
            }, status=status.HTTP_200_OK)

        try:
            from .stripe_connect import get_stripe_account_status
            account_status = get_stripe_account_status(provider_profile.stripe_account_id)

            # Update provider profile status
            provider_profile.stripe_account_enabled = (
                account_status['charges_enabled'] and account_status['payouts_enabled']
            )
            provider_profile.stripe_onboarding_completed = account_status['details_submitted']
            provider_profile.save()

            return Response({
                'has_account': True,
                'account_id': account_status['id'],
                'charges_enabled': account_status['charges_enabled'],
                'payouts_enabled': account_status['payouts_enabled'],
                'details_submitted': account_status['details_submitted'],
                'enabled': provider_profile.stripe_account_enabled,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class StripeConnectLoginView(generics.GenericAPIView):
    """
    Get Stripe Express account login link
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Check if provider profile exists
        if not hasattr(user, 'profile') or not hasattr(user.profile, 'provider_profile'):
            return Response(
                {'error': 'Provider profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        provider_profile = user.profile.provider_profile

        if not provider_profile.stripe_account_id:
            return Response(
                {'error': 'No Stripe account found. Use onboard endpoint to create one.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from .stripe_connect import create_stripe_login_link
            login_url = create_stripe_login_link(provider_profile.stripe_account_id)

            return Response({
                'login_url': login_url,
                'message': 'Redirect user to login_url to access their Stripe Express dashboard'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
