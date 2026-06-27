from django.contrib import admin
from django.shortcuts import render
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core.admin_dashboard import dashboard_view


def handler404(request, exception):
    return render(request, 'errors/404.html', status=404)

urlpatterns = [
    path('admin/dashboard/', dashboard_view, name='admin_dashboard'),
    path('admin/', admin.site.urls),
    path('', include('apps.products.urls')),
    path('', include('apps.regions.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('cart/', include('apps.carts.urls')),
    path('orders/', include('apps.orders.urls')),
    path('payment/', include('apps.payments.urls')),
    path('promotions/', include('apps.promotions.urls')),
    path('shipping/', include('apps.shipping.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
