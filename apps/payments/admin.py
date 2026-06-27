from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from apps.core.admin_utils import format_rupiah, status_badge_html as _status_badge_html

from .models import Payment, PaymentStatusHistory


def status_badge_html(status):
    colors = {
        'pending': ('badge badge-warning', 'Pending'),
        'success': ('badge badge-success', 'Success'),
        'failed': ('badge badge-danger', 'Failed'),
        'expired': ('badge badge-secondary', 'Expired'),
    }
    return _status_badge_html(status, colors)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order_link', 'transaction_id_short', 'payment_method', 'amount_formatted', 'status_colored', 'payment_time']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order__order_number', 'transaction_id', 'payment_method']
    autocomplete_fields = ['order']
    readonly_fields = ['snap_token', 'snap_redirect_url', 'raw_response', 'created_at', 'updated_at']
    list_select_related = ['order']
    ordering = ['-created_at']

    fieldsets = (
        ('Informasi Pembayaran', {
            'fields': ('order', 'transaction_id', 'payment_method', 'amount', 'status', 'payment_time')
        }),
        ('Midtrans Detail', {
            'fields': ('snap_token', 'snap_redirect_url', 'fraud_status'),
            'classes': ('collapse',)
        }),
        ('Raw Response', {
            'fields': ('raw_response',),
            'classes': ('collapse',)
        }),
        ('Waktu', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def order_link(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
    order_link.short_description = 'Pesanan'
    order_link.admin_order_field = 'order'

    def transaction_id_short(self, obj):
        if obj.transaction_id and len(obj.transaction_id) > 25:
            return format_html(
                '<span title="{}">{}</span>',
                obj.transaction_id,
                obj.transaction_id[:22] + '...'
            )
        return obj.transaction_id or '-'
    transaction_id_short.short_description = 'ID Transaksi'

    def amount_formatted(self, obj):
        return format_rupiah(obj.amount)
    amount_formatted.short_description = 'Jumlah'
    amount_formatted.admin_order_field = 'amount'

    def status_colored(self, obj):
        return status_badge_html(obj.status)
    status_colored.short_description = 'Status'
    status_colored.admin_order_field = 'status'


@admin.register(PaymentStatusHistory)
class PaymentStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['payment', 'from_status', 'to_status', 'created_at']
    list_filter = ['to_status', 'created_at']
    readonly_fields = ['payment', 'from_status', 'to_status', 'raw_response', 'created_at']
    search_fields = ['payment__order__order_number']
    autocomplete_fields = ['payment']

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
