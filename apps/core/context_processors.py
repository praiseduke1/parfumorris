from django.utils.timezone import now

from apps.accounts.models import Wishlist
from apps.carts.models import Cart
from apps.promotions.models import UserVoucher


def cart_count(request):
    if request.user.is_authenticated and not request.user.is_superuser:
        try:
            cart = Cart.objects.get(user=request.user)
            count = cart.total_items()
        except Cart.DoesNotExist:
            count = 0
    else:
        count = 0
    return {'cart_count': count}


def wishlist_ids(request):
    if request.user.is_authenticated and not request.user.is_superuser:
        ids = set(
            Wishlist.objects.filter(user=request.user)
            .values_list('product_id', flat=True)
        )
    else:
        ids = set()
    return {'wishlist_product_ids': ids}


def voucher_notification(request):
    count = 0
    if request.user.is_authenticated and not request.user.is_superuser:
        count = UserVoucher.objects.filter(
            user=request.user,
            status=UserVoucher.Status.AVAILABLE,
            expires_at__gt=now(),
        ).count()
    return {'unclaimed_vouchers_count': count}


def voucher_floating_panel(request):
    from datetime import timedelta

    from apps.promotions.models import Voucher

    today = now().date()
    vouchers = Voucher.objects.active().order_by('-claimed_count')

    is_customer = request.user.is_authenticated and not request.user.is_superuser
    claimed_ids = set()
    if is_customer:
        claimed_ids = set(
            UserVoucher.objects.filter(user=request.user)
            .values_list('voucher_id', flat=True)
        )

    items = []
    best_id = vouchers[0].id if vouchers else None

    for v in vouchers:
        remaining = v.remaining_quota()
        diff_days = (v.expired_date - today).days if v.expired_date else 999

        items.append({
            'id': v.id,
            'code': v.code,
            'description': v.description,
            'discount_type': v.discount_type,
            'discount_amount': v.discount_amount,
            'min_purchase': v.min_purchase,
            'is_expiring_today': diff_days == 0,
            'is_expiring_soon': 0 < diff_days <= 3,
            'remaining': remaining,
            'remaining_limited': 0 < remaining <= 5,
            'is_claimed': v.id in claimed_ids,
            'is_best': v.id == best_id,
        })

    return {'floating_vouchers': items}
