from django.urls import include, path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('member-benefits/', views.member_benefits, name='member_benefits'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('member/', views.member_dashboard, name='member_dashboard'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.ProfileUpdateView.as_view(), name='profile'),
    path('forgot-password/', auth_views.PasswordResetView.as_view(
        template_name='accounts/forgot_password.html',
        email_template_name='registration/password_reset_email.html',
        success_url=reverse_lazy('accounts:password_reset_sent'),
    ), name='forgot_password'),
    path('forgot-password/sent/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_sent.html',
    ), name='password_reset_sent'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/create_new_password.html',
        success_url=reverse_lazy('accounts:password_reset_success'),
    ), name='create_new_password'),
    path('reset/success/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_success.html',
    ), name='password_reset_success'),
    path('wishlist/', views.wishlist_list, name='wishlist_list'),
    path('wishlist/add/<int:product_id>/', views.wishlist_add, name='wishlist_add'),
    path('wishlist/remove/<int:product_id>/', views.wishlist_remove, name='wishlist_remove'),
    path('dashboard/addresses/', views.address_list, name='address_list'),
    path('dashboard/addresses/create/', views.address_create, name='address_create'),
    path('dashboard/addresses/<int:address_id>/edit/', views.address_edit, name='address_edit'),
    path('dashboard/addresses/<int:address_id>/delete/', views.address_delete, name='address_delete'),
    path('dashboard/addresses/<int:address_id>/set-default/', views.address_set_default, name='address_set_default'),
]
