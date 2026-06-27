from datetime import timedelta

from django.db.models import F, Q, Count, Sum
from django.utils.timezone import now

from apps.orders.models import Order
from .models import Voucher, UserVoucher


WELCOME_VOUCHER_CODE = 'WELCOME10'


def validate_voucher(code, user, subtotal):
    """Validate a voucher code against all rules.
    
    Returns:
        (valid: bool, voucher: Voucher|None, discount: int, error: str|None)
    """
    code = code.strip().upper()

    try:
        voucher = Voucher.objects.get(code=code)
    except Voucher.DoesNotExist:
        return False, None, 0, 'Kode voucher tidak ditemukan.'

    today = now().date()

    if not voucher.is_active:
        return False, voucher, 0, 'Voucher sudah tidak aktif.'

    if voucher.start_date and voucher.start_date > today:
        return False, voucher, 0, 'Voucher belum berlaku.'

    if voucher.expired_date and voucher.expired_date < today:
        return False, voucher, 0, 'Voucher sudah kedaluwarsa.'

    if subtotal < voucher.min_purchase:
        return (
            False, voucher, 0,
            f'Minimum pembelian Rp{voucher.min_purchase:,.0f} untuk menggunakan voucher ini.'
        )

    if voucher.quota > 0:
        total_uses = (
            voucher.used_count
            + UserVoucher.objects.filter(
                voucher=voucher, status=UserVoucher.Status.USED,
            ).count()
        )
        if total_uses >= voucher.quota:
            return False, voucher, 0, 'Kuota voucher sudah habis.'

    if voucher.voucher_type != Voucher.Type.PUBLIC:
        user_voucher = UserVoucher.objects.filter(
            user=user, voucher=voucher,
        ).first()
        if not user_voucher:
            return False, voucher, 0, 'Anda tidak memiliki voucher ini.'
        if user_voucher.status != UserVoucher.Status.AVAILABLE:
            return False, voucher, 0, 'Voucher sudah digunakan atau kedaluwarsa.'
        if user_voucher.expires_at <= now():
            return False, voucher, 0, 'Voucher sudah kedaluwarsa.'

    discount = voucher.calculate_discount(subtotal)
    return True, voucher, discount, None


def assign_welcome_voucher(user):
    voucher = Voucher.objects.filter(
        code=WELCOME_VOUCHER_CODE, is_active=True,
    ).first()

    if not voucher:
        voucher = Voucher.objects.filter(
            voucher_type=Voucher.Type.WELCOME, is_active=True,
        ).first()

    if not voucher:
        return None
    if UserVoucher.objects.filter(user=user, voucher=voucher).exists():
        return None

    expires_at = now() + timedelta(days=30)
    uv = UserVoucher.objects.create(
        user=user, voucher=voucher, expires_at=expires_at,
    )
    Voucher.objects.filter(pk=voucher.pk).update(
        claimed_count=F('claimed_count') + 1
    )
    return uv


def assign_birthday_vouchers():
    today = now().date()
    from apps.accounts.models import MemberProfile
    profiles = MemberProfile.objects.filter(
        birth_date__day=today.day, birth_date__month=today.month,
    ).select_related('user')

    vouchers = Voucher.objects.auto_assignable().filter(
        voucher_type=Voucher.Type.BIRTHDAY,
    )
    assigned = []
    for profile in profiles:
        for voucher in vouchers:
            if UserVoucher.objects.filter(user=profile.user, voucher=voucher).exists():
                continue
            expires_at = now() + timedelta(days=14)
            uv = UserVoucher.objects.create(
                user=profile.user, voucher=voucher, expires_at=expires_at,
            )
            Voucher.objects.filter(pk=voucher.pk).update(
                claimed_count=F('claimed_count') + 1
            )
            assigned.append(uv)
    return assigned


def assign_loyalty_vouchers(user):
    order_count = Order.objects.filter(user=user).exclude(
        status='cancelled',
    ).count()

    vouchers = Voucher.objects.auto_assignable().filter(
        voucher_type=Voucher.Type.LOYALTY,
        min_transactions__gte=1,
        min_transactions__lte=order_count,
    )
    assigned = []
    for voucher in vouchers:
        if UserVoucher.objects.filter(user=user, voucher=voucher).exists():
            continue
        expires_at = now() + timedelta(days=30)
        uv = UserVoucher.objects.create(
            user=user, voucher=voucher, expires_at=expires_at,
        )
        Voucher.objects.filter(pk=voucher.pk).update(
            claimed_count=F('claimed_count') + 1
        )
        assigned.append(uv)
    return assigned


def assign_min_purchase_vouchers(user, amount):
    total_spent = Order.objects.filter(
        user=user,
    ).exclude(status='cancelled').aggregate(
        total=Sum('total_price'),
    )['total'] or 0

    vouchers = Voucher.objects.auto_assignable().filter(
        voucher_type=Voucher.Type.MIN_PURCHASE,
        min_purchase__gte=1,
        min_purchase__lte=total_spent,
    )
    assigned = []
    for voucher in vouchers:
        if UserVoucher.objects.filter(user=user, voucher=voucher).exists():
            continue
        expires_at = now() + timedelta(days=30)
        uv = UserVoucher.objects.create(
            user=user, voucher=voucher, expires_at=expires_at,
        )
        Voucher.objects.filter(pk=voucher.pk).update(
            claimed_count=F('claimed_count') + 1
        )
        assigned.append(uv)
    return assigned


def auto_assign_vouchers(user, order_total=0):
    results = []
    wv = assign_welcome_voucher(user)
    if wv:
        results.append(wv)

    lv = assign_loyalty_vouchers(user)
    results.extend(lv)

    if order_total > 0:
        mv = assign_min_purchase_vouchers(user, order_total)
        results.extend(mv)

    return results


def get_available_vouchers(user, subtotal=0):
    qs = UserVoucher.objects.filter(
        user=user,
        status=UserVoucher.Status.AVAILABLE,
        expires_at__gt=now(),
    ).select_related('voucher')

    if subtotal > 0:
        qs = qs.filter(voucher__min_purchase__lte=subtotal)

    return qs


def claim_voucher(user, voucher):
    if not voucher.is_claimable():
        return None, 'Voucher tidak tersedia atau sudah kedaluwarsa.'

    if UserVoucher.objects.filter(user=user, voucher=voucher).exists():
        return None, 'Anda sudah memiliki voucher ini.'

    default_validity = timedelta(days=30)
    if voucher.expired_date:
        remaining = voucher.expired_date - now().date()
        if remaining.days > 0:
            default_validity = min(timedelta(days=remaining.days), default_validity)

    expires_at = now() + default_validity
    if voucher.expired_date:
        voucher_expiry = min(
            now() + default_validity,
            now() + timedelta(days=(voucher.expired_date - now().date()).days)
        )
        expires_at = voucher_expiry

    uv = UserVoucher.objects.create(
        user=user, voucher=voucher, expires_at=expires_at,
    )

    Voucher.objects.filter(pk=voucher.pk).update(
        claimed_count=F('claimed_count') + 1
    )

    return uv, None


def get_active_vouchers():
    return Voucher.objects.active().order_by('-claimed_count', '-created_at')


def get_claimable_vouchers(user):
    claimed_ids = UserVoucher.objects.filter(user=user).values_list('voucher_id', flat=True)
    return Voucher.objects.active().public().exclude(pk__in=claimed_ids)


def get_voucher_stats():
    from django.db.models import Count, Q as Q_

    total_claimed = UserVoucher.objects.count()
    total_used = UserVoucher.objects.filter(status=UserVoucher.Status.USED).count()
    total_expired = UserVoucher.objects.filter(status=UserVoucher.Status.EXPIRED).count()
    total_available = UserVoucher.objects.filter(
        status=UserVoucher.Status.AVAILABLE,
        expires_at__gt=now(),
    ).count()

    def _by_category(cat):
        base = UserVoucher.objects.filter(voucher__category=cat)
        return {
            'total': base.count(),
            'active': base.filter(
                status=UserVoucher.Status.AVAILABLE, expires_at__gt=now()
            ).count(),
            'used': base.filter(status=UserVoucher.Status.USED).count(),
        }

    voucher_usage = Voucher.objects.annotate(
        claim_count=Count('user_vouchers'),
        usage_count=Count('user_vouchers', filter=Q_(user_vouchers__status=UserVoucher.Status.USED)),
    ).order_by('-usage_count')

    most_popular = voucher_usage.first()
    conversion_rate = round(total_used / total_claimed * 100, 1) if total_claimed else 0

    return {
        'total_claimed': total_claimed,
        'total_used': total_used,
        'total_expired': total_expired,
        'total_available': total_available,
        'conversion_rate': conversion_rate,
        'most_popular': most_popular,
        'voucher_usage': voucher_usage[:10],
        'product': _by_category('product'),
        'shipping': _by_category('shipping'),
    }
