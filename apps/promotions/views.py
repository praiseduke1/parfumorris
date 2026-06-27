import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q as Q_
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.timezone import now as tz_now
from django.views.decorators.http import require_POST

from apps.core.decorators import customer_required
from apps.carts.models import Cart
from .models import UserVoucher, Voucher
from .services import claim_voucher, get_active_vouchers


def voucher_list(request):
    vouchers = get_active_vouchers()

    if request.user.is_authenticated and not request.user.is_superuser:
        claimed_ids = set(
            UserVoucher.objects.filter(user=request.user)
            .values_list('voucher_id', flat=True)
        )
    elif request.user.is_superuser:
        claimed_ids = set()
    else:
        claimed_ids = None

    return render(request, 'promotions/voucher_list.html', {
        'vouchers': vouchers,
        'claimed_ids': claimed_ids,
    })


@login_required
@customer_required
def my_vouchers(request):
    filter_status = request.GET.get('status', 'available')
    now_val = tz_now()

    def _filtered_qs(category):
        qs = UserVoucher.objects.filter(
            user=request.user, voucher__category=category,
        ).select_related('voucher').order_by('-assigned_at')
        if filter_status == 'available':
            return qs.filter(status=UserVoucher.Status.AVAILABLE, expires_at__gt=now_val)
        elif filter_status == 'used':
            return qs.filter(status=UserVoucher.Status.USED)
        elif filter_status == 'expired':
            return qs.filter(
                Q_(status=UserVoucher.Status.EXPIRED) |
                Q_(status=UserVoucher.Status.AVAILABLE, expires_at__lte=now_val)
            )
        return qs

    product_vouchers = _filtered_qs('product')
    shipping_vouchers = _filtered_qs('shipping')

    def _count(category):
        base = UserVoucher.objects.filter(user=request.user, voucher__category=category)
        return {
            'available': base.filter(
                status=UserVoucher.Status.AVAILABLE, expires_at__gt=now_val
            ).count(),
            'used': base.filter(status=UserVoucher.Status.USED).count(),
            'expired': base.filter(
                Q_(status=UserVoucher.Status.EXPIRED) |
                Q_(status=UserVoucher.Status.AVAILABLE, expires_at__lte=now_val)
            ).count(),
        }

    return render(request, 'promotions/my_vouchers.html', {
        'product_vouchers': product_vouchers,
        'shipping_vouchers': shipping_vouchers,
        'filter_status': filter_status,
        'counts_product': _count('product'),
        'counts_shipping': _count('shipping'),
        'now': now_val,
    })


@login_required
@customer_required
@require_POST
def claim_voucher_view(request, voucher_id):
    voucher = get_object_or_404(Voucher, id=voucher_id)

    result, error = claim_voucher(request.user, voucher)
    if error:
        messages.error(request, error)
    else:
        if voucher.discount_type == 'percentage':
            msg = f'Voucher {voucher.code} berhasil diklaim! Selamat menikmati diskon {voucher.discount_amount}%'
        else:
            msg = f'Voucher {voucher.code} berhasil diklaim! Selamat menikmati diskon Rp {voucher.discount_amount:,.0f}'.replace(',', '.')
        messages.success(request, msg)

    return redirect(request.META.get('HTTP_REFERER', 'promotions:voucher_list'))


@login_required
@customer_required
def claim_voucher_ajax(request, voucher_id):
    voucher = get_object_or_404(Voucher, id=voucher_id)
    result, error = claim_voucher(request.user, voucher)

    if error:
        return JsonResponse({'success': False, 'error': error})

    return JsonResponse({
        'success': True,
        'message': f'Voucher {voucher.code} berhasil diklaim!',
        'voucher_code': voucher.code,
    })


def _get_session_voucher_ids(request):
    """Get product_voucher_id and shipping_voucher_id from session."""
    product_voucher_id = request.session.get('product_voucher_id')
    shipping_voucher_id = request.session.get('shipping_voucher_id')
    # Fallback: old combined dict
    if not product_voucher_id and not shipping_voucher_id:
        old = request.session.get('selected_vouchers', {})
        product_voucher_id = old.get('product')
        shipping_voucher_id = old.get('shipping')
    return product_voucher_id, shipping_voucher_id


def _set_session_voucher_ids(request, product_voucher_id=None, shipping_voucher_id=None):
    """Set product_voucher_id and shipping_voucher_id in session separately."""
    if product_voucher_id is not None:
        request.session['product_voucher_id'] = product_voucher_id
    elif 'product_voucher_id' in request.session:
        del request.session['product_voucher_id']
    if shipping_voucher_id is not None:
        request.session['shipping_voucher_id'] = shipping_voucher_id
    elif 'shipping_voucher_id' in request.session:
        del request.session['shipping_voucher_id']
    # Clean up old format
    if 'selected_vouchers' in request.session:
        del request.session['selected_vouchers']


def calculate_product_discount(subtotal, product_voucher_id, user):
    """Calculate discount from a product voucher."""
    if not product_voucher_id:
        return 0, None
    try:
        pv = Voucher.objects.get(id=product_voucher_id, category=Voucher.Category.PRODUCT, is_active=True)
        if subtotal >= pv.min_purchase:
            uv = UserVoucher.objects.filter(
                user=user, voucher=pv,
                status=UserVoucher.Status.AVAILABLE,
                expires_at__gt=tz_now(),
            ).first()
            if uv:
                return pv.calculate_discount(subtotal), pv
    except Voucher.DoesNotExist:
        pass
    return 0, None


def calculate_shipping_discount(shipping_cost, shipping_voucher_id, subtotal, user):
    """Calculate discount from a shipping voucher."""
    if not shipping_voucher_id or shipping_cost <= 0:
        return 0, None
    try:
        sv = Voucher.objects.get(id=shipping_voucher_id, category=Voucher.Category.SHIPPING, is_active=True)
        if subtotal >= sv.min_purchase:
            uv = UserVoucher.objects.filter(
                user=user, voucher=sv,
                status=UserVoucher.Status.AVAILABLE,
                expires_at__gt=tz_now(),
            ).first()
            if uv:
                return sv.calculate_discount(shipping_cost), sv
    except Voucher.DoesNotExist:
        pass
    return 0, None


def calculate_subtotal(cart):
    """Get subtotal from cart."""
    if not cart:
        return 0
    return cart.total_price()


def calculate_shipping_cost(shipping_info):
    """Extract shipping cost from session shipping info."""
    if not shipping_info:
        return 0
    return int(shipping_info.get('cost', 0))


def calculate_total(subtotal, shipping_cost, product_discount, shipping_discount):
    """Calculate final grand total."""
    return subtotal - product_discount + shipping_cost - shipping_discount


@login_required
@customer_required
def api_my_vouchers(request):
    category = request.GET.get('category', '')
    q = request.GET.get('q', '').strip().lower()

    now_val = tz_now()
    user_vouchers = UserVoucher.objects.filter(user=request.user).select_related('voucher')

    if category in ('product', 'shipping'):
        user_vouchers = user_vouchers.filter(voucher__category=category)
    if q:
        user_vouchers = user_vouchers.filter(
            Q_(voucher__code__icontains=q) | Q_(voucher__description__icontains=q)
        )

    subtotal = 0
    cart = Cart.objects.filter(user=request.user).first()
    if cart:
        subtotal = cart.total_price()

    shipping_cost = 0
    shipping_info = request.session.get('shipping', {})
    if shipping_info:
        shipping_cost = int(shipping_info.get('cost', 0))

    pv_id, sv_id = _get_session_voucher_ids(request)

    data = []
    for uv in user_vouchers:
        v = uv.voucher
        is_used = uv.status == UserVoucher.Status.USED
        is_expired = uv.status == UserVoucher.Status.EXPIRED or (
            uv.expires_at and uv.expires_at <= now_val
        )
        is_available = uv.status == UserVoucher.Status.AVAILABLE and (
            not uv.expires_at or uv.expires_at > now_val
        ) and v.is_active

        can_use = False
        reason = ''
        if is_used:
            reason = 'Sudah digunakan'
        elif is_expired:
            reason = 'Kedaluwarsa'
        elif not v.is_active:
            reason = 'Voucher tidak aktif'
        elif v.expired_date and v.expired_date < now_val.date():
            reason = 'Voucher sudah kedaluwarsa'
        else:
            needed = 0
            if v.category == Voucher.Category.PRODUCT:
                if subtotal < v.min_purchase:
                    needed = int(v.min_purchase - subtotal)
                    reason = f'Butuh belanja Rp {needed:,} lagi'.replace(',', '.')
                else:
                    can_use = True
            elif v.category == Voucher.Category.SHIPPING:
                if subtotal < v.min_purchase:
                    needed = int(v.min_purchase - subtotal)
                    reason = f'Butuh belanja Rp {needed:,} lagi'.replace(',', '.')
                elif shipping_cost <= 0:
                    reason = 'Pilih layanan pengiriman terlebih dahulu'
                else:
                    can_use = True

        is_selected = False
        if v.category == Voucher.Category.PRODUCT:
            is_selected = pv_id is not None and str(v.id) == str(pv_id)
        elif v.category == Voucher.Category.SHIPPING:
            is_selected = sv_id is not None and str(v.id) == str(sv_id)

        discount_text = ''
        if v.discount_type == 'percentage':
            discount_text = f'{v.discount_amount}%'
            if v.max_discount:
                discount_text += f' (maks. Rp {int(v.max_discount):,})'.replace(',', '.')
        else:
            discount_text = f'Rp {int(v.discount_amount):,}'.replace(',', '.')

        remaining_days = ''
        if uv.expires_at and uv.expires_at > now_val:
            days = (uv.expires_at - now_val).days
            if days <= 1:
                remaining_days = 'Hari ini'
            elif days <= 7:
                remaining_days = f'Sisa {days} hari'
            else:
                remaining_days = f'{days} hari'

        min_purchase_text = ''
        if v.min_purchase > 0:
            min_purchase_text = f'Min. Belanja Rp {int(v.min_purchase):,}'.replace(',', '.')

        data.append({
            'id': v.id,
            'code': v.code,
            'category': v.category,
            'category_label': v.get_category_display(),
            'discount_type': v.discount_type,
            'discount_amount': int(v.discount_amount),
            'discount_text': discount_text,
            'description': v.description or '',
            'min_purchase': int(v.min_purchase),
            'min_purchase_text': min_purchase_text,
            'max_discount': int(v.max_discount) if v.max_discount else None,
            'status': {
                'label': 'Tersedia' if is_available else ('Terpakai' if is_used else 'Kedaluwarsa'),
                'key': 'available' if is_available else ('used' if is_used else 'expired'),
            },
            'can_use': can_use,
            'reason': reason,
            'is_selected': is_selected,
            'remaining_days': remaining_days,
            'expires_at': uv.expires_at.isoformat() if uv.expires_at else None,
            'icon': 'ticket' if v.category == Voucher.Category.PRODUCT else 'truck',
        })

    return JsonResponse({'vouchers': data})


@login_required
@customer_required
@require_POST
def api_select_voucher(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    voucher_id = body.get('voucher_id')
    category = body.get('category')
    subtotal_from_cart = 0
    cart = Cart.objects.filter(user=request.user).first()
    if cart:
        subtotal_from_cart = cart.total_price()

    shipping_cost = 0
    shipping_info = request.session.get('shipping', {})
    if shipping_info:
        shipping_cost = int(shipping_info.get('cost', 0))

    if not voucher_id or category not in ('product', 'shipping'):
        return JsonResponse({'error': 'Parameter tidak valid'}, status=400)

    voucher = get_object_or_404(Voucher, id=voucher_id)

    now_val = tz_now()
    uv = UserVoucher.objects.filter(
        user=request.user, voucher=voucher,
        status=UserVoucher.Status.AVAILABLE,
        expires_at__gt=now_val,
        voucher__is_active=True,
    ).first()

    if not uv:
        return JsonResponse({'error': 'Voucher tidak tersedia atau sudah kedaluwarsa'}, status=400)

    if category == 'product' and voucher.category != Voucher.Category.PRODUCT:
        return JsonResponse({'error': 'Voucher ini bukan voucher produk'}, status=400)
    if category == 'shipping' and voucher.category != Voucher.Category.SHIPPING:
        return JsonResponse({'error': 'Voucher ini bukan voucher ongkir'}, status=400)

    if subtotal_from_cart < voucher.min_purchase:
        needed = int(voucher.min_purchase - subtotal_from_cart)
        return JsonResponse({
            'error': f'Minimal belanja Rp {needed:,} lagi untuk menggunakan voucher ini'
        }, status=400)

    if category == 'shipping' and shipping_cost <= 0:
        return JsonResponse({'error': 'Pilih layanan pengiriman terlebih dahulu'}, status=400)

    if category == 'product':
        _set_session_voucher_ids(request, product_voucher_id=voucher.id)
    else:
        _set_session_voucher_ids(request, shipping_voucher_id=voucher.id)

    pv_id, sv_id = _get_session_voucher_ids(request)
    product_discount, pv = calculate_product_discount(subtotal_from_cart, pv_id, request.user)
    shipping_discount, sv = calculate_shipping_discount(shipping_cost, sv_id, subtotal_from_cart, request.user)
    grand_total = calculate_total(subtotal_from_cart, shipping_cost, product_discount, shipping_discount)

    return JsonResponse({
        'success': True,
        'voucher_id': voucher.id,
        'voucher_code': voucher.code,
        'category': category,
        'product_discount': product_discount,
        'shipping_discount': shipping_discount,
        'grand_total': grand_total,
        'subtotal': subtotal_from_cart,
        'shipping_cost': shipping_cost,
    })


@login_required
@customer_required
@require_POST
def api_remove_voucher(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    category = body.get('category')
    if category not in ('product', 'shipping'):
        return JsonResponse({'error': 'Parameter tidak valid'}, status=400)

    if category == 'product':
        _set_session_voucher_ids(request, product_voucher_id=None)
    else:
        _set_session_voucher_ids(request, shipping_voucher_id=None)

    cart = Cart.objects.filter(user=request.user).first()
    subtotal_from_cart = cart.total_price() if cart else 0
    shipping_info = request.session.get('shipping', {})
    shipping_cost = int(shipping_info.get('cost', 0)) if shipping_info else 0

    pv_id, sv_id = _get_session_voucher_ids(request)
    product_discount, pv = calculate_product_discount(subtotal_from_cart, pv_id, request.user)
    shipping_discount, sv = calculate_shipping_discount(shipping_cost, sv_id, subtotal_from_cart, request.user)
    grand_total = calculate_total(subtotal_from_cart, shipping_cost, product_discount, shipping_discount)

    return JsonResponse({
        'success': True,
        'category': category,
        'product_discount': product_discount,
        'shipping_discount': shipping_discount,
        'grand_total': grand_total,
        'subtotal': subtotal_from_cart,
        'shipping_cost': shipping_cost,
    })


@login_required
@customer_required
@require_POST
def api_calculate_totals(request):
    cart = Cart.objects.filter(user=request.user).first()
    subtotal_from_cart = cart.total_price() if cart else 0

    shipping_info = request.session.get('shipping', {})
    shipping_cost = int(shipping_info.get('cost', 0)) if shipping_info else 0

    pv_id, sv_id = _get_session_voucher_ids(request)
    product_discount, pv = calculate_product_discount(subtotal_from_cart, pv_id, request.user)
    shipping_discount, sv = calculate_shipping_discount(shipping_cost, sv_id, subtotal_from_cart, request.user)
    grand_total = calculate_total(subtotal_from_cart, shipping_cost, product_discount, shipping_discount)

    return JsonResponse({
        'subtotal': subtotal_from_cart,
        'product_discount': product_discount,
        'shipping_cost': shipping_cost,
        'shipping_discount': shipping_discount,
        'grand_total': grand_total,
    })
