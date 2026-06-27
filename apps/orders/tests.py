from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils.timezone import now
from apps.products.models import Category, Product
from apps.orders.forms import CheckoutForm
from apps.orders.models import Order, OrderItem, OrderStatusHistory
from apps.carts.models import Cart, CartItem
from apps.regions.models import Province, City, District, PostalCode
from apps.promotions.models import Voucher as PromoVoucher, UserVoucher


@pytest.mark.django_db
class TestOrderModel:
    def test_order_number_auto_generated(self):
        user = User.objects.create_user(username='testuser', password='pass12345')
        order = Order.objects.create(user=user, total_price=100000)
        assert order.order_number.startswith('ORD-')
        assert len(order.order_number) == 19

    def test_order_default_status_pending_payment(self):
        user = User.objects.create_user(username='testuser', password='pass12345')
        order = Order.objects.create(user=user, total_price=100000)
        assert order.status == Order.Status.PENDING_PAYMENT

    def test_str_representation(self):
        user = User.objects.create_user(username='testuser', password='pass12345')
        order = Order.objects.create(user=user, total_price=100000)
        assert str(order) == f'{order.order_number} - {order.user.username}'


@pytest.mark.django_db
class TestOrderStatusHistory:
    def test_history_created_on_new_order(self):
        user = User.objects.create_user(username='testuser', password='pass12345')
        order = Order.objects.create(user=user, total_price=100000)
        history = order.status_history.all()
        assert history.count() == 1
        assert history[0].status == Order.Status.PENDING_PAYMENT

    def test_history_created_on_status_change(self):
        user = User.objects.create_user(username='testuser', password='pass12345')
        order = Order.objects.create(user=user, total_price=100000)
        order.status = Order.Status.PAID
        order.save()
        history = order.status_history.all()
        assert history.count() == 2
        assert history[0].status == Order.Status.PENDING_PAYMENT
        assert history[1].status == Order.Status.PAID

    def test_history_not_duplicated_on_same_status(self):
        user = User.objects.create_user(username='testuser', password='pass12345')
        order = Order.objects.create(user=user, total_price=100000)
        order.save()
        assert order.status_history.count() == 1

    def test_history_str(self):
        user = User.objects.create_user(username='testuser', password='pass12345')
        order = Order.objects.create(user=user, total_price=100000)
        h = order.status_history.first()
        assert str(h) == f'{order.order_number}: Pending Payment'


@pytest.mark.django_db
class TestOrderViews:
    def test_order_list_requires_login(self):
        client = Client()
        response = client.get(reverse('orders:list'))
        assert response.status_code == 302

    def test_order_detail_own_order(self):
        client = Client()
        user = User.objects.create_user(username='testuser', password='pass12345')
        order = Order.objects.create(user=user, total_price=100000)
        client.force_login(user)
        response = client.get(reverse('orders:detail', args=[order.id]))
        assert response.status_code == 200

    def test_order_detail_not_owner(self):
        client = Client()
        user1 = User.objects.create_user(username='user1', password='pass12345')
        user2 = User.objects.create_user(username='user2', password='pass12345')
        order = Order.objects.create(user=user1, total_price=100000)
        client.force_login(user2)
        response = client.get(reverse('orders:detail', args=[order.id]))
        assert response.status_code == 404

    def test_cancel_pending_payment_order(self):
        client = Client()
        user = User.objects.create_user(username='testuser', password='pass12345')
        order = Order.objects.create(user=user, total_price=100000)
        client.force_login(user)
        response = client.post(reverse('orders:cancel', args=[order.id]))
        assert response.status_code == 302
        order.refresh_from_db()
        assert order.status == Order.Status.CANCELLED

    def test_cancel_non_pending_payment_fails(self):
        client = Client()
        user = User.objects.create_user(username='testuser', password='pass12345')
        order = Order.objects.create(user=user, total_price=100000, status=Order.Status.PAID)
        client.force_login(user)
        response = client.post(reverse('orders:cancel', args=[order.id]))
        assert response.status_code == 302
        order.refresh_from_db()
        assert order.status == Order.Status.PAID

    def test_create_order_insufficient_stock(self):
        client = Client()
        user = User.objects.create_user(username='testuser', password='pass12345')
        prov = Province.objects.create(code='99', name='Test Province')
        city = City.objects.create(code='99999', name='Test City', province=prov)
        dist = District.objects.create(code='99999999', name='Test District', city=city)
        pc = PostalCode.objects.create(code='12345', district=dist)
        cat = Category.objects.create(name='Cat', slug='cat')
        prod = Product.objects.create(name='Limited', slug='limited', category=cat, price=100, stock=1)
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=prod, quantity=3)
        client.force_login(user)
        response = client.post(reverse('orders:create'), {
            'recipient_name': 'Test User',
            'phone': '08123456789',
            'shipping_address': 'Jl. Merdeka No. 10',
            'province': prov.id,
            'city': city.id,
            'district': dist.id,
            'postal_code': pc.id,
        })
        assert response.status_code == 302
        assert 'Stok' in response.wsgi_request._messages._queued_messages[0].message


@pytest.mark.django_db
class TestOrderTrackView:
    def test_track_own_order(self):
        client = Client()
        user = User.objects.create_user(username='testuser', password='pass12345')
        order = Order.objects.create(user=user, total_price=100000)
        order.status = Order.Status.PAID
        order.save()
        client.force_login(user)
        response = client.get(reverse('orders:track', args=[order.id]))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Lacak Pesanan' in content
        assert 'Menunggu Pembayaran' in content
        assert 'Pembayaran Dikonfirmasi' in content
        assert 'Pesanan Diproses' in content

    def test_track_not_owner(self):
        client = Client()
        user1 = User.objects.create_user(username='user1', password='pass12345')
        user2 = User.objects.create_user(username='user2', password='pass12345')
        order = Order.objects.create(user=user1, total_price=100000)
        client.force_login(user2)
        response = client.get(reverse('orders:track', args=[order.id]))
        assert response.status_code == 404

    def test_track_requires_login(self):
        user = User.objects.create_user(username='testuser', password='pass12345')
        order = Order.objects.create(user=user, total_price=100000)
        client = Client()
        response = client.get(reverse('orders:track', args=[order.id]))
        assert response.status_code == 302

    def test_track_shows_cancelled_state(self):
        client = Client()
        user = User.objects.create_user(username='testuser', password='pass12345')
        order = Order.objects.create(user=user, total_price=100000)
        order.status = Order.Status.CANCELLED
        order.save()
        client.force_login(user)
        response = client.get(reverse('orders:track', args=[order.id]))
        content = response.content.decode()
        assert 'Pesanan Dibatalkan' in content


@pytest.mark.django_db
class TestCheckoutFormHierarchy:
    def _setup_regions(self):
        prov = Province.objects.create(code='11', name='Test Province')
        city = City.objects.create(code='1101', name='Test City', province=prov)
        dist = District.objects.create(code='110101', name='Test District', city=city)
        pc = PostalCode.objects.create(code='11111', district=dist)
        return prov, city, dist, pc

    def test_valid_hierarchy(self):
        prov, city, dist, pc = self._setup_regions()
        form = CheckoutForm(data={
            'recipient_name': 'Test', 'phone': '08123456789',
            'shipping_address': 'Jl. Test No. 10',
            'province': prov.id, 'city': city.id,
            'district': dist.id, 'postal_code': pc.id,
        })
        assert form.is_valid(), form.errors

    def test_city_not_in_province(self):
        prov, _, dist, pc = self._setup_regions()
        other_prov = Province.objects.create(code='12', name='Other')
        orphan_city = City.objects.create(code='1201', name='Orphan', province=other_prov)
        form = CheckoutForm(data={
            'recipient_name': 'Test', 'phone': '08123456789',
            'shipping_address': 'Jl. Test No. 10',
            'province': prov.id, 'city': orphan_city.id,
            'district': dist.id, 'postal_code': pc.id,
        })
        assert not form.is_valid()
        assert 'city' in form.errors

    def test_district_not_in_city(self):
        prov, city, _, pc = self._setup_regions()
        other_city = City.objects.create(code='1102', name='Other', province=prov)
        orphan_dist = District.objects.create(code='110201', name='Orphan', city=other_city)
        form = CheckoutForm(data={
            'recipient_name': 'Test', 'phone': '08123456789',
            'shipping_address': 'Jl. Test No. 10',
            'province': prov.id, 'city': city.id,
            'district': orphan_dist.id, 'postal_code': pc.id,
        })
        assert not form.is_valid()
        assert 'district' in form.errors

    def test_save_converts_fk_to_text(self):
        prov, city, dist, pc = self._setup_regions()
        form = CheckoutForm(data={
            'recipient_name': 'Test', 'phone': '08123456789',
            'shipping_address': 'Jl. Test No. 10',
            'province': prov.id, 'city': city.id,
            'district': dist.id, 'postal_code': pc.id,
        })
        assert form.is_valid()
        order = form.save(commit=False)
        assert order.province == 'Test Province'
        assert order.city == 'Test City'
        assert order.district == 'Test District'
        assert order.postal_code == '11111'


@pytest.mark.django_db
class TestVoucherFlow:
    """Test Cart → Voucher → Checkout flow end-to-end."""

    def _setup(self):
        user = User.objects.create_user(username='buyer', password='pass12345')
        cat = Category.objects.create(name='Parfum', slug='parfum')
        prod = Product.objects.create(
            name='Test Parfum', slug='test-parfum',
            category=cat, price=100000, stock=99,
        )
        Cart.objects.create(user=user)
        cart = Cart.objects.get(user=user)
        CartItem.objects.create(cart=cart, product=prod, quantity=2)
        return user, prod, cart

    def _setup_voucher(self, min_purchase=0, quota=0, expired_days=30):
        voucher = PromoVoucher.objects.create(
            code='TEST10',
            description='Test voucher 10%',
            discount_type=PromoVoucher.DiscountType.PERCENTAGE,
            discount_amount=10,
            min_purchase=min_purchase,
            max_discount=50000,
            quota=quota,
            start_date=now().date() - timedelta(days=1),
            expired_date=now().date() + timedelta(days=expired_days),
            is_active=True,
        )
        return voucher

    def _setup_regions(self):
        prov = Province.objects.create(code='11', name='Test Prov')
        city = City.objects.create(code='1101', name='Test City', province=prov)
        dist = District.objects.create(code='110101', name='Test Dist', city=city)
        pc = PostalCode.objects.create(code='11111', district=dist)
        return prov, city, dist, pc

    # --- Apply voucher tests (no order created) ---

    def test_apply_voucher_valid(self):
        user, _prod, cart = self._setup()
        self._setup_voucher()
        client = Client()
        client.force_login(user)
        response = client.post(reverse('carts:apply_voucher'), {'code': 'TEST10'}, follow=True)
        assert response.status_code == 200
        messages_list = list(response.context['messages'])
        assert any('berhasil diterapkan' in str(m) for m in messages_list)
        assert client.session.get('voucher_code') == 'TEST10'
        assert Order.objects.count() == 0

    def test_apply_voucher_expired(self):
        user, _prod, cart = self._setup()
        self._setup_voucher(expired_days=-1)
        client = Client()
        client.force_login(user)
        response = client.post(reverse('carts:apply_voucher'), {'code': 'TEST10'}, follow=True)
        messages_list = list(response.context['messages'])
        assert any('kedaluwarsa' in str(m) for m in messages_list)
        assert client.session.get('voucher_code') is None

    def test_apply_voucher_min_purchase_fails(self):
        user, _prod, cart = self._setup()
        self._setup_voucher(min_purchase=500000)
        client = Client()
        client.force_login(user)
        response = client.post(reverse('carts:apply_voucher'), {'code': 'TEST10'}, follow=True)
        messages_list = list(response.context['messages'])
        assert any('Minimum pembelian' in str(m) for m in messages_list)
        assert client.session.get('voucher_code') is None

    def test_apply_voucher_quota_exhausted(self):
        user, _prod, cart = self._setup()
        voucher = self._setup_voucher(quota=1)
        UserVoucher.objects.create(
            user=user, voucher=voucher, status=UserVoucher.Status.USED,
            expires_at=now() + timedelta(days=30),
        )
        client = Client()
        client.force_login(user)
        response = client.post(reverse('carts:apply_voucher'), {'code': 'TEST10'}, follow=True)
        messages_list = list(response.context['messages'])
        assert any('Kuota' in str(m) or 'habis' in str(m) for m in messages_list)
        assert client.session.get('voucher_code') is None

    def test_apply_voucher_does_not_create_order(self):
        user, _prod, cart = self._setup()
        self._setup_voucher()
        client = Client()
        client.force_login(user)
        client.post(reverse('carts:apply_voucher'), {'code': 'TEST10'})
        assert Order.objects.count() == 0

    # --- Cart detail shows discount ---

    def test_cart_detail_shows_discount(self):
        user, prod, cart = self._setup()
        self._setup_voucher()
        client = Client()
        client.force_login(user)
        session = client.session
        session['voucher_code'] = 'TEST10'
        session.save()
        response = client.get(reverse('carts:detail'))
        assert response.status_code == 200
        assert response.context['voucher_code'] == 'TEST10'
        expected_discount = int(200000 * 10 / 100)
        assert response.context['voucher_discount'] == expected_discount
        assert response.context['final_total'] == 200000 - expected_discount

    # --- Checkout without voucher ---

    def test_checkout_without_voucher(self):
        user, _prod, cart = self._setup()
        prov, city, dist, pc = self._setup_regions()
        client = Client()
        client.force_login(user)
        session = client.session
        session['shipping'] = {'courier_code': 'jne', 'service': 'OKE', 'cost': 15000, 'etd': '3-5'}
        session.save()
        response = client.post(reverse('orders:create'), {
            'recipient_name': 'Buyer',
            'phone': '08123456789',
            'shipping_address': 'Jl. Test No. 10',
            'province': prov.id,
            'city': city.id,
            'district': dist.id,
            'postal_code': pc.id,
        })
        assert response.status_code == 302
        assert Order.objects.count() == 1
        order = Order.objects.first()
        assert order.subtotal == 200000
        assert order.discount_amount == 0
        assert order.total_price == 200000 + 15000

    # --- Checkout with valid voucher ---

    def test_checkout_with_valid_voucher(self):
        user, _prod, cart = self._setup()
        self._setup_voucher()
        prov, city, dist, pc = self._setup_regions()
        client = Client()
        client.force_login(user)
        session = client.session
        session['voucher_code'] = 'TEST10'
        session['shipping'] = {'courier_code': 'jne', 'service': 'OKE', 'cost': 15000, 'etd': '3-5'}
        session.save()
        response = client.post(reverse('orders:create'), {
            'recipient_name': 'Buyer',
            'phone': '08123456789',
            'shipping_address': 'Jl. Test No. 10',
            'province': prov.id,
            'city': city.id,
            'district': dist.id,
            'postal_code': pc.id,
        })
        assert response.status_code == 302
        assert Order.objects.count() == 1
        order = Order.objects.first()
        assert order.subtotal == 200000
        expected_discount = int(200000 * 10 / 100)
        assert order.discount_amount == expected_discount
        assert order.total_price == 200000 - expected_discount + 15000

    # --- Checkout with invalid voucher at re-validation ---

    def test_checkout_with_expired_voucher_rejected(self):
        user, _prod, cart = self._setup()
        voucher = self._setup_voucher(expired_days=-1)
        prov, city, dist, pc = self._setup_regions()
        client = Client()
        client.force_login(user)
        session = client.session
        session['voucher_code'] = 'TEST10'
        session['shipping'] = {'courier_code': 'jne', 'service': 'OKE', 'cost': 15000, 'etd': '3-5'}
        session.save()
        response = client.post(reverse('orders:create'), {
            'recipient_name': 'Buyer',
            'phone': '08123456789',
            'shipping_address': 'Jl. Test No. 10',
            'province': prov.id,
            'city': city.id,
            'district': dist.id,
            'postal_code': pc.id,
        })
        assert response.status_code == 302
        assert Order.objects.count() == 0
        assert client.session.get('voucher_code') is None

    def test_checkout_voucher_usage_recorded(self):
        user, _prod, cart = self._setup()
        voucher = self._setup_voucher()
        uv = UserVoucher.objects.create(
            user=user, voucher=voucher, status=UserVoucher.Status.AVAILABLE,
            expires_at=now() + timedelta(days=30),
        )
        prov, city, dist, pc = self._setup_regions()
        client = Client()
        client.force_login(user)
        session = client.session
        session['voucher_code'] = 'TEST10'
        session['shipping'] = {'courier_code': 'jne', 'service': 'OKE', 'cost': 15000, 'etd': '3-5'}
        session.save()
        response = client.post(reverse('orders:create'), {
            'recipient_name': 'Buyer',
            'phone': '08123456789',
            'shipping_address': 'Jl. Test No. 10',
            'province': prov.id,
            'city': city.id,
            'district': dist.id,
            'postal_code': pc.id,
        })
        assert response.status_code == 302
        uv.refresh_from_db()
        assert uv.status == UserVoucher.Status.USED
        assert uv.used_at is not None

    # --- Discount never exceeds subtotal ---

    def test_discount_never_exceeds_subtotal(self):
        user, prod, cart = self._setup()
        PromoVoucher.objects.create(
            code='FIXED500',
            description='Rp 500k off',
            discount_type=PromoVoucher.DiscountType.FIXED,
            discount_amount=500000,
            min_purchase=0,
            start_date=now().date() - timedelta(days=1),
            expired_date=now().date() + timedelta(days=30),
            is_active=True,
        )
        prov, city, dist, pc = self._setup_regions()
        client = Client()
        client.force_login(user)
        session = client.session
        session['voucher_code'] = 'FIXED500'
        session['shipping'] = {'courier_code': 'jne', 'service': 'OKE', 'cost': 15000, 'etd': '3-5'}
        session.save()
        response = client.post(reverse('orders:create'), {
            'recipient_name': 'Buyer',
            'phone': '08123456789',
            'shipping_address': 'Jl. Test No. 10',
            'province': prov.id,
            'city': city.id,
            'district': dist.id,
            'postal_code': pc.id,
        })
        assert response.status_code == 302
        order = Order.objects.first()
        assert order.discount_amount == 200000
        assert order.total_price == 0 + 15000
