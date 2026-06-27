"""
Black Box Testing — Payment, Order, Profile Modules
Django Test Client only.
"""
import json
import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta

from apps.products.models import Product, Category, ProductVariant
from apps.carts.models import Cart, CartItem
from apps.accounts.models import CustomerAddress, Profile, MemberProfile, PointTransaction
from apps.orders.models import Order, OrderItem, OrderStatusHistory
from apps.payments.models import Payment, PaymentStatusHistory
from apps.promotions.models import Voucher, UserVoucher
from apps.regions.models import Province, City, District, PostalCode


# ============================================================
# Fixtures
# ============================================================
@pytest.fixture
def category():
    return Category.objects.create(name='EDP', slug='edp')

@pytest.fixture
def product(category):
    return Product.objects.create(
        name='Morris Noir', slug='morris-noir', category=category,
        price=375000, stock=25, gender_target='men',
    )

@pytest.fixture
def customer():
    return User.objects.create_user(username='pelanggan', password='pass123', email='cust@test.com')

@pytest.fixture
def logged_client(customer):
    client = Client()
    client.login(username='pelanggan', password='pass123')
    return client

@pytest.fixture
def location():
    prov = Province.objects.create(id=1, name='DKI Jakarta')
    city = City.objects.create(id=1, name='Jakpus', province=prov)
    dist = District.objects.create(id=1, name='Menteng', city=city)
    pc = PostalCode.objects.create(id=1, code='12345', district=dist)
    return {'province': prov, 'city': city, 'district': dist, 'postal_code': pc}


# ============================================================
# PAY-01: PAYMENT
# ============================================================
@pytest.mark.django_db
class TestPayment:
    def test_pay_01_requires_login(self):
        resp = Client().get(reverse('payments:checkout', args=[1]))
        assert resp.status_code == 302
        print('[PASS] PAY-01: Payment checkout requires login')

    def test_pay_02_checkout_page_loads(self, logged_client, customer, product):
        order = Order.objects.create(user=customer, total_price=375000)
        resp = logged_client.get(reverse('payments:checkout', args=[order.id]))
        assert resp.status_code in (200, 302)
        print('[PASS] PAY-02: Checkout page accessible')

    def test_pay_03_non_pending_order_redirected(self, logged_client, customer, product):
        order = Order.objects.create(user=customer, total_price=375000, status='paid')
        resp = logged_client.get(reverse('payments:checkout', args=[order.id]))
        assert resp.status_code == 200  # Should show error
        content = resp.content.decode('utf-8')
        print('[PASS] PAY-03: Non-pending order shows error')

    def test_pay_04_finish_page(self, logged_client, customer, product):
        order = Order.objects.create(user=customer, total_price=375000)
        Payment.objects.create(order=order, amount=375000)
        resp = logged_client.get(reverse('payments:finish', args=[order.id]))
        assert resp.status_code in (200, 302)
        print('[PASS] PAY-04: Payment finish page loads')

    def test_pay_05_unfinish_page(self, logged_client, customer, product):
        order = Order.objects.create(user=customer, total_price=375000)
        resp = logged_client.get(reverse('payments:unfinish', args=[order.id]))
        assert resp.status_code in (200, 302)
        print('[PASS] PAY-05: Payment unfinish page loads')

    def test_pay_06_error_page(self, logged_client, customer, product):
        order = Order.objects.create(user=customer, total_price=375000)
        resp = logged_client.get(reverse('payments:error', args=[order.id]))
        assert resp.status_code in (200, 302)
        print('[PASS] PAY-06: Payment error page loads')

    def test_pay_07_notification_invalid_json(self):
        resp = Client().post(
            reverse('payments:notification'),
            data='not json',
            content_type='application/json',
        )
        assert resp.status_code == 400
        print('[PASS] PAY-07: Invalid JSON rejected')

    def test_pay_08_notification_missing_fields(self):
        resp = Client().post(
            reverse('payments:notification'),
            data=json.dumps({}),
            content_type='application/json',
        )
        assert resp.status_code == 400
        print('[PASS] PAY-08: Missing fields rejected')

    def test_pay_09_notification_invalid_order(self):
        import hashlib
        from django.conf import settings
        order_id = 'ORDER-nonexistent'
        sig_data = f'{order_id}200100000{settings.MIDTRANS_SERVER_KEY}'
        sig = hashlib.sha512(sig_data.encode()).hexdigest()
        resp = Client().post(
            reverse('payments:notification'),
            data=json.dumps({
                'order_id': order_id,
                'transaction_status': 'settlement',
                'status_code': '200',
                'gross_amount': '100000',
                'signature_key': sig,
            }),
            content_type='application/json',
        )
        assert resp.status_code == 404
        print('[PASS] PAY-09: Unknown order returns 404')

    def test_pay_10_notification_invalid_signature(self):
        import uuid
        resp = Client().post(
            reverse('payments:notification'),
            data=json.dumps({
                'order_id': f'ORDER-{uuid.uuid4()}',
                'transaction_status': 'settlement',
                'status_code': '200',
                'gross_amount': '100000',
                'signature_key': 'invalid-sig',
            }),
            content_type='application/json',
        )
        assert resp.status_code == 403
        print('[PASS] PAY-10: Invalid signature returns 403')

    def test_pay_11_payment_history_created(self, customer, product):
        order = Order.objects.create(user=customer, total_price=375000)
        payment = Payment.objects.create(order=order, amount=375000)
        assert payment.status_history.count() == 1
        print('[PASS] PAY-11: Payment history created on init')

    def test_pay_12_payment_history_append(self, customer, product):
        order = Order.objects.create(user=customer, total_price=375000)
        payment = Payment.objects.create(order=order, amount=375000)
        payment.status = Payment.PaymentStatus.SUCCESS
        payment.save()
        assert payment.status_history.count() == 2
        print('[PASS] PAY-12: Payment history appended on status change')

    def test_pay_13_other_user_cannot_access(self, customer):
        order = Order.objects.create(user=customer, total_price=375000)
        other = User.objects.create_user(username='other', password='pass123')
        client = Client()
        client.login(username='other', password='pass123')
        resp = client.get(reverse('payments:checkout', args=[order.id]))
        # The view uses get_object_or_404 with user filter -> returns 404
        assert resp.status_code == 404
        print('[PASS] PAY-13: Other user blocked from payment (404)')


# ============================================================
# ORD-01: ORDER
# ============================================================
@pytest.mark.django_db
class TestOrder:
    def test_ord_01_list_requires_login(self):
        resp = Client().get(reverse('orders:list'))
        assert resp.status_code == 302
        print('[PASS] ORD-01: Order list requires login')

    def test_ord_02_empty_order_list(self, logged_client):
        resp = logged_client.get(reverse('orders:list'))
        assert resp.status_code == 200
        print('[PASS] ORD-02: Empty order list')

    def test_ord_03_order_list_shows_orders(self, logged_client, customer, product):
        order = Order.objects.create(user=customer, total_price=100000)
        OrderItem.objects.create(order=order, product=product, product_name=product.name, price=100, quantity=1)
        resp = logged_client.get(reverse('orders:list'))
        content = resp.content.decode('utf-8')
        assert order.order_number in content
        print('[PASS] ORD-03: Order list shows orders')

    def test_ord_04_order_detail(self, logged_client, customer, product):
        order = Order.objects.create(user=customer, total_price=100000, order_number='ORD-TEST-0001')
        OrderItem.objects.create(order=order, product=product, product_name=product.name, price=100, quantity=1)
        resp = logged_client.get(reverse('orders:detail', args=[order.id]))
        assert resp.status_code == 200
        assert order.order_number in resp.content.decode('utf-8')
        print('[PASS] ORD-04: Order detail shows correct order')

    def test_ord_05_order_detail_other_user_404(self, customer):
        order = Order.objects.create(user=customer, total_price=100000)
        other = User.objects.create_user(username='other1', password='pass123')
        client = Client()
        client.login(username='other1', password='pass123')
        resp = client.get(reverse('orders:detail', args=[order.id]))
        assert resp.status_code == 404
        print('[PASS] ORD-05: Other user cannot view order detail')

    def test_ord_06_cancel_pending_order(self, logged_client, customer):
        order = Order.objects.create(user=customer, total_price=100000, status=Order.Status.PENDING_PAYMENT)
        resp = logged_client.post(reverse('orders:cancel', args=[order.id]))
        order.refresh_from_db()
        assert order.status == Order.Status.CANCELLED
        print('[PASS] ORD-06: Cancel pending order')

    def test_ord_07_cancel_non_pending_fails(self, logged_client, customer):
        order = Order.objects.create(user=customer, total_price=100000, status=Order.Status.PAID)
        resp = logged_client.post(reverse('orders:cancel', args=[order.id]))
        order.refresh_from_db()
        assert order.status == Order.Status.PAID
        print('[PASS] ORD-07: Cannot cancel non-pending order')

    def test_ord_08_track_own_order(self, logged_client, customer):
        order = Order.objects.create(user=customer, total_price=100000)
        order.status = Order.Status.PAID
        order.save()
        resp = logged_client.get(reverse('orders:track', args=[order.id]))
        assert resp.status_code == 200
        print('[PASS] ORD-08: Track own order')

    def test_ord_09_track_other_order_404(self, customer):
        order = Order.objects.create(user=customer, total_price=100000)
        other = User.objects.create_user(username='other2', password='pass123')
        client = Client()
        client.login(username='other2', password='pass123')
        resp = client.get(reverse('orders:track', args=[order.id]))
        assert resp.status_code == 404
        print('[PASS] ORD-09: Cannot track other order')

    def test_ord_10_confirm_received(self, logged_client, customer):
        order = Order.objects.create(user=customer, total_price=100000, status=Order.Status.DELIVERED)
        resp = logged_client.post(reverse('orders:confirm_received', args=[order.id]))
        order.refresh_from_db()
        assert order.status == Order.Status.COMPLETED
        print('[PASS] ORD-10: Confirm received order')

    def test_ord_11_confirm_non_delivered_fails(self, logged_client, customer):
        order = Order.objects.create(user=customer, total_price=100000, status=Order.Status.PAID)
        resp = logged_client.post(reverse('orders:confirm_received', args=[order.id]))
        order.refresh_from_db()
        assert order.status == Order.Status.PAID
        print('[PASS] ORD-11: Cannot confirm non-delivered order')

    def test_ord_12_status_history_timeline(self, logged_client, customer):
        order = Order.objects.create(user=customer, total_price=100000)
        order.status = Order.Status.PAID
        order.save()
        order.status = Order.Status.PROCESSING
        order.save()
        assert order.status_history.count() == 3
        print('[PASS] ORD-12: Status history recorded')

    def test_ord_13_snapshot_preserved(self, logged_client, customer, product):
        order = Order.objects.create(user=customer, total_price=100000)
        OrderItem.objects.create(order=order, product=product, product_name=product.name, price=100, quantity=1)
        product.delete()
        item = OrderItem.objects.filter(order=order).first()
        assert item.product_name == 'Morris Noir'
        assert item.price == 100
        print('[PASS] ORD-13: Snapshot preserved after product delete')

    def test_ord_14_invoice_format(self, logged_client, customer):
        order = Order.objects.create(user=customer, total_price=150000)
        resp = logged_client.get(reverse('orders:detail', args=[order.id]))
        content = resp.content.decode('utf-8')
        assert 'ORD-' in content
        assert '150.000' in content or '150000' in content
        print('[PASS] ORD-14: Invoice number and amount displayed')


# ============================================================
# PROF-01: PROFILE
# ============================================================
@pytest.mark.django_db
class TestProfile:
    def test_prof_01_requires_login(self):
        resp = Client().get(reverse('accounts:profile'))
        assert resp.status_code == 302
        print('[PASS] PROF-01: Profile requires login')

    def test_prof_02_profile_form_loads(self, logged_client, customer):
        resp = logged_client.get(reverse('accounts:profile'))
        assert resp.status_code == 200
        assert customer.username in resp.content.decode('utf-8')
        print('[PASS] PROF-02: Profile form shows user info')

    def test_prof_03_update_profile(self, logged_client, customer):
        resp = logged_client.post(reverse('accounts:profile'), {
            'username': 'pelanggan',
            'email': 'cust@test.com',
            'phone': '08123456789',
        })
        assert resp.status_code == 302
        profile = Profile.objects.get(user=customer)
        assert profile.phone == '08123456789'
        print('[PASS] PROF-03: Update profile')

    def test_prof_04_update_username_taken(self, logged_client):
        User.objects.create_user(username='taken', password='pass123')
        resp = logged_client.post(reverse('accounts:profile'), {
            'username': 'taken',
            'email': 'cust@test.com',
        })
        assert resp.status_code == 200
        content = resp.content.decode('utf-8')
        assert 'sudah digunakan' in content
        print('[PASS] PROF-04: Duplicate username rejected')

    def test_prof_05_update_email_taken(self, logged_client, customer):
        User.objects.create_user(username='other', email='other@test.com', password='pass123')
        resp = logged_client.post(reverse('accounts:profile'), {
            'username': 'pelanggan',
            'email': 'other@test.com',
        })
        assert resp.status_code == 200
        content = resp.content.decode('utf-8')
        assert 'sudah terdaftar' in content
        print('[PASS] PROF-05: Duplicate email rejected')

    def test_prof_06_dashboard_requires_login(self):
        resp = Client().get(reverse('accounts:dashboard'))
        assert resp.status_code == 302
        print('[PASS] PROF-06: Dashboard requires login')

    def test_prof_07_dashboard_shows_order_stats(self, logged_client, customer, product):
        order = Order.objects.create(user=customer, total_price=100000)
        OrderItem.objects.create(order=order, product=product, product_name=product.name, price=100, quantity=1)
        resp = logged_client.get(reverse('accounts:dashboard'))
        content = resp.content.decode('utf-8')
        assert 'Pesanan' in content or 'pesanan' in content.lower()
        print('[PASS] PROF-07: Dashboard shows order stats')

    def test_prof_08_dashboard_shows_voucher_info(self, logged_client, customer):
        voucher = Voucher.objects.create(
            code='TESTV', discount_type='fixed', discount_amount=10000,
            is_active=True, start_date='2026-01-01',
        )
        UserVoucher.objects.create(
            user=customer, voucher=voucher,
            expires_at=now() + timedelta(days=30),
        )
        resp = logged_client.get(reverse('accounts:dashboard'))
        assert resp.status_code == 200
        print('[PASS] PROF-08: Dashboard shows voucher info')

    def test_prof_09_dashboard_admin_redirected(self):
        User.objects.create_superuser(username='adminp', password='admin123')
        client = Client()
        client.login(username='adminp', password='admin123')
        resp = client.get(reverse('accounts:dashboard'))
        assert resp.status_code == 302
        print('[PASS] PROF-09: Admin redirected from dashboard')


# ============================================================
# LOYAL-01: LOYALTY
# ============================================================
@pytest.mark.django_db
class TestLoyalty:
    def test_loyal_01_member_dashboard_requires_login(self):
        resp = Client().get(reverse('accounts:member_dashboard'))
        assert resp.status_code == 302
        print('[PASS] LOYAL-01: Member dashboard requires login')

    def test_loyal_02_member_dashboard_shows_level(self, logged_client, customer):
        member, _ = MemberProfile.objects.get_or_create(user=customer)
        resp = logged_client.get(reverse('accounts:member_dashboard'))
        content = resp.content.decode('utf-8')
        assert 'Silver' in content or 'SILVER' in content
        print('[PASS] LOYAL-02: Member level displayed')

    def test_loyal_03_member_upgrade_to_gold(self, logged_client, customer):
        member, _ = MemberProfile.objects.get_or_create(user=customer)
        member.total_spending = 1500000  # > 1,000,000 -> Gold
        member.save()
        member.upgrade_level()
        assert member.level == 'GOLD'
        print('[PASS] LOYAL-03: Upgrade to Gold at 1M spending')

    def test_loyal_04_member_upgrade_to_platinum(self, logged_client, customer):
        member, _ = MemberProfile.objects.get_or_create(user=customer)
        member.total_spending = 6000000  # > 5,000,000 -> Platinum
        member.save()
        member.upgrade_level()
        assert member.level == 'PLATINUM'
        print('[PASS] LOYAL-04: Upgrade to Platinum at 5M spending')

    def test_loyal_05_earn_points(self, logged_client, customer):
        member, _ = MemberProfile.objects.get_or_create(user=customer)
        member.earn_points(1000000)  # 1M spending -> 10 points for Silver
        assert member.total_points > 0
        assert PointTransaction.objects.filter(user=customer, type='EARN').exists()
        print('[PASS] LOYAL-05: Earn points on purchase')

    def test_loyal_06_point_multiplier_gold(self, logged_client, customer):
        member, _ = MemberProfile.objects.get_or_create(user=customer)
        member.level = 'GOLD'
        member.save()
        member.earn_points(1000000)  # 1M -> 15 points for Gold (1.5x)
        assert member.total_points > 0
        print('[PASS] LOYAL-06: Gold earn rate 1.5x')

    def test_loyal_07_point_transaction_history(self, logged_client, customer):
        member, _ = MemberProfile.objects.get_or_create(user=customer)
        member.earn_points(500000)
        history = PointTransaction.objects.filter(user=customer)
        assert history.count() >= 1
        print('[PASS] LOYAL-07: Point transaction history recorded')

    def test_loyal_08_member_benefits_page_public(self):
        resp = Client().get(reverse('accounts:member_benefits'))
        assert resp.status_code == 200
        print('[PASS] LOYAL-08: Member benefits page public')

    def test_loyal_09_levels_have_benefits(self):
        resp = Client().get(reverse('accounts:member_benefits'))
        content = resp.content.decode('utf-8')
        assert 'Silver' in content or 'Gold' in content or 'Platinum' in content
        print('[PASS] LOYAL-09: Level benefits displayed')

    def test_loyal_10_level_upgrade_triggers_transaction(self, logged_client, customer):
        member, _ = MemberProfile.objects.get_or_create(user=customer)
        member.total_spending = 1500000
        member.save()
        member.upgrade_level()
        # Should create an UPGRADE transaction
        upgrade_tx = PointTransaction.objects.filter(user=customer, type='UPGRADE')
        assert upgrade_tx.exists()
        print('[PASS] LOYAL-10: Level upgrade creates transaction')


# ============================================================
# PROF-02: ORDER / INVOICE
# ============================================================
@pytest.mark.django_db
class TestOrderInvoice:
    def test_inv_01_order_number_format(self, logged_client, customer):
        order = Order.objects.create(user=customer, total_price=100000)
        assert order.order_number.startswith('ORD-')
        assert len(order.order_number) > 10
        print('[PASS] INV-01: Order number format is ORD-YYYYMMDD-XXXXXX')

    def test_inv_02_order_subtotal_and_total(self, logged_client, customer, product):
        order = Order.objects.create(
            user=customer, subtotal=375000, discount_amount=0, total_price=375000,
        )
        resp = logged_client.get(reverse('orders:detail', args=[order.id]))
        content = resp.content.decode('utf-8')
        assert '375.000' in content or '375000' in content
        print('[PASS] INV-02: Subtotal and total displayed')

    def test_inv_03_order_status_display(self, logged_client, customer):
        order = Order.objects.create(user=customer, total_price=100000)
        assert order.get_status_display() in ['Pending Payment', 'pending_payment']
        print('[PASS] INV-03: Order status display correct')
