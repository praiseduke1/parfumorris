from datetime import timedelta, date

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Avg, Count, Sum, F, Q
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from apps.orders.models import Order, OrderItem
from apps.products.models import Product, Category, Review
from django.contrib.auth.models import User
from apps.accounts.models import MemberProfile
from apps.payments.models import Payment
from apps.promotions.models import Voucher as PromoVoucher
from apps.promotions.services import get_voucher_stats



@staff_member_required
def dashboard_view(request):
    now = timezone.now()
    today = now.date()
    yesterday = today - timedelta(days=1)

    days = int(request.GET.get('days', 30))
    days = max(7, min(365, days))
    since = now - timedelta(days=days)
    since_date = since.date()

    revenue_statuses = ['paid', 'processing', 'shipped', 'delivered', 'completed']

    # ──────────────────────────────────────────────────
    # 1. KPI metrics
    # ──────────────────────────────────────────────────
    revenue_total = Order.objects.filter(
        status__in=revenue_statuses
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0

    orders_total = Order.objects.count()

    paid_orders = Order.objects.exclude(status='cancelled').exclude(status='pending_payment')
    aov = (paid_orders.aggregate(avg=Avg('total_price'))['avg'] or 0) if paid_orders.exists() else 0

    active_customers = User.objects.filter(
        orders__isnull=False
    ).distinct().count()

    active_products = Product.objects.filter(is_available=True).count()

    completion_rate = round(
        orders_total and Order.objects.filter(
            status__in=['paid', 'processing', 'shipped', 'delivered', 'completed', 'cancelled']
        ).count() / orders_total * 100
    ) if orders_total else 0

    paid_rate = round(
        Order.objects.filter(status__in=revenue_statuses).count() / orders_total * 100
    ) if orders_total else 0

    # today vs yesterday delta
    revenue_today = Order.objects.filter(
        status__in=revenue_statuses, created_at__date=today
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0

    revenue_yesterday = Order.objects.filter(
        status__in=revenue_statuses, created_at__date=yesterday
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0

    if revenue_yesterday > 0:
        revenue_today_change = round((revenue_today - revenue_yesterday) / revenue_yesterday * 100, 1)
    else:
        revenue_today_change = 100 if revenue_today > 0 else 0

    orders_today = Order.objects.filter(created_at__date=today).count()
    orders_yesterday = Order.objects.filter(created_at__date=yesterday).count()
    if orders_yesterday > 0:
        orders_today_change = round((orders_today - orders_yesterday) / orders_yesterday * 100, 1)
    else:
        orders_today_change = 100 if orders_today > 0 else 0

    # ──────────────────────────────────────────────────
    # 2. Daily chart data (configurable days)
    # ──────────────────────────────────────────────────
    chart_dates = []
    revenue_chart = []
    orders_chart = []
    date_range_start = today - timedelta(days=days - 1)
    daily_data = Order.objects.filter(
        created_at__date__gte=date_range_start
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        revenue=Sum('total_price', filter=Q(status__in=revenue_statuses)),
        count=Count('id')
    ).order_by('date')
    date_map = {d['date']: d for d in daily_data}
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        label = day.strftime('%d %b')
        d = date_map.get(day, {})
        chart_dates.append(label)
        revenue_chart.append(d.get('revenue') or 0)
        orders_chart.append(d.get('count') or 0)

    # ──────────────────────────────────────────────────
    # 3. Monthly summary (last 12 months)
    # ──────────────────────────────────────────────────
    monthly_data = []
    for m in range(11, -1, -1):
        first = today.replace(day=1) - timedelta(days=30 * m)
        month_label = first.strftime('%b %Y')
        month_start = first
        if m == 0:
            month_end = today
        else:
            next_first = today.replace(day=1) - timedelta(days=30 * (m - 1))
            month_end = next_first - timedelta(days=1)
        m_orders = Order.objects.filter(
            created_at__date__gte=month_start, created_at__date__lte=month_end
        )
        m_rev = m_orders.filter(status__in=revenue_statuses).aggregate(
            Sum('total_price')
        )['total_price__sum'] or 0
        m_cnt = m_orders.count()
        m_new_customers = User.objects.filter(
            is_superuser=False, date_joined__date__gte=month_start, date_joined__date__lte=month_end
        ).count()
        monthly_data.append({
            'label': month_label,
            'revenue': int(m_rev),
            'orders': m_cnt,
            'new_customers': m_new_customers,
        })

    # ──────────────────────────────────────────────────
    # 4. Order status breakdown (for donut)
    # ──────────────────────────────────────────────────
    status_counts = {}
    for s, label in Order._meta.get_field('status').choices:
        cnt = Order.objects.filter(status=s).count()
        if cnt:
            status_counts[s] = {'label': label, 'count': cnt}

    # ──────────────────────────────────────────────────
    # 5. Top 10 products by revenue
    # ──────────────────────────────────────────────────
    top_agg = OrderItem.objects.filter(
        product__isnull=False
    ).values('product', 'product__name').annotate(
        total_sold=Sum('quantity'),
        revenue=Sum(F('price') * F('quantity'))
    ).order_by('-revenue')[:10]

    pid_list = [ta['product'] for ta in top_agg]
    product_map = {p.id: p for p in Product.objects.filter(id__in=pid_list)}

    total_product_revenue = top_agg.aggregate(s=Sum('revenue'))['s'] or 0

    top_products_with_pct = []
    for ta in top_agg:
        product = product_map.get(ta['product'])
        if not product:
            continue
        pct = round(ta['revenue'] / revenue_total * 100, 1) if revenue_total else 0
        top_products_with_pct.append({
            'name': product.name,
            'total_sold': ta['total_sold'],
            'revenue': ta['revenue'],
            'pct': pct,
            'image': product.image.url if product.image else None,
        })

    # ──────────────────────────────────────────────────
    # 6. Top 10 customers by spending
    # ──────────────────────────────────────────────────
    top_customers = User.objects.filter(
        orders__isnull=False,
        is_superuser=False,
    ).annotate(
        order_count=Count('orders'),
        total_spent=Sum('orders__total_price', filter=Q(orders__status__in=revenue_statuses)),
    ).order_by('-total_spent')[:10]

    resolved_top_customers = []
    for c in top_customers:
        last_order_date = Order.objects.filter(
            user=c, status__in=revenue_statuses
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        resolved_top_customers.append({
            'user': c,
            'order_count': c.order_count,
            'total_spent': c.total_spent or 0,
            'last_order': last_order_date,
        })

    # ──────────────────────────────────────────────────
    # 7. Category revenue
    # ──────────────────────────────────────────────────
    category_revenue = OrderItem.objects.filter(
        product__isnull=False,
        order__status__in=revenue_statuses,
    ).values('product__category__name').annotate(
        revenue=Sum(F('price') * F('quantity')),
        total_sold=Sum('quantity')
    ).order_by('-revenue')

    cat_total_revenue = sum(c['revenue'] or 0 for c in category_revenue)

    cat_data = []
    for cr in category_revenue:
        pct = round(cr['revenue'] / cat_total_revenue * 100, 1) if cat_total_revenue else 0
        cat_data.append({
            'name': cr['product__category__name'] or 'Uncategorized',
            'revenue': cr['revenue'] or 0,
            'total_sold': cr['total_sold'] or 0,
            'pct': pct,
        })

    # ──────────────────────────────────────────────────
    # 8. Aroma family analytics
    # ──────────────────────────────────────────────────
    family_data = Product.objects.values(
        'fragrance_families__name'
    ).annotate(
        product_count=Count('id', distinct=True),
        total_stock=Sum('stock')
    ).order_by('-product_count')

    # ──────────────────────────────────────────────────
    # 9. Payment method breakdown
    # ──────────────────────────────────────────────────
    payment_methods = Payment.objects.values('payment_method').annotate(
        total=Count('id'),
        total_amount=Sum('amount'),
    ).order_by('-total')

    # ──────────────────────────────────────────────────
    # 10. Customer growth (daily registrations, last 30 d)
    # ──────────────────────────────────────────────────
    thirty_days_ago = now - timedelta(days=30)
    reg_dates = []
    reg_counts = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        cnt = User.objects.filter(
            date_joined__date=d, is_superuser=False
        ).count()
        reg_dates.append(d.strftime('%d %b'))
        reg_counts.append(cnt)

    # ──────────────────────────────────────────────────
    # 11. Low stock products detail
    # ──────────────────────────────────────────────────
    low_stock_products = Product.objects.filter(
        Q(stock__gt=0, stock__lte=5)
    ).order_by('stock')[:15]

    out_of_stock_products = Product.objects.filter(
        Q(is_available=False) | Q(stock=0)
    ).order_by('name')[:10]

    # ──────────────────────────────────────────────────
    # 12. Recent activity timeline
    # ──────────────────────────────────────────────────
    recent_orders = Order.objects.select_related(
        'user'
    ).order_by('-created_at')[:5]

    recent_payments = Payment.objects.select_related(
        'order'
    ).order_by('-created_at')[:5]

    recent_reviews = Review.objects.select_related(
        'user', 'product'
    ).order_by('-created_at')[:5]

    activities = []
    for o in recent_orders:
        activities.append({
            'type': 'order',
            'icon': 'shopping-cart',
            'text': format_html(
                'Pesanan <strong>#{}</strong> oleh <strong>{}</strong>',
                o.order_number, o.user.get_full_name() or o.user.username
            ),
            'status': o.get_status_display(),
            'time': o.created_at,
            'url': reverse('admin:orders_order_change', args=[o.id]),
        })
    for p in recent_payments:
        activities.append({
            'type': 'payment',
            'icon': 'credit-card',
        'text': format_html(
            'Pembayaran <strong>{}</strong> ({}) — {}',
            p.transaction_id or '-', p.payment_method or '-',
            'Rp {:,.0f}'.format(p.amount or 0).replace(',', '.'),
        ),
            'status': p.get_status_display(),
            'time': p.created_at,
            'url': reverse('admin:payments_payment_change', args=[p.id]),
        })
    for r in recent_reviews:
        activities.append({
            'type': 'review',
            'icon': 'star',
            'text': format_html(
                'Ulasan <strong>{}</strong> oleh <strong>{}</strong>',
                r.product.name if r.product else '-',
                r.user.get_full_name() or r.user.username,
            ),
            'status': '{} / 5'.format(r.rating),
            'time': r.created_at,
            'url': reverse('admin:products_review_change', args=[r.id]),
        })

    activities.sort(key=lambda a: a['time'], reverse=True)
    activities = activities[:15]

    # ──────────────────────────────────────────────────
    # 13. Notifications
    # ──────────────────────────────────────────────────
    notifications = []
    low_stock_list = Product.objects.filter(stock__gt=0, stock__lte=5)[:5]
    if low_stock_list:
        names = ', '.join(p.name for p in low_stock_list)
        notifications.append({
            'type': 'warning',
            'text': format_html('<strong>Stok menipis:</strong> {}', names)
        })
    oos_count = Product.objects.filter(Q(is_available=False) | Q(stock=0)).count()
    if oos_count:
        notifications.append({
            'type': 'danger',
            'text': format_html('<strong>{} produk</strong> stok habis. Segera lakukan restock.', oos_count)
        })
    expiring_vouchers = PromoVoucher.objects.filter(
        is_active=True, expired_date__gte=today,
        expired_date__lte=today + timedelta(days=3)
    )
    for v in expiring_vouchers:
        expired_str = v.expired_date.strftime('%d %b')
        notifications.append({
            'type': 'info',
            'text': format_html('Voucher <strong>{}</strong> akan kedaluwarsa pada {}.', v.code, expired_str)
        })
    new_orders_today = Order.objects.filter(created_at__date=today).count()
    if new_orders_today:
        notifications.append({
            'type': 'success',
            'text': format_html('<strong>{} pesanan baru</strong> hari ini.', new_orders_today)
        })
    pending_orders = Order.objects.filter(status='pending_payment').count()
    if pending_orders:
        notifications.append({
            'type': 'warning',
            'text': format_html('<strong>{} pesanan</strong> menunggu konfirmasi pembayaran.', pending_orders)
        })

    # ──────────────────────────────────────────────────
    # 14. Aggregate counts
    # ──────────────────────────────────────────────────
    products_total = Product.objects.count()
    products_available = Product.objects.filter(is_available=True).count()
    products_low_stock = Product.objects.filter(
        Q(stock__gt=0, stock__lte=5) | Q(variants__stock__gt=0, variants__stock__lte=5)
    ).distinct().count()
    products_out_of_stock = Product.objects.filter(
        Q(is_available=False) | Q(stock=0)
    ).distinct().count()

    customers_total = User.objects.filter(is_superuser=False).count()
    customers_new_30d = User.objects.filter(
        is_superuser=False, date_joined__gte=thirty_days_ago
    ).count()

    reviews_total = Review.objects.count()
    avg_rating = Review.objects.aggregate(avg=Avg('rating'))['avg'] or 0

    payments_total = Payment.objects.count()
    payments_success = Payment.objects.filter(status='success').count()
    payments_pending = Payment.objects.filter(status='pending').count()
    payments_failed = Payment.objects.filter(status='failed').count()

    members = MemberProfile.objects.all()
    members_silver = members.filter(level='SILVER').count()
    members_gold = members.filter(level='GOLD').count()
    members_platinum = members.filter(level='PLATINUM').count()

    # ──────────────────────────────────────────────────
    # 15. Today / Week / Month summaries
    # ──────────────────────────────────────────────────
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    prev_week_start = week_start - timedelta(days=7)
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)

    customers_today = User.objects.filter(is_superuser=False, date_joined__date=today).count()
    customers_week = User.objects.filter(is_superuser=False, date_joined__date__gte=week_start).count()
    customers_month = User.objects.filter(is_superuser=False, date_joined__date__gte=month_start).count()

    revenue_week = Order.objects.filter(
        status__in=revenue_statuses, created_at__date__gte=week_start
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    orders_week = Order.objects.filter(created_at__date__gte=week_start).count()

    revenue_prev_week = Order.objects.filter(
        status__in=revenue_statuses,
        created_at__date__gte=prev_week_start, created_at__date__lt=week_start
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    rev_week_change = round(
        (revenue_week - revenue_prev_week) / revenue_prev_week * 100, 1
    ) if revenue_prev_week else (100 if revenue_week else 0)

    revenue_this_month = Order.objects.filter(
        status__in=revenue_statuses, created_at__date__gte=month_start
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    orders_this_month = Order.objects.filter(created_at__date__gte=month_start).count()

    revenue_prev_month = Order.objects.filter(
        status__in=revenue_statuses,
        created_at__date__gte=prev_month_start, created_at__date__lt=month_start
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    rev_month_change = round(
        (revenue_this_month - revenue_prev_month) / revenue_prev_month * 100, 1
    ) if revenue_prev_month else (100 if revenue_this_month else 0)

    # ──────────────────────────────────────────────────
    # 16. Period-specific KPI data (for tab switching)
    # ──────────────────────────────────────────────────

    # AOV per period
    today_paid_orders = Order.objects.filter(
        status__in=revenue_statuses, created_at__date=today
    )
    aov_today = today_paid_orders.aggregate(avg=Avg('total_price'))['avg'] or 0

    week_paid_orders = Order.objects.filter(
        status__in=revenue_statuses, created_at__date__gte=week_start
    )
    aov_week = week_paid_orders.aggregate(avg=Avg('total_price'))['avg'] or 0

    month_paid_orders = Order.objects.filter(
        status__in=revenue_statuses, created_at__date__gte=month_start
    )
    aov_month = month_paid_orders.aggregate(avg=Avg('total_price'))['avg'] or 0

    # AOV changes
    yesterday_paid_orders = Order.objects.filter(
        status__in=revenue_statuses, created_at__date=yesterday
    )
    aov_yesterday = yesterday_paid_orders.aggregate(avg=Avg('total_price'))['avg'] or 0
    aov_today_change = round((aov_today - aov_yesterday) / aov_yesterday * 100, 1) if aov_yesterday else (100 if aov_today else 0)

    prev_week_paid_orders = Order.objects.filter(
        status__in=revenue_statuses,
        created_at__date__gte=prev_week_start, created_at__date__lt=week_start
    )
    aov_prev_week = prev_week_paid_orders.aggregate(avg=Avg('total_price'))['avg'] or 0
    aov_week_change = round((aov_week - aov_prev_week) / aov_prev_week * 100, 1) if aov_prev_week else (100 if aov_week else 0)

    aov_prev_month = Order.objects.filter(
        status__in=revenue_statuses,
        created_at__date__gte=prev_month_start, created_at__date__lt=month_start
    ).aggregate(avg=Avg('total_price'))['avg'] or 0
    aov_month_change = round((aov_month - aov_prev_month) / aov_prev_month * 100, 1) if aov_prev_month else (100 if aov_month else 0)

    # Paid rate per period
    today_all = Order.objects.filter(created_at__date=today).count()
    paid_rate_today = round(today_paid_orders.count() / today_all * 100) if today_all else 0

    week_all = Order.objects.filter(created_at__date__gte=week_start).count()
    paid_rate_week = round(week_paid_orders.count() / week_all * 100) if week_all else 0

    month_all = Order.objects.filter(created_at__date__gte=month_start).count()
    paid_rate_month = round(month_paid_orders.count() / month_all * 100) if month_all else 0

    # Paid rate changes
    yesterday_all = Order.objects.filter(created_at__date=yesterday).count()
    paid_rate_yesterday = round(yesterday_paid_orders.count() / yesterday_all * 100) if yesterday_all else 0
    paid_rate_today_change = paid_rate_today - paid_rate_yesterday

    prev_week_all = Order.objects.filter(
        created_at__date__gte=prev_week_start, created_at__date__lt=week_start
    ).count()
    paid_rate_prev_week = round(prev_week_paid_orders.count() / prev_week_all * 100) if prev_week_all else 0
    paid_rate_week_change = paid_rate_week - paid_rate_prev_week

    prev_month_all = Order.objects.filter(
        created_at__date__gte=prev_month_start, created_at__date__lt=month_start
    ).count()
    paid_rate_prev_month = round(prev_month_paid_orders.count() / prev_month_all * 100) if prev_month_all else 0
    paid_rate_month_change = paid_rate_month - paid_rate_prev_month

    # Orders period changes
    prev_week_orders = Order.objects.filter(
        created_at__date__gte=prev_week_start, created_at__date__lt=week_start
    ).count()
    orders_week_change = round((orders_week - prev_week_orders) / prev_week_orders * 100, 1) if prev_week_orders else (100 if orders_week else 0)

    prev_month_orders = Order.objects.filter(
        created_at__date__gte=prev_month_start, created_at__date__lt=month_start
    ).count()
    orders_month_change = round((orders_this_month - prev_month_orders) / prev_month_orders * 100, 1) if prev_month_orders else (100 if orders_this_month else 0)

    # Active customers per period (distinct users with orders in period)
    customers_active_today = User.objects.filter(
        orders__created_at__date=today
    ).distinct().count()
    customers_active_week = User.objects.filter(
        orders__created_at__date__gte=week_start
    ).distinct().count()
    customers_active_month = User.objects.filter(
        orders__created_at__date__gte=month_start
    ).distinct().count()

    # Customer changes
    prev_week_customers = User.objects.filter(
        orders__created_at__date__gte=prev_week_start, orders__created_at__date__lt=week_start
    ).distinct().count()
    customers_week_change = round((customers_active_week - prev_week_customers) / prev_week_customers * 100, 1) if prev_week_customers else (100 if customers_active_week else 0)

    prev_month_customers = User.objects.filter(
        orders__created_at__date__gte=prev_month_start, orders__created_at__date__lt=month_start
    ).distinct().count()
    customers_month_change = round((customers_active_month - prev_month_customers) / prev_month_customers * 100, 1) if prev_month_customers else (100 if customers_active_month else 0)

    # ──────────────────────────────────────────────────
    # 17. Voucher stats by category
    # ──────────────────────────────────────────────────
    voucher_stats = get_voucher_stats()

    # ──────────────────────────────────────────────────
    # 18. Chart helper flags + monthly max
    # ──────────────────────────────────────────────────
    has_chart_data = sum(revenue_chart) > 0 and len(revenue_chart) > 2
    max_monthly_revenue = max((m['revenue'] for m in monthly_data), default=1)
    for m in monthly_data:
        m['revenue_pct'] = round(m['revenue'] / max_monthly_revenue * 100, 1) if max_monthly_revenue else 0

    # ──────────────────────────────────────────────────
    # 18. Sidebar quick insights
    # ──────────────────────────────────────────────────
    best_product = top_products_with_pct[0] if top_products_with_pct else None
    best_customer = resolved_top_customers[0] if resolved_top_customers else None
    sidebar_pending = Order.objects.filter(status='pending_payment').count()
    sidebar_low_stock_count = products_low_stock
    sidebar_oos_count = products_out_of_stock

    has_orders = orders_total > 0
    has_products = products_total > 0
    has_customers = customers_total > 0
    has_any_data = has_orders or has_products or has_customers

    context = {
        'title': 'Analytics Dashboard',
        'selected_days': days,

        # Today / Week / Month summary
        'revenue_today': revenue_today,
        'revenue_yesterday': revenue_yesterday,
        'revenue_today_change': revenue_today_change,
        'orders_today': orders_today,
        'orders_today_change': orders_today_change,
        'customers_active_today': customers_active_today,
        'customers_today': customers_today,
        'revenue_week': revenue_week,
        'revenue_week_change': rev_week_change,
        'orders_week': orders_week,
        'orders_week_change': orders_week_change,
        'customers_active_week': customers_active_week,
        'customers_week': customers_week,
        'customers_week_change': customers_week_change,
        'revenue_month': revenue_this_month,
        'revenue_month_change': rev_month_change,
        'orders_month': orders_this_month,
        'orders_month_change': orders_month_change,
        'customers_active_month': customers_active_month,
        'customers_month': customers_month,
        'customers_month_change': customers_month_change,

        # KPIs
        'revenue_total': revenue_total,
        'revenue_today': revenue_today,
        'revenue_today_change': revenue_today_change,
        'orders_total': orders_total,
        'orders_today': orders_today,
        'orders_today_change': orders_today_change,
        'aov': aov,
        'aov_today': aov_today,
        'aov_week': aov_week,
        'aov_month': aov_month,
        'aov_today_change': aov_today_change,
        'aov_week_change': aov_week_change,
        'aov_month_change': aov_month_change,
        'active_customers': active_customers,
        'active_products': active_products,
        'completion_rate': completion_rate,
        'paid_rate': paid_rate,
        'paid_rate_today': paid_rate_today,
        'paid_rate_week': paid_rate_week,
        'paid_rate_month': paid_rate_month,
        'paid_rate_today_change': paid_rate_today_change,
        'paid_rate_week_change': paid_rate_week_change,
        'paid_rate_month_change': paid_rate_month_change,

        # Chart data
        'chart_dates': chart_dates,
        'revenue_chart': revenue_chart,
        'orders_chart': orders_chart,
        'has_chart_data': has_chart_data,
        'has_orders': has_orders,
        'has_products': has_products,
        'has_customers': has_customers,
        'has_any_data': has_any_data,
        'monthly_data': monthly_data,
        'max_monthly_revenue': max_monthly_revenue,

        # Status breakdown
        'status_counts': status_counts,

        # Products
        'top_products': top_products_with_pct,
        'products_total': products_total,
        'products_available': products_available,
        'products_low_stock': products_low_stock,
        'products_out_of_stock': products_out_of_stock,

        # Categories
        'category_revenue': cat_data,
        'family_data': family_data,

        # Customers
        'top_customers': resolved_top_customers,
        'customers_total': customers_total,
        'customers_new_30d': customers_new_30d,

        # Members
        'members_silver': members_silver,
        'members_gold': members_gold,
        'members_platinum': members_platinum,

        # Reviews
        'reviews_total': reviews_total,
        'avg_rating': round(avg_rating, 1),

        # Payments
        'payments_total': payments_total,
        'payments_success': payments_success,
        'payments_pending': payments_pending,
        'payments_failed': payments_failed,
        'payment_methods': payment_methods,

        # Customer growth
        'reg_dates': reg_dates,
        'reg_counts': reg_counts,

        # Inventory
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,

        # Sidebar insights
        'best_product': best_product,
        'best_customer': best_customer,
        'sidebar_pending': sidebar_pending,
        'sidebar_low_stock_count': sidebar_low_stock_count,
        'sidebar_oos_count': sidebar_oos_count,

        # Activities & notifications
        'activities': activities,
        'notifications': notifications,

        'site_header': 'Morris Parfum',
        'site_title': 'Morris Parfum',

        # Voucher stats
        'voucher_stats': voucher_stats,
    }
    return render(request, 'admin/dashboard.html', context)
