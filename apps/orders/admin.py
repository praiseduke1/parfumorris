from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from apps.core.admin_utils import format_rupiah, status_badge_html as _status_badge_html

from .models import Order, OrderItem, OrderStatusHistory, Voucher


def status_badge_html(status):
    colors = {
        'pending_payment': ('badge badge-warning', 'Pending Payment'),
        'paid': ('badge badge-info', 'Paid'),
        'processing': ('badge badge-primary', 'Processing'),
        'shipped': ('badge badge-dark', 'Shipped'),
        'delivered': ('badge badge-success', 'Delivered'),
        'completed': ('badge badge-success', 'Completed'),
        'cancelled': ('badge badge-danger', 'Cancelled'),
    }
    return _status_badge_html(status, colors)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'price', 'quantity', 'item_total']
    can_delete = False

    def item_total(self, obj):
        return format_rupiah(obj.total_price())
    item_total.short_description = 'Subtotal'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['status', 'notes', 'created_at']
    can_delete = False
    ordering = ['created_at']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user_link', 'status_badge', 'total_price_formatted', 'item_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'user__username', 'user__email']
    autocomplete_fields = ['user', 'voucher', 'product_voucher', 'shipping_voucher']
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    list_select_related = ['user', 'voucher', 'product_voucher', 'shipping_voucher']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['order_number', 'subtotal', 'discount_amount', 'product_discount', 'shipping_discount',
                       'shipping_cost', 'total_price', 'created_at', 'updated_at',
                       'paid_at', 'processing_at', 'shipped_at', 'delivered_at', 'completed_at']
    actions = ['mark_as_paid', 'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_completed', 'mark_as_cancelled']

    fieldsets = (
        ('Informasi Pesanan', {
            'fields': ('order_number', 'user', 'status', 'voucher', 'product_voucher', 'shipping_voucher',
                       'subtotal', 'discount_amount', 'product_discount', 'shipping_discount',
                       'shipping_cost', 'total_price')
        }),
        ('Alamat Pengiriman', {
            'fields': ('recipient_name', 'phone', 'shipping_address', 'city', 'province', 'district', 'postal_code', 'notes'),
            'classes': ('collapse',)
        }),
        ('Informasi Pengiriman', {
            'fields': ('shipping_courier', 'shipping_service', 'shipping_estimation', 'shipping_weight', 'shipping_origin', 'shipping_destination', 'tracking_number'),
        }),
        ('Waktu Status', {
            'fields': ('paid_at', 'processing_at', 'shipped_at', 'delivered_at', 'completed_at'),
        }),
        ('Waktu Sistem', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Pengguna'
    user_link.admin_order_field = 'user'

    def status_badge(self, obj):
        return status_badge_html(obj.status)
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def total_price_formatted(self, obj):
        return format_rupiah(obj.total_price)
    total_price_formatted.short_description = 'Total'
    total_price_formatted.admin_order_field = 'total_price'

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Item'

    def _update_status(self, request, queryset, target_status, from_statuses, success_msg, exclude_statuses=None):
        count = 0
        details = []
        for order in queryset.all():
            old_status = order.status
            if exclude_statuses and old_status in exclude_statuses:
                continue
            if from_statuses and old_status not in from_statuses:
                continue
            order.status = target_status
            order.save()
            order.refresh_from_db()
            details.append(f'{order.order_number}: {old_status} → {target_status}')
            count += 1
        if count:
            self.message_user(request, f'{success_msg.format(count)}\n' + '\n'.join(details))
        else:
            self.message_user(request, 'Tidak ada pesanan yang memenuhi syarat untuk perubahan status ini.')

    def mark_as_paid(self, request, queryset):
        self._update_status(request, queryset, Order.Status.PAID,
            from_statuses=[Order.Status.PENDING_PAYMENT],
            success_msg='{} pesanan dikonfirmasi pembayarannya.')
    mark_as_paid.short_description = 'Konfirmasi pembayaran'

    def mark_as_processing(self, request, queryset):
        self._update_status(request, queryset, Order.Status.PROCESSING,
            from_statuses=[Order.Status.PAID],
            success_msg='{} pesanan diproses.')
    mark_as_processing.short_description = 'Proses pesanan terpilih'

    def mark_as_shipped(self, request, queryset):
        self._update_status(request, queryset, Order.Status.SHIPPED,
            from_statuses=[Order.Status.PROCESSING],
            success_msg='{} pesanan dikirim.')
    mark_as_shipped.short_description = 'Tandai terkirim'

    def mark_as_delivered(self, request, queryset):
        self._update_status(request, queryset, Order.Status.DELIVERED,
            from_statuses=[Order.Status.SHIPPED],
            success_msg='{} pesanan sampai.')
    mark_as_delivered.short_description = 'Tandai sampai tujuan'

    def mark_as_completed(self, request, queryset):
        self._update_status(request, queryset, Order.Status.COMPLETED,
            from_statuses=[Order.Status.DELIVERED],
            success_msg='{} pesanan selesai.')
    mark_as_completed.short_description = 'Selesaikan pesanan'

    def mark_as_cancelled(self, request, queryset):
        self._update_status(request, queryset, Order.Status.CANCELLED,
            from_statuses=None,
            exclude_statuses=[Order.Status.DELIVERED, Order.Status.COMPLETED],
            success_msg='{} pesanan dibatalkan.')
    mark_as_cancelled.short_description = 'Batalkan pesanan terpilih'


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    readonly_fields = ['order', 'status', 'notes', 'created_at']
    search_fields = ['order__order_number']
    autocomplete_fields = ['order']

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_amount_formatted', 'min_purchase_formatted',
                    'used_count', 'max_uses', 'is_active', 'valid_from', 'valid_until']
    list_filter = ['discount_type', 'is_active', 'valid_from', 'valid_until']
    search_fields = ['code', 'discount_type']
    ordering = ['-created_at']
    readonly_fields = ['used_count', 'created_at', 'updated_at']

    fieldsets = (
        ('Informasi Voucher', {
            'fields': ('code', 'discount_type', 'discount_amount', 'is_active')
        }),
        ('Ketentuan', {
            'fields': ('min_purchase', 'max_discount', 'max_uses', 'used_count')
        }),
        ('Periode', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Waktu', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def discount_amount_formatted(self, obj):
        if obj.discount_type == Voucher.DiscountType.PERCENTAGE:
            return f'{obj.discount_amount}%'
        return format_rupiah(obj.discount_amount)
    discount_amount_formatted.short_description = 'Diskon'

    def min_purchase_formatted(self, obj):
        return format_rupiah(obj.min_purchase) if obj.min_purchase else '0'
    min_purchase_formatted.short_description = 'Min. Belanja'
