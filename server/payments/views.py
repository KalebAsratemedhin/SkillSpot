import stripe
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
from contracts.models import ContractMilestone
from .serializers import (
    PaymentSerializer,
    PaymentCreateSerializer,
    PaymentTransactionSerializer,
    StripePaymentIntentSerializer,
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

        return queryset.distinct()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PaymentCreateSerializer
        return PaymentSerializer

    def perform_create(self, serializer):
        serializer.save(payer=self.request.user)


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
            platform_fee_percent = getattr(settings, 'STRIPE_PLATFORM_FEE_PERCENT', 5.0) / 100
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

                # Update milestone status if linked
                if payment.milestone:
                    payment.milestone.status = ContractMilestone.MilestoneStatus.COMPLETED
                    payment.milestone.completed_at = timezone.now()
                    payment.milestone.save()

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
    Handle Stripe webhook events
    """
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
            # For development, skip signature verification
            import json
            event = json.loads(payload)
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    # Handle the event
    event_type = event.get('type')
    data = event.get('data', {}).get('object', {})

    try:
        if event_type == 'payment_intent.succeeded':
            payment_intent_id = data.get('id')
            payment = Payment.objects.filter(
                stripe_payment_intent_id=payment_intent_id
            ).first()

            if payment:
                payment.status = Payment.PaymentStatus.COMPLETED
                payment.stripe_charge_id = data.get('latest_charge')
                payment.completed_at = timezone.now()
                payment.save()

                PaymentTransaction.objects.create(
                    payment=payment,
                    transaction_type=PaymentTransaction.TransactionType.COMPLETED,
                    stripe_event_id=event.get('id'),
                    details={'charge_id': data.get('latest_charge')}
                )

                # Update milestone if linked
                if payment.milestone:
                    payment.milestone.status = ContractMilestone.MilestoneStatus.COMPLETED
                    payment.milestone.completed_at = timezone.now()
                    payment.milestone.save()

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
            return Response(
                {'error': str(e)},
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
