from django.contrib import admin
from django.db.models import Count, Q
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from apps.core.admin_utils import format_rupiah

from .models import Voucher, UserVoucher


class UserVoucherInline(admin.TabularInline):
    model = UserVoucher
    extra = 0
    readonly_fields = ['user', 'voucher', 'status', 'assigned_at', 'used_at', 'expires_at']
    can_delete = False
    max_num = 10

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ['code', 'description', 'category_badge', 'discount_display',
                    'min_purchase', 'quota_display', 'expired_date', 'is_active_badge']
    list_filter = ['category', 'is_active', 'voucher_type', 'start_date', 'expired_date']
    search_fields = ['code', 'description']
    ordering = ['-created_at']
    readonly_fields = ['claimed_count', 'used_count', 'updated_at']
    inlines = [UserVoucherInline]

    fieldsets = (
        ('Informasi Voucher', {
            'fields': ('code', 'description', 'category', 'discount_type', 'discount_amount', 'is_active')
        }),
        ('Distribusi', {
            'fields': ('voucher_type', 'auto_assign', 'quota'),
        }),
        ('Ketentuan', {
            'fields': ('min_purchase', 'max_discount', 'min_transactions'),
        }),
        ('Periode', {
            'fields': ('start_date', 'expired_date'),
        }),
        ('Statistik Penggunaan', {
            'fields': ('claimed_count', 'used_count', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    actions = ['mark_active', 'mark_inactive']

    def discount_display(self, obj):
        if obj.discount_type == Voucher.DiscountType.PERCENTAGE:
            return f'{obj.discount_amount}%'
        return format_rupiah(obj.discount_amount)
    discount_display.short_description = 'Diskon'

    def category_badge(self, obj):
        if obj.category == Voucher.Category.PRODUCT:
            return mark_safe('<span style="display:inline-flex;align-items:center;gap:4px;padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600;background:#F97316;color:white;">🟠 Produk</span>')
        return mark_safe('<span style="display:inline-flex;align-items:center;gap:4px;padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600;background:#0EA5E9;color:white;">🔵 Ongkir</span>')
    category_badge.short_description = 'Jenis Voucher'
    category_badge.admin_order_field = 'category'

    def quota_display(self, obj):
        if obj.quota == 0:
            return '♾ Tidak terbatas'
        remaining = obj.remaining_quota()
        pct = round(obj.claimed_count / obj.quota * 100) if obj.quota else 0
        return f'{obj.claimed_count}/{obj.quota} ({pct}%)'
    quota_display.short_description = 'Kuota'
    quota_display.admin_order_field = 'quota'

    def is_active_badge(self, obj):
        if obj.is_active:
            return mark_safe('<span class="badge badge-success">Aktif</span>')
        return mark_safe('<span class="badge badge-danger">Nonaktif</span>')
    is_active_badge.short_description = 'Status'
    is_active_badge.admin_order_field = 'is_active'

    def mark_active(self, request, queryset):
        queryset.update(is_active=True)
    mark_active.short_description = 'Aktifkan voucher terpilih'

    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)
    mark_inactive.short_description = 'Nonaktifkan voucher terpilih'


@admin.register(UserVoucher)
class UserVoucherAdmin(admin.ModelAdmin):
    list_display = ['user', 'voucher_code', 'voucher_category_display', 'status_badge',
                    'assigned_at', 'expires_at', 'used_at']
    list_filter = ['status', 'voucher__category', 'voucher__voucher_type', 'assigned_at']
    search_fields = ['user__username', 'user__email', 'voucher__code']
    autocomplete_fields = ['user', 'voucher']
    readonly_fields = ['assigned_at', 'used_at']
    ordering = ['-assigned_at']
    date_hierarchy = 'assigned_at'

    fieldsets = (
        ('Informasi', {
            'fields': ('user', 'voucher', 'status')
        }),
        ('Waktu', {
            'fields': ('assigned_at', 'used_at', 'expires_at'),
        }),
    )

    def voucher_code(self, obj):
        return obj.voucher.code
    voucher_code.short_description = 'Kode Voucher'
    voucher_code.admin_order_field = 'voucher__code'

    def voucher_category_display(self, obj):
        return obj.voucher.get_category_display()
    voucher_category_display.short_description = 'Jenis'
    voucher_category_display.admin_order_field = 'voucher__category'

    def status_badge(self, obj):
        colors = {
            'available': 'badge badge-success',
            'used': 'badge badge-secondary',
            'expired': 'badge badge-danger',
        }
        cls = colors.get(obj.status, 'badge badge-secondary')
        return format_html('<span class="{}">{}</span>', cls, obj.get_status_display())
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
