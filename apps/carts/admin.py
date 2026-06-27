from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['product', 'variant', 'quantity', 'unit_price', 'total_price']
    autocomplete_fields = ['product']

    def unit_price(self, obj):
        return obj.unit_price()

    def total_price(self, obj):
        return obj.total_price()


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'total_price', 'created_at']
    list_filter = ['created_at']
    list_select_related = ['user']
    search_fields = ['user__username', 'user__email']
    autocomplete_fields = ['user']
    date_hierarchy = 'created_at'
    inlines = [CartItemInline]
