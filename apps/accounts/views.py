from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme

from django.db.models import Q
from django.utils.timezone import now

from apps.core.decorators import customer_required
from apps.core.mixins import CustomerRequiredMixin
from .forms import CustomerAddressForm, LoginForm, RegisterForm, ProfileUpdateForm
from .models import (
    CustomerAddress, LEVEL_BENEFITS, MemberProfile,
    PointTransaction, Profile, Wishlist,
)
from apps.orders.models import Order
from apps.products.models import Product


def member_benefits(request):
    return render(request, 'accounts/member_benefits.html', {
        'levels_data': LEVEL_BENEFITS,
    })


@login_required
@customer_required
def dashboard(request):
    orders = Order.objects.filter(user=request.user).select_related('payment').prefetch_related('items').order_by('-created_at')
    order_count = orders.count()
    completed_count = orders.filter(status=Order.Status.DELIVERED).count()
    pending_count = orders.filter(status=Order.Status.PENDING_PAYMENT).count()
    cancelled_count = orders.filter(status=Order.Status.CANCELLED).count()
    in_progress_count = order_count - completed_count - cancelled_count

    try:
        profile = request.user.profile
    except AttributeError:
        profile = None

    from apps.promotions.models import UserVoucher
    voucher_available = UserVoucher.objects.filter(
        user=request.user, status=UserVoucher.Status.AVAILABLE,
        expires_at__gt=now(),
    ).count()
    voucher_used = UserVoucher.objects.filter(
        user=request.user, status=UserVoucher.Status.USED,
    ).count()
    voucher_expired = UserVoucher.objects.filter(
        user=request.user,
    ).filter(
        Q(status=UserVoucher.Status.EXPIRED) |
        Q(status=UserVoucher.Status.AVAILABLE, expires_at__lte=now())
    ).count()

    context = {
        'orders': orders,
        'order_count': order_count,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'cancelled_count': cancelled_count,
        'in_progress_count': in_progress_count,
        'profile': profile,
        'voucher_available': voucher_available,
        'voucher_used': voucher_used,
        'voucher_expired': voucher_expired,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
@customer_required
def member_dashboard(request):
    member, _ = MemberProfile.objects.get_or_create(user=request.user)
    points_history = PointTransaction.objects.filter(user=request.user)[:20]
    levels_data = LEVEL_BENEFITS
    context = {
        'member': member,
        'levels_data': levels_data,
        'points_history': points_history,
    }
    return render(request, 'accounts/member_dashboard.html', context)


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'

    def get_success_url(self):
        return reverse_lazy('accounts:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Daftar Akun'
        context['next'] = self.request.GET.get('next', '')
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        from apps.promotions.services import assign_welcome_voucher
        assign_welcome_voucher(self.object)
        messages.success(self.request, 'Registrasi berhasil. Silakan masuk menggunakan email dan kata sandi Anda.')
        return redirect(self.get_success_url())


import logging

logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        logger.debug(
            f"LOGIN PAGE — user={request.user.id} "
            f"username={request.user.username} "
            f"superuser={request.user.is_superuser} "
            f"session_key={request.session.session_key}"
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        logger.debug(
            f"LOGIN SUCCESS — logging in as user={user.id} "
            f"username={user.username} superuser={user.is_superuser} "
            f"session_key={self.request.session.session_key}"
        )
        return super().form_valid(form)

    def get_success_url(self):
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
            return next_url
        return reverse_lazy('products:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Login'
        context['next'] = self.request.GET.get('next', '')
        return context


@require_POST
def logout_view(request):
    logger.debug(
        f"LOGOUT — user={request.user.id} "
        f"username={request.user.username} superuser={request.user.is_superuser} "
        f"session_key={request.session.session_key}"
    )
    logout(request)
    return redirect('products:list')


class ProfileUpdateView(CustomerRequiredMixin, LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Profile
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    success_message = 'Profil berhasil diperbarui.'

    def get_object(self, queryset=None):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Profil'
        return context


@login_required
@customer_required
def wishlist_list(request):
    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related('product__category').order_by('-created_at')

    try:
        profile = request.user.profile
    except AttributeError:
        profile = None

    context = {
        'wishlist_items': wishlist_items,
        'title': 'Wishlist Saya',
        'profile': profile,
    }
    return render(request, 'accounts/wishlist_list.html', context)


@login_required
@customer_required
@require_POST
def wishlist_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_available=True)

    _, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product,
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'saved': created, 'in_wishlist': True})

    if created:
        messages.success(request, f'{product.name} ditambahkan ke Wishlist.')
    else:
        messages.info(request, f'{product.name} sudah ada di Wishlist.')

    return redirect(request.META.get('HTTP_REFERER', 'products:list'))


@login_required
@customer_required
@require_POST
def wishlist_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    deleted, _ = Wishlist.objects.filter(
        user=request.user, product=product
    ).delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'removed': bool(deleted), 'in_wishlist': False})

    if deleted:
        messages.success(request, f'{product.name} dihapus dari Wishlist.')
    else:
        messages.info(request, f'{product.name} tidak ditemukan di Wishlist.')

    return redirect(request.META.get('HTTP_REFERER', 'accounts:wishlist_list'))


@login_required
@customer_required
def address_list(request):
    addresses = CustomerAddress.objects.filter(user=request.user)
    try:
        profile = request.user.profile
    except AttributeError:
        profile = None
    return render(request, 'accounts/address_list.html', {
        'addresses': addresses,
        'profile': profile,
        'title': 'Alamat Saya',
    })


@login_required
@customer_required
def address_create(request):
    try:
        profile = request.user.profile
    except AttributeError:
        profile = None

    if request.method == 'POST':
        form = CustomerAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, 'Alamat berhasil ditambahkan.')
            return redirect('accounts:address_list')
    else:
        form = CustomerAddressForm()

    return render(request, 'accounts/address_form.html', {
        'form': form,
        'profile': profile,
        'title': 'Tambah Alamat',
    })


@login_required
@customer_required
def address_edit(request, address_id):
    address = get_object_or_404(CustomerAddress, id=address_id, user=request.user)
    try:
        profile = request.user.profile
    except AttributeError:
        profile = None

    if request.method == 'POST':
        form = CustomerAddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Alamat berhasil diperbarui.')
            return redirect('accounts:address_list')
    else:
        form = CustomerAddressForm(instance=address)

    return render(request, 'accounts/address_form.html', {
        'form': form,
        'profile': profile,
        'title': 'Edit Alamat',
    })


@login_required
@customer_required
@require_POST
def address_delete(request, address_id):
    address = get_object_or_404(CustomerAddress, id=address_id, user=request.user)
    address.delete()
    messages.success(request, 'Alamat berhasil dihapus.')
    return redirect('accounts:address_list')


@login_required
@customer_required
@require_POST
def address_set_default(request, address_id):
    address = get_object_or_404(CustomerAddress, id=address_id, user=request.user)
    CustomerAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
    address.is_default = True
    address.save(update_fields=['is_default'])
    messages.success(request, f'"{address.label or "Alamat"}" sekarang menjadi alamat utama.')
    return redirect('accounts:address_list')
