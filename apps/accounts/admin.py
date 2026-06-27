from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode

from apps.core.admin_utils import format_rupiah

from .models import Profile, MemberProfile, PointTransaction, CustomerAddress, Wishlist

admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'order_count', 'total_spending_formatted', 'is_active', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    date_hierarchy = 'date_joined'

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _order_count=Count('orders', distinct=True),
            _total_spending=Sum('orders__total_price', distinct=True),
        )

    def order_count(self, obj):
        count = getattr(obj, '_order_count', 0)
        url = reverse('admin:orders_order_changelist') + '?' + urlencode({'user__id__exact': obj.id})
        return format_html('<a href="{}">{}</a>', url, count)
    order_count.short_description = 'Pesanan'
    order_count.admin_order_field = '_order_count'

    def total_spending_formatted(self, obj):
        total = getattr(obj, '_total_spending', 0) or 0
        return format_rupiah(total)
    total_spending_formatted.short_description = 'Total Belanja'
    total_spending_formatted.admin_order_field = '_total_spending'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'created_at']
    search_fields = ['user__username', 'phone']
    autocomplete_fields = ['user']
    date_hierarchy = 'created_at'


@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'label', 'recipient_name', 'city', 'district', 'is_default']
    list_select_related = ['user', 'province', 'city', 'district']
    list_filter = ['is_default', 'city__province', 'city']
    search_fields = ['user__username', 'recipient_name', 'label']
    autocomplete_fields = ['user', 'province', 'city', 'district', 'postal_code']
    date_hierarchy = 'created_at'


@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'level', 'total_points', 'total_spending_formatted', 'created_at']
    list_select_related = ['user']
    list_filter = ['level', 'created_at']
    search_fields = ['user__username']
    autocomplete_fields = ['user']
    readonly_fields = ['total_points', 'total_spending', 'created_at', 'updated_at']

    def total_spending_formatted(self, obj):
        return format_rupiah(obj.total_spending)
    total_spending_formatted.short_description = 'Total Belanja'


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'points', 'type', 'description', 'created_at']
    list_select_related = ['user']
    list_filter = ['type', 'created_at']
    search_fields = ['user__username', 'description']
    autocomplete_fields = ['user']
    readonly_fields = ['user', 'points', 'type', 'description', 'created_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_select_related = ['user', 'product']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__name']
    autocomplete_fields = ['user', 'product']
    date_hierarchy = 'created_at'
