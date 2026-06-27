from django.contrib import admin
from .models import ShippingConfig, Courier


@admin.register(ShippingConfig)
class ShippingConfigAdmin(admin.ModelAdmin):
    list_display = ['origin_district', 'origin_city', 'origin_province', 'default_weight', 'cache_ttl']
    fieldsets = (
        ('Alamat Asal (Warehouse)', {
            'fields': ('origin_province', 'origin_city', 'origin_district', 'origin_district_code'),
        }),
        ('Pengaturan Pengiriman', {
            'fields': ('default_weight', 'cache_ttl', 'enabled_couriers'),
        }),
    )

    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Courier)
class CourierAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']
    search_fields = ['code', 'name']
