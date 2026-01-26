from django.contrib import admin
from .models import Contract, ContractMilestone, ContractSignature


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'provider', 'status', 'total_amount', 'currency', 'start_date', 'created_at')
    list_filter = ('status', 'currency', 'created_at', 'start_date')
    search_fields = ('title', 'client__email', 'provider__email', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at', 'signed_at', 'completed_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title', 'description', 'terms')
        }),
        ('Parties', {
            'fields': ('client', 'provider')
        }),
        ('Job Information', {
            'fields': ('job', 'job_application'),
            'classes': ('collapse',)
        }),
        ('Financial', {
            'fields': ('total_amount', 'currency')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('status', 'signed_at', 'completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ContractMilestone)
class ContractMilestoneAdmin(admin.ModelAdmin):
    list_display = ('title', 'contract', 'amount', 'status', 'due_date', 'order', 'created_at')
    list_filter = ('status', 'created_at', 'due_date')
    search_fields = ('title', 'contract__title', 'description')
    readonly_fields = ('id', 'completed_at', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'contract', 'title', 'description')
        }),
        ('Details', {
            'fields': ('amount', 'due_date', 'order', 'status')
        }),
        ('Timestamps', {
            'fields': ('completed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ContractSignature)
class ContractSignatureAdmin(admin.ModelAdmin):
    list_display = ('contract', 'signer', 'is_signed', 'signature_type', 'signed_at', 'created_at')
    list_filter = ('is_signed', 'signature_type', 'signed_at', 'created_at')
    search_fields = ('contract__title', 'signer__email')
    readonly_fields = ('id', 'signed_at', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'contract', 'signer', 'is_signed')
        }),
        ('Signature Details', {
            'fields': ('signature_data', 'signature_type')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'signed_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
