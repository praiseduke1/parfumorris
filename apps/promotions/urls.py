from django.urls import path
from . import views

app_name = 'promotions'

urlpatterns = [
    path('', views.voucher_list, name='voucher_list'),
    path('saya/', views.my_vouchers, name='my_vouchers'),
    path('claim/<int:voucher_id>/', views.claim_voucher_view, name='claim_voucher'),
    path('claim/<int:voucher_id>/ajax/', views.claim_voucher_ajax, name='claim_voucher_ajax'),
    path('api/my/', views.api_my_vouchers, name='api_my_vouchers'),
    path('api/select/', views.api_select_voucher, name='api_select_voucher'),
    path('api/remove/', views.api_remove_voucher, name='api_remove_voucher'),
    path('api/calculate/', views.api_calculate_totals, name='api_calculate_totals'),
]
