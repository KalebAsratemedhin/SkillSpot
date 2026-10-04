from django.contrib import admin
from .models import Payment, PaymentTransaction


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'contract', 'payer', 'recipient', 'amount', 'currency',
        'status', 'payment_method', 'created_at', 'completed_at'
    )
    list_filter = ('status', 'payment_method', 'currency', 'created_at', 'completed_at')
    search_fields = (
        'payer__email', 'recipient__email', 'contract__title',
        'stripe_payment_intent_id', 'stripe_charge_id'
    )
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'completed_at', 'failed_at',
        'stripe_payment_intent_id', 'stripe_charge_id', 'stripe_refund_id'
    )
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'contract', 'milestone', 'payer', 'recipient')
        }),
        ('Payment Details', {
            'fields': ('amount', 'currency', 'status', 'payment_method', 'description')
        }),
        ('Stripe Information', {
            'fields': (
                'stripe_payment_intent_id', 'stripe_charge_id', 'stripe_refund_id'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at', 'failed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment', 'transaction_type', 'stripe_event_id', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('payment__id', 'stripe_event_id')
    readonly_fields = ('id', 'created_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'payment', 'transaction_type')
        }),
        ('Stripe Information', {
            'fields': ('stripe_event_id',),
            'classes': ('collapse',)
        }),
        ('Details', {
            'fields': ('details',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
