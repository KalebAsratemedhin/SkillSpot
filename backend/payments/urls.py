from django.urls import path
from .views import (
    PaymentListCreateView,
    PaymentDetailView,
    CreateStripePaymentIntentView,
    CreateStripeCheckoutSessionView,
    CreateStripeCheckoutSessionForTimeEntriesView,
    ConfirmStripePaymentView,
    stripe_webhook,
    PaymentHistoryView,
    StripeConnectOnboardView,
    StripeConnectStatusView,
    StripeConnectLoginView,
)

app_name = 'payments'

urlpatterns = [
    path('', PaymentListCreateView.as_view(), name='payment_list_create'),
    path('<uuid:id>/', PaymentDetailView.as_view(), name='payment_detail'),
    path('create-intent/', CreateStripePaymentIntentView.as_view(), name='create_stripe_payment_intent'),
    path('create-checkout-session/', CreateStripeCheckoutSessionView.as_view(), name='create_stripe_checkout_session'),
    path('create-checkout-session-time-entries/', CreateStripeCheckoutSessionForTimeEntriesView.as_view(), name='create_stripe_checkout_session_time_entries'),
    path('<uuid:payment_id>/confirm/', ConfirmStripePaymentView.as_view(), name='confirm_stripe_payment'),
    path('webhook/stripe/', stripe_webhook, name='stripe_webhook'),
    path('history/', PaymentHistoryView.as_view(), name='payment_history'),
    # Stripe Connect endpoints
    path('stripe-connect/onboard/', StripeConnectOnboardView.as_view(), name='stripe_connect_onboard'),
    path('stripe-connect/status/', StripeConnectStatusView.as_view(), name='stripe_connect_status'),
    path('stripe-connect/login/', StripeConnectLoginView.as_view(), name='stripe_connect_login'),
]
