from django.urls import path
from . import views

app_name = 'shipping'

urlpatterns = [
    path('api/cost/', views.api_shipping_cost, name='api_cost'),
    path('api/select/', views.api_select_shipping, name='api_select'),
    path('api/clear/', views.api_clear_shipping, name='api_clear'),
]
