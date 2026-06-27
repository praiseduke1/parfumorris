from django.urls import path
from . import views

app_name = 'carts'

urlpatterns = [
    path('', views.cart_detail, name='detail'),
    path('add/<int:product_id>/', views.cart_add, name='add'),
    path('update/<int:item_id>/', views.cart_update, name='update'),
    path('remove/<int:item_id>/', views.cart_remove, name='remove'),
    path('voucher/apply/', views.apply_voucher, name='apply_voucher'),
    path('voucher/remove/', views.remove_voucher, name='remove_voucher'),
]
