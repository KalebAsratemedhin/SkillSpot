"""
Stripe Connect utilities for provider onboarding and account management.

Platform requirement: The Stripe account (STRIPE_SECRET_KEY) must have Connect
enabled. Enable it at https://dashboard.stripe.com/connect — otherwise
creating connected accounts will fail with "You can only create new accounts
if you've signed up for Connect".
"""
import stripe
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


# Countries that support card_payments (see https://stripe.com/global).
# For others (e.g. ET), only request transfers for cross-border payouts.
CARD_PAYMENTS_COUNTRIES = frozenset(['US', 'CA', 'GB', 'AU', 'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE', 'CH', 'JP', 'SG', 'NZ', 'BR', 'MX'])


def create_stripe_connect_account(user):
    """
    Create a Stripe Connect Express account for a provider
    Returns the account ID and onboarding link
    """
    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
    if not stripe.api_key:
        raise ValueError('Stripe is not configured.')

    country = getattr(settings, 'STRIPE_CONNECT_DEFAULT_COUNTRY', 'ET')
    # For ET (and similar), do not include card_payments at all — Stripe rejects it.
    # Only request transfers for payouts (see https://stripe.com/docs/connect/cross-border-payouts).
    capabilities = {'transfers': {'requested': True}}
    if country in CARD_PAYMENTS_COUNTRIES:
        capabilities['card_payments'] = {'requested': True}

    try:
        # Create Express account (for ET: only transfers; no card_payments key sent)
        account = stripe.Account.create(
            type='express',
            country=country,
            email=user.email,
            capabilities=capabilities,
            metadata={
                'user_id': str(user.id),
                'user_email': user.email,
            }
        )

        # Create account link for onboarding
        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url=f"{settings.FRONTEND_URL}/stripe/onboarding/refresh",
            return_url=f"{settings.FRONTEND_URL}/stripe/onboarding/return",
            type='account_onboarding',
        )

        return {
            'account_id': account.id,
            'onboarding_url': account_link.url,
        }
    except stripe.error.StripeError as e:
        raise Exception(f'Stripe error: {str(e)}')


def get_stripe_account_status(account_id):
    """
    Get the status of a Stripe Connect account
    """
    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
    if not stripe.api_key:
        raise ValueError('Stripe is not configured.')

    try:
        account = stripe.Account.retrieve(account_id)
        return {
            'id': account.id,
            'charges_enabled': account.charges_enabled,
            'payouts_enabled': account.payouts_enabled,
            'details_submitted': account.details_submitted,
            'email': account.email,
        }
    except stripe.error.StripeError as e:
        raise Exception(f'Stripe error: {str(e)}')


def create_stripe_login_link(account_id):
    """
    Create a login link for a Stripe Connect account (for Express accounts)
    """
    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
    if not stripe.api_key:
        raise ValueError('Stripe is not configured.')

    try:
        login_link = stripe.Account.create_login_link(account_id)
        return login_link.url
    except stripe.error.StripeError as e:
        raise Exception(f'Stripe error: {str(e)}')
