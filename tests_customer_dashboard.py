"""
Comprehensive Black-Box Tests — Customer Dashboard
Modules: Dashboard, Profile/Edit Profile, Address, Wishlist,
         Voucher (My Vouchers), Order History, Loyalty, Notifications
"""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils.timezone import now

from apps.accounts.models import (
    CustomerAddress, MemberProfile, PointTransaction, Profile, Wishlist,
)
from apps.orders.models import Order, OrderItem
from apps.products.models import Category, Product
from apps.promotions.models import UserVoucher, Voucher


# ============================================================
# Fixtures
# ============================================================
@pytest.fixture
def category():
    return Category.objects.create(name='Parfum', slug='parfum')


@pytest.fixture
def product(category):
    return Product.objects.create(
        name='Test Parfum', slug='test-parfum',
        category=category, price=100000, stock=50, is_available=True,
    )


@pytest.fixture
def unavailable_product(category):
    return Product.objects.create(
        name='Habis', slug='habis',
        category=category, price=50000, stock=0, is_available=False,
    )


@pytest.fixture
def customer():
    user = User.objects.create_user(
        username='pelanggan', password='pass123', email='cust@test.com',
    )
    MemberProfile.objects.get_or_create(user=user)
    Profile.objects.get_or_create(user=user)
    return user


@pytest.fixture
def other_user():
    return User.objects.create_user(
        username='orang_lain', password='pass123', email='other@test.com',
    )


@pytest.fixture
def superuser():
    return User.objects.create_superuser(
        username='admin', password='admin123', email='admin@test.com',
    )


@pytest.fixture
def logged_client(customer):
    client = Client()
    client.login(username='pelanggan', password='pass123')
    return client


@pytest.fixture
def superuser_client(superuser):
    client = Client()
    client.login(username='admin', password='admin123')
    return client


@pytest.fixture
def order(customer):
    return Order.objects.create(
        user=customer, total_price=100000,
        recipient_name='Budi', phone='08123456789',
        shipping_address='Jl. Merdeka No. 10, Jakarta',
        province='Aceh', city='Kab. Simeulue',
        district='Alafan', postal_code='12345',
    )


@pytest.fixture
def order_with_items(customer, product, order):
    OrderItem.objects.create(
        order=order, product=product, product_name=product.name,
        price=product.price, quantity=2,
    )
    return order


@pytest.fixture
def voucher():
    return Voucher.objects.create(
        code='DISC10',
        discount_type='percentage',
        discount_amount=10,
        min_purchase=0,
        max_discount=50000,
        voucher_type='public',
        quota=100,
        is_active=True,
        start_date=now().date(),
    )


@pytest.fixture
def user_voucher(customer, voucher):
    return UserVoucher.objects.create(
        user=customer, voucher=voucher,
        expires_at=now() + timedelta(days=30),
    )


@pytest.fixture
def wishlist_item(customer, product):
    return Wishlist.objects.create(user=customer, product=product)


# ============================================================
# DASHBOARD
# ============================================================
@pytest.mark.django_db
class TestDashboard:
    def test_dashboard_requires_login(self):
        resp = Client().get(reverse('accounts:dashboard'))
        assert resp.status_code == 302

    def test_dashboard_blocks_superuser(self, superuser_client):
        resp = superuser_client.get(reverse('accounts:dashboard'))
        assert resp.status_code == 302

    def test_dashboard_renders(self, logged_client, customer):
        resp = logged_client.get(reverse('accounts:dashboard'))
        assert resp.status_code == 200
        content = resp.content.decode()
        assert 'Dashboard' in content
        assert customer.username in content

    def test_dashboard_order_counts_zero(self, logged_client):
        resp = logged_client.get(reverse('accounts:dashboard'))
        assert resp.context['order_count'] == 0
        assert resp.context['pending_count'] == 0
        assert resp.context['completed_count'] == 0
        assert resp.context['cancelled_count'] == 0

    def test_dashboard_order_counts_with_orders(self, logged_client, customer):
        Order.objects.create(user=customer, total_price=50000, status=Order.Status.PAID)
        Order.objects.create(user=customer, total_price=30000, status=Order.Status.PENDING_PAYMENT)
        Order.objects.create(user=customer, total_price=20000, status=Order.Status.CANCELLED)
        resp = logged_client.get(reverse('accounts:dashboard'))
        assert resp.context['order_count'] == 3
        assert resp.context['pending_count'] == 1
        assert resp.context['cancelled_count'] == 1

    def test_dashboard_shows_recent_orders(self, logged_client, customer):
        o = Order.objects.create(user=customer, total_price=50000)
        resp = logged_client.get(reverse('accounts:dashboard'))
        assert o in resp.context['orders']

    def test_dashboard_voucher_counts(self, logged_client, customer, voucher):
        UserVoucher.objects.create(
            user=customer, voucher=voucher,
            expires_at=now() + timedelta(days=30),
        )
        resp = logged_client.get(reverse('accounts:dashboard'))
        assert resp.context['voucher_available'] == 1
        assert resp.context['voucher_used'] == 0
        assert resp.context['voucher_expired'] == 0

    def test_dashboard_profile_in_context(self, logged_client, customer):
        resp = logged_client.get(reverse('accounts:dashboard'))
        assert resp.context['profile'] is not None
        assert resp.context['profile'].user == customer

    def test_dashboard_no_other_user_orders(self, logged_client, customer, other_user):
        Order.objects.create(user=other_user, total_price=99999)
        resp = logged_client.get(reverse('accounts:dashboard'))
        assert resp.context['order_count'] == 0


# ============================================================
# PROFILE / EDIT PROFILE
# ============================================================
@pytest.mark.django_db
class TestProfileEdit:
    def test_profile_requires_login(self):
        resp = Client().get(reverse('accounts:profile'))
        assert resp.status_code == 302

    def test_profile_blocks_superuser(self, superuser_client):
        resp = superuser_client.get(reverse('accounts:profile'))
        assert resp.status_code == 302

    def test_profile_renders_form(self, logged_client):
        resp = logged_client.get(reverse('accounts:profile'))
        assert resp.status_code == 200
        content = resp.content.decode()
        assert 'Edit Profil' in content or 'Profil Saya' in content

    def test_profile_form_has_username_email_phone(self, logged_client):
        resp = logged_client.get(reverse('accounts:profile'))
        assert 'username' in resp.context['form'].fields
        assert 'email' in resp.context['form'].fields
        assert 'phone' in resp.context['form'].fields

    def test_profile_update_success(self, logged_client, customer):
        resp = logged_client.post(reverse('accounts:profile'), {
            'username': 'pelanggan_baru',
            'email': 'baru@test.com',
            'phone': '081234567890',
        }, follow=True)
        assert resp.status_code == 200
        customer.refresh_from_db()
        assert customer.username == 'pelanggan_baru'
        assert customer.email == 'baru@test.com'
        profile = Profile.objects.get(user=customer)
        assert profile.phone == '081234567890'

    def test_profile_update_duplicate_username(self, logged_client, customer, other_user):
        resp = logged_client.post(reverse('accounts:profile'), {
            'username': 'orang_lain',
            'email': 'cust@test.com',
            'phone': '081234567890',
        })
        assert resp.status_code == 200
        assert 'Username sudah digunakan' in resp.content.decode()

    def test_profile_update_duplicate_email(self, logged_client, customer, other_user):
        resp = logged_client.post(reverse('accounts:profile'), {
            'username': 'pelanggan',
            'email': 'other@test.com',
            'phone': '081234567890',
        })
        assert resp.status_code == 200
        assert 'Email sudah terdaftar' in resp.content.decode()

    def test_profile_update_empty_username(self, logged_client):
        resp = logged_client.post(reverse('accounts:profile'), {
            'username': '',
            'email': 'cust@test.com',
            'phone': '081234567890',
        })
        assert resp.status_code == 200
        form = resp.context['form']
        assert form.errors.get('username')

    def test_profile_update_success_message(self, logged_client):
        resp = logged_client.post(reverse('accounts:profile'), {
            'username': 'pelanggan',
            'email': 'cust@test.com',
            'phone': '081234567890',
        }, follow=True)
        assert 'berhasil diperbarui' in resp.content.decode()

    def test_profile_auto_created(self, logged_client, customer):
        Profile.objects.filter(user=customer).delete()
        resp = logged_client.get(reverse('accounts:profile'))
        assert resp.status_code == 200
        assert Profile.objects.filter(user=customer).exists()

    def test_profile_sidebar_shows_info(self, logged_client, customer):
        Profile.objects.filter(user=customer).update(phone='081234567890')
        resp = logged_client.get(reverse('accounts:dashboard'))
        content = resp.content.decode()
        assert customer.username in content
        assert customer.email in content


# ============================================================
# WISHLIST
# ============================================================
@pytest.mark.django_db
class TestWishlist:
    def test_wishlist_requires_login(self):
        resp = Client().get(reverse('accounts:wishlist_list'))
        assert resp.status_code == 302

    def test_wishlist_blocks_superuser(self, superuser_client):
        resp = superuser_client.get(reverse('accounts:wishlist_list'))
        assert resp.status_code == 302

    def test_wishlist_empty(self, logged_client):
        resp = logged_client.get(reverse('accounts:wishlist_list'))
        assert resp.status_code == 200
        assert 'Wishlist Masih Kosong' in resp.content.decode()

    def test_wishlist_shows_items(self, logged_client, product, wishlist_item):
        resp = logged_client.get(reverse('accounts:wishlist_list'))
        assert resp.status_code == 200
        assert product.name in resp.content.decode()

    def test_wishlist_add(self, logged_client, product):
        resp = logged_client.get(reverse('accounts:wishlist_add', args=[product.id]))
        assert resp.status_code == 302
        assert Wishlist.objects.filter(user=logged_client.session['_auth_user_id'], product=product).exists()

    def test_wishlist_add_duplicate(self, logged_client, product, wishlist_item):
        resp = logged_client.get(reverse('accounts:wishlist_add', args=[product.id]))
        assert resp.status_code == 302
        count = Wishlist.objects.filter(user=wishlist_item.user, product=product).count()
        assert count == 1

    def test_wishlist_add_unavailable_product(self, logged_client, unavailable_product):
        resp = logged_client.get(reverse('accounts:wishlist_add', args=[unavailable_product.id]))
        assert resp.status_code == 404

    def test_wishlist_remove(self, logged_client, product, wishlist_item):
        resp = logged_client.get(reverse('accounts:wishlist_remove', args=[product.id]))
        assert resp.status_code == 302
        assert not Wishlist.objects.filter(id=wishlist_item.id).exists()

    def test_wishlist_remove_nonexistent(self, logged_client, product):
        resp = logged_client.get(reverse('accounts:wishlist_remove', args=[product.id]))
        assert resp.status_code == 302

    def test_wishlist_add_ajax(self, logged_client, product):
        resp = logged_client.get(
            reverse('accounts:wishlist_add', args=[product.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data['saved'] is True
        assert data['in_wishlist'] is True

    def test_wishlist_remove_ajax(self, logged_client, product, wishlist_item):
        resp = logged_client.get(
            reverse('accounts:wishlist_remove', args=[product.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data['removed'] is True
        assert data['in_wishlist'] is False

    def test_wishlist_context_processor(self, logged_client, product, wishlist_item):
        resp = logged_client.get(reverse('products:list'))
        ids = resp.context.get('wishlist_product_ids', set())
        assert product.id in ids


# ============================================================
# VOUCHER — MY VOUCHERS
# ============================================================
@pytest.mark.django_db
class TestMyVouchers:
    def test_my_vouchers_requires_login(self):
        resp = Client().get(reverse('promotions:my_vouchers'))
        assert resp.status_code == 302

    def test_my_vouchers_blocks_superuser(self, superuser_client):
        resp = superuser_client.get(reverse('promotions:my_vouchers'))
        assert resp.status_code == 302

    def test_my_vouchers_empty_all(self, logged_client):
        resp = logged_client.get(reverse('promotions:my_vouchers') + '?status=all')
        assert resp.status_code == 200
        assert resp.context['counts']['available'] == 0

    def test_my_vouchers_shows_available(self, logged_client, customer, voucher, user_voucher):
        resp = logged_client.get(reverse('promotions:my_vouchers') + '?status=available')
        assert resp.status_code == 200
        assert voucher.code in resp.content.decode()
        assert resp.context['counts']['available'] == 1

    def test_my_vouchers_filter_available(self, logged_client, customer, voucher):
        uv = UserVoucher.objects.create(
            user=customer, voucher=voucher,
            expires_at=now() + timedelta(days=30),
        )
        resp = logged_client.get(reverse('promotions:my_vouchers') + '?status=available')
        assert uv in resp.context['vouchers']

    def test_my_vouchers_filter_used(self, logged_client, customer, voucher):
        uv = UserVoucher.objects.create(
            user=customer, voucher=voucher,
            status=UserVoucher.Status.USED, used_at=now(),
            expires_at=now() + timedelta(days=30),
        )
        resp = logged_client.get(reverse('promotions:my_vouchers') + '?status=used')
        assert uv in resp.context['vouchers']
        assert resp.context['counts']['used'] == 1

    def test_my_vouchers_filter_expired_by_status(self, logged_client, customer, voucher):
        uv = UserVoucher.objects.create(
            user=customer, voucher=voucher,
            status=UserVoucher.Status.EXPIRED,
            expires_at=now() - timedelta(days=1),
        )
        resp = logged_client.get(reverse('promotions:my_vouchers') + '?status=expired')
        assert uv in resp.context['vouchers']

    def test_my_vouchers_filter_expired_by_date(self, logged_client, customer, voucher):
        uv = UserVoucher.objects.create(
            user=customer, voucher=voucher,
            status=UserVoucher.Status.AVAILABLE,
            expires_at=now() - timedelta(days=1),
        )
        resp = logged_client.get(reverse('promotions:my_vouchers') + '?status=expired')
        assert uv in resp.context['vouchers']
        assert resp.context['counts']['expired'] == 1

    def test_my_vouchers_counts_accurate(self, logged_client, customer, voucher):
        v2 = Voucher.objects.create(code='DISC20', discount_type='percentage',
                                     discount_amount=20, quota=100)
        UserVoucher.objects.create(user=customer, voucher=voucher,
                                    expires_at=now() + timedelta(days=30))
        UserVoucher.objects.create(user=customer, voucher=v2,
                                    status=UserVoucher.Status.USED, used_at=now(),
                                    expires_at=now() + timedelta(days=30))
        resp = logged_client.get(reverse('promotions:my_vouchers'))
        assert resp.context['counts']['available'] == 1
        assert resp.context['counts']['used'] == 1
        assert resp.context['counts']['expired'] == 0

    def test_my_vouchers_filter_status_active_in_url(self, logged_client):
        resp = logged_client.get(reverse('promotions:my_vouchers') + '?status=available')
        assert resp.context['filter_status'] == 'available'

    def test_my_vouchers_other_user_not_visible(self, logged_client, other_user, voucher):
        UserVoucher.objects.create(user=other_user, voucher=voucher,
                                    expires_at=now() + timedelta(days=30))
        resp = logged_client.get(reverse('promotions:my_vouchers') + '?status=all')
        assert resp.context['counts']['available'] == 0

    def test_my_vouchers_accessible_via_accounts(self, logged_client):
        resp = logged_client.get('/accounts/vouchers/saya/')
        assert resp.status_code == 200


# ============================================================
# VOUCHER — CLAIM
# ============================================================
@pytest.mark.django_db
class TestVoucherClaim:
    def test_claim_requires_login(self, voucher):
        resp = Client().get(reverse('promotions:claim_voucher', args=[voucher.id]))
        assert resp.status_code == 302

    def test_claim_blocks_superuser(self, superuser_client, voucher):
        resp = superuser_client.get(reverse('promotions:claim_voucher', args=[voucher.id]))
        assert resp.status_code == 302

    def test_claim_success(self, logged_client, customer, voucher):
        resp = logged_client.get(
            reverse('promotions:claim_voucher', args=[voucher.id]),
            HTTP_REFERER=reverse('promotions:voucher_list'),
        )
        assert resp.status_code == 302
        assert UserVoucher.objects.filter(user=customer, voucher=voucher).exists()

    def test_claim_already_claimed(self, logged_client, customer, voucher, user_voucher):
        resp = logged_client.get(
            reverse('promotions:claim_voucher', args=[voucher.id]),
            HTTP_REFERER=reverse('promotions:voucher_list'),
        )
        assert resp.status_code == 302
        uv_count = UserVoucher.objects.filter(user=customer, voucher=voucher).count()
        assert uv_count == 1  # no duplicate created

    def test_claim_quota_exhausted(self, logged_client, customer):
        v = Voucher.objects.create(
            code='LIMITED', discount_type='percentage', discount_amount=10,
            quota=1, claimed_count=1, is_active=True,
        )
        resp = logged_client.get(
            reverse('promotions:claim_voucher', args=[v.id]),
            HTTP_REFERER=reverse('promotions:voucher_list'),
            follow=True,
        )
        assert 'tidak tersedia' in resp.content.decode().lower()

    def test_claim_inactive_voucher(self, logged_client, customer):
        v = Voucher.objects.create(
            code='INACTIVE', discount_type='percentage', discount_amount=10,
            is_active=False,
        )
        resp = logged_client.get(
            reverse('promotions:claim_voucher', args=[v.id]),
            HTTP_REFERER=reverse('promotions:voucher_list'),
            follow=True,
        )
        assert 'tidak tersedia' in resp.content.decode().lower()

    def test_claim_expired_voucher(self, logged_client, customer):
        v = Voucher.objects.create(
            code='EXPIRED', discount_type='percentage', discount_amount=10,
            is_active=True, expired_date=now().date() - timedelta(days=1),
        )
        resp = logged_client.get(
            reverse('promotions:claim_voucher', args=[v.id]),
            HTTP_REFERER=reverse('promotions:voucher_list'),
            follow=True,
        )
        assert 'tidak tersedia' in resp.content.decode().lower()

    def test_claim_ajax_success(self, logged_client, voucher):
        resp = logged_client.get(
            reverse('promotions:claim_voucher_ajax', args=[voucher.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data['success'] is True
        assert data['voucher_code'] == 'DISC10'

    def test_claim_ajax_already_claimed(self, logged_client, voucher, user_voucher):
        resp = logged_client.get(
            reverse('promotions:claim_voucher_ajax', args=[voucher.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data['success'] is False


# ============================================================
# ORDER HISTORY
# ============================================================
@pytest.mark.django_db
class TestOrderHistory:
    def test_order_list_requires_login(self):
        resp = Client().get(reverse('orders:list'))
        assert resp.status_code == 302

    def test_order_list_blocks_superuser(self, superuser_client):
        resp = superuser_client.get(reverse('orders:list'))
        assert resp.status_code == 302

    def test_order_list_empty(self, logged_client):
        resp = logged_client.get(reverse('orders:list'))
        assert resp.status_code == 200
        assert 'Belum Ada Pesanan' in resp.content.decode()

    def test_order_list_shows_orders(self, logged_client, customer, order):
        resp = logged_client.get(reverse('orders:list'))
        assert resp.status_code == 200
        assert order.order_number in resp.content.decode()

    def test_order_list_only_own_orders(self, logged_client, customer, other_user):
        o1 = Order.objects.create(user=customer, total_price=50000)
        o2 = Order.objects.create(user=other_user, total_price=99999)
        resp = logged_client.get(reverse('orders:list'))
        assert o1 in resp.context['orders']
        assert o2 not in resp.context['orders']

    def test_order_list_newest_first(self, logged_client, customer):
        o1 = Order.objects.create(user=customer, total_price=10000)
        o2 = Order.objects.create(user=customer, total_price=20000)
        resp = logged_client.get(reverse('orders:list'))
        orders = list(resp.context['orders'])
        assert orders[0] == o2
        assert orders[1] == o1

    def test_order_list_shows_payment_status(self, logged_client, customer, order):
        resp = logged_client.get(reverse('orders:list'))
        assert 'pending_payment' in resp.content.decode() or 'pending' in resp.content.decode().lower()

    def test_order_detail_requires_login(self, order):
        resp = Client().get(reverse('orders:detail', args=[order.id]))
        assert resp.status_code == 302

    def test_order_detail_blocks_superuser(self, superuser_client, order):
        resp = superuser_client.get(reverse('orders:detail', args=[order.id]))
        assert resp.status_code == 302

    def test_order_detail_renders(self, logged_client, order):
        resp = logged_client.get(reverse('orders:detail', args=[order.id]))
        assert resp.status_code == 200
        assert order.order_number in resp.content.decode()

    def test_order_detail_other_user_404(self, logged_client, other_user):
        o = Order.objects.create(user=other_user, total_price=50000)
        resp = logged_client.get(reverse('orders:detail', args=[o.id]))
        assert resp.status_code == 404

    def test_order_detail_shows_items(self, logged_client, order_with_items):
        resp = logged_client.get(reverse('orders:detail', args=[order_with_items.id]))
        assert resp.status_code == 200
        assert 'Test Parfum' in resp.content.decode()

    def test_order_detail_cancel_button_pending(self, logged_client, order):
        resp = logged_client.get(reverse('orders:detail', args=[order.id]))
        content = resp.content.decode()
        assert 'Batalkan' in content

    def test_order_detail_no_cancel_button_paid(self, logged_client, order):
        order.status = Order.Status.PAID
        order.save()
        resp = logged_client.get(reverse('orders:detail', args=[order.id]))
        content = resp.content.decode()
        # Should not have cancel button for paid orders
        assert 'Batalkan' not in content or 'tidak dapat dibatalkan' in content


# ============================================================
# ORDER CANCEL
# ============================================================
@pytest.mark.django_db
class TestOrderCancel:
    def test_cancel_requires_login(self, order):
        resp = Client().get(reverse('orders:cancel', args=[order.id]))
        assert resp.status_code == 302

    def test_cancel_blocks_superuser(self, superuser_client, order):
        resp = superuser_client.get(reverse('orders:cancel', args=[order.id]))
        assert resp.status_code == 302

    def test_cancel_pending_success(self, logged_client, order):
        resp = logged_client.post(reverse('orders:cancel', args=[order.id]), follow=True)
        order.refresh_from_db()
        assert order.status == Order.Status.CANCELLED
        assert 'berhasil dibatalkan' in resp.content.decode()

    def test_cancel_paid_fails(self, logged_client, order):
        order.status = Order.Status.PAID
        order.save()
        resp = logged_client.post(reverse('orders:cancel', args=[order.id]), follow=True)
        order.refresh_from_db()
        assert order.status == Order.Status.PAID
        assert 'tidak dapat dibatalkan' in resp.content.decode()

    def test_cancel_already_cancelled(self, logged_client, order):
        order.status = Order.Status.CANCELLED
        order.save()
        resp = logged_client.post(reverse('orders:cancel', args=[order.id]), follow=True)
        order.refresh_from_db()
        assert order.status == Order.Status.CANCELLED

    def test_cancel_other_user_404(self, logged_client, other_user):
        o = Order.objects.create(user=other_user, total_price=50000)
        resp = logged_client.post(reverse('orders:cancel', args=[o.id]))
        assert resp.status_code == 404


# ============================================================
# ORDER CONFIRM RECEIVED
# ============================================================
@pytest.mark.django_db
class TestOrderConfirmReceived:
    def test_confirm_requires_login(self, order):
        resp = Client().get(reverse('orders:confirm_received', args=[order.id]))
        assert resp.status_code == 302

    def test_confirm_blocks_superuser(self, superuser_client, order):
        resp = superuser_client.get(reverse('orders:confirm_received', args=[order.id]))
        assert resp.status_code == 302

    def test_confirm_delivered_success(self, logged_client, order):
        order.status = Order.Status.DELIVERED
        order.save()
        resp = logged_client.post(reverse('orders:confirm_received', args=[order.id]), follow=True)
        order.refresh_from_db()
        assert order.status == Order.Status.COMPLETED
        assert 'berhasil diselesaikan' in resp.content.decode()

    def test_confirm_pending_fails(self, logged_client, order):
        resp = logged_client.post(reverse('orders:confirm_received', args=[order.id]), follow=True)
        order.refresh_from_db()
        assert order.status == Order.Status.PENDING_PAYMENT
        assert 'Pesanan Sampai' in resp.content.decode()

    def test_confirm_other_user_404(self, logged_client, other_user):
        o = Order.objects.create(user=other_user, total_price=50000)
        resp = logged_client.post(reverse('orders:confirm_received', args=[o.id]))
        assert resp.status_code == 404


# ============================================================
# ORDER TRACK
# ============================================================
@pytest.mark.django_db
class TestOrderTrack:
    def test_track_requires_login(self, order):
        resp = Client().get(reverse('orders:track', args=[order.id]))
        assert resp.status_code == 302

    def test_track_blocks_superuser(self, superuser_client, order):
        resp = superuser_client.get(reverse('orders:track', args=[order.id]))
        assert resp.status_code == 302

    def test_track_renders_timeline(self, logged_client, order):
        resp = logged_client.get(reverse('orders:track', args=[order.id]))
        assert resp.status_code == 200
        assert 'timeline' in resp.context or 'order' in resp.context

    def test_track_shows_pending_status(self, logged_client, order):
        resp = logged_client.get(reverse('orders:track', args=[order.id]))
        assert resp.status_code == 200
        content = resp.content.decode()
        assert 'Menunggu' in content

    def test_track_shows_cancelled_state(self, logged_client, order):
        order.status = Order.Status.CANCELLED
        order.save()
        resp = logged_client.get(reverse('orders:track', args=[order.id]))
        assert resp.status_code == 200

    def test_track_other_user_404(self, logged_client, other_user):
        o = Order.objects.create(user=other_user, total_price=50000)
        resp = logged_client.get(reverse('orders:track', args=[o.id]))
        assert resp.status_code == 404


# ============================================================
# LOYALTY — MEMBER DASHBOARD
# ============================================================
@pytest.mark.django_db
class TestMemberDashboard:
    def test_member_dashboard_requires_login(self):
        resp = Client().get(reverse('accounts:member_dashboard'))
        assert resp.status_code == 302

    def test_member_dashboard_blocks_superuser(self, superuser_client):
        resp = superuser_client.get(reverse('accounts:member_dashboard'))
        assert resp.status_code == 302

    def test_member_dashboard_renders(self, logged_client, customer):
        resp = logged_client.get(reverse('accounts:member_dashboard'))
        assert resp.status_code == 200
        assert 'Loyalty' in resp.content.decode() or 'Member' in resp.content.decode()

    def test_member_dashboard_shows_level(self, logged_client, customer):
        resp = logged_client.get(reverse('accounts:member_dashboard'))
        member = resp.context['member']
        assert member.level in ('SILVER', 'GOLD', 'PLATINUM')

    def test_member_dashboard_shows_points(self, logged_client, customer):
        member = MemberProfile.objects.get(user=customer)
        member.total_points = 500
        member.save()
        resp = logged_client.get(reverse('accounts:member_dashboard'))
        assert resp.context['member'].total_points == 500
        assert '500' in resp.content.decode()

    def test_member_dashboard_shows_total_spending(self, logged_client, customer):
        member = MemberProfile.objects.get(user=customer)
        member.total_spending = 2000000
        member.save()
        resp = logged_client.get(reverse('accounts:member_dashboard'))
        assert resp.context['member'].total_spending == 2000000

    def test_member_dashboard_points_history_empty(self, logged_client):
        resp = logged_client.get(reverse('accounts:member_dashboard'))
        assert len(resp.context['points_history']) == 0
        assert 'Belum Ada Riwayat Poin' in resp.content.decode()

    def test_member_dashboard_points_history_shown(self, logged_client, customer):
        PointTransaction.objects.create(
            user=customer, points=100, type=PointTransaction.Type.EARN,
            description='Poin test',
        )
        resp = logged_client.get(reverse('accounts:member_dashboard'))
        assert len(resp.context['points_history']) == 1
        assert 'Poin test' in resp.content.decode()

    def test_member_dashboard_levels_data_in_context(self, logged_client):
        resp = logged_client.get(reverse('accounts:member_dashboard'))
        assert 'levels_data' in resp.context
        assert 'SILVER' in resp.context['levels_data']

    def test_member_dashboard_silver_default(self, logged_client, customer):
        member = MemberProfile.objects.get(user=customer)
        assert member.level == 'SILVER'

    def test_member_dashboard_gold_after_spending(self, logged_client, customer):
        member = MemberProfile.objects.get(user=customer)
        member.total_spending = 1000000
        member.upgrade_level()
        member.refresh_from_db()
        assert member.level == 'GOLD'

    def test_member_dashboard_platinum_after_spending(self, logged_client, customer):
        member = MemberProfile.objects.get(user=customer)
        member.total_spending = 5000000
        member.upgrade_level()
        member.refresh_from_db()
        assert member.level == 'PLATINUM'

    def test_point_transaction_earn_creates_record(self, logged_client, customer):
        member = MemberProfile.objects.get(user=customer)
        member.earn_points(100000)
        assert PointTransaction.objects.filter(user=customer, type=PointTransaction.Type.EARN).exists()

    def test_point_transaction_upgrade_creates_record(self, logged_client, customer):
        member = MemberProfile.objects.get(user=customer)
        member.total_spending = 1000000
        member.upgrade_level()
        assert PointTransaction.objects.filter(user=customer, type=PointTransaction.Type.UPGRADE).exists()


# ============================================================
# CONTEXT PROCESSORS
# ============================================================
@pytest.mark.django_db
class TestContextProcessors:
    def test_cart_count_zero(self, logged_client):
        resp = logged_client.get(reverse('products:list'))
        assert resp.context['cart_count'] == 0

    def test_wishlist_ids_empty(self, logged_client):
        resp = logged_client.get(reverse('products:list'))
        assert resp.context['wishlist_product_ids'] == set()

    def test_wishlist_ids_with_item(self, logged_client, product, wishlist_item):
        resp = logged_client.get(reverse('products:list'))
        assert product.id in resp.context['wishlist_product_ids']

    def test_voucher_notification_zero(self, logged_client):
        resp = logged_client.get(reverse('products:list'))
        assert resp.context['unclaimed_vouchers_count'] == 0

    def test_voucher_notification_with_vouchers(self, logged_client, customer, voucher):
        UserVoucher.objects.create(
            user=customer, voucher=voucher,
            expires_at=now() + timedelta(days=30),
        )
        resp = logged_client.get(reverse('products:list'))
        assert resp.context['unclaimed_vouchers_count'] == 1

    def test_floating_vouchers_in_context(self, logged_client, voucher):
        resp = logged_client.get(reverse('products:list'))
        assert 'floating_vouchers' in resp.context

    def test_cart_count_anonymous(self):
        resp = Client().get(reverse('products:list'))
        assert resp.context['cart_count'] == 0

    def test_wishlist_ids_anonymous(self):
        resp = Client().get(reverse('products:list'))
        assert resp.context['wishlist_product_ids'] == set()

    def test_voucher_notification_anonymous(self):
        resp = Client().get(reverse('products:list'))
        assert resp.context['unclaimed_vouchers_count'] == 0


# ============================================================
# SUPERUSER BLOCKED ON ALL CUSTOMER VIEWS
# ============================================================
@pytest.mark.django_db
class TestSuperuserBlocked:
    """Verify all customer-facing views redirect superusers."""

    @pytest.fixture
    def assert_blocked(self, superuser_client):
        def _check(url_name, *args):
            resp = superuser_client.get(reverse(url_name, args=args))
            assert resp.status_code == 302, f'{url_name} did not block superuser'
        return _check

    def test_dashboard_blocked(self, assert_blocked):
        assert_blocked('accounts:dashboard')

    def test_profile_blocked(self, assert_blocked):
        assert_blocked('accounts:profile')

    def test_wishlist_blocked(self, assert_blocked):
        assert_blocked('accounts:wishlist_list')

    def test_member_dashboard_blocked(self, assert_blocked):
        assert_blocked('accounts:member_dashboard')

    def test_my_vouchers_blocked(self, assert_blocked):
        assert_blocked('promotions:my_vouchers')

    def test_address_list_blocked(self, assert_blocked):
        assert_blocked('accounts:address_list')

    def test_order_list_blocked(self, assert_blocked):
        assert_blocked('orders:list')

    def test_order_create_blocked(self, assert_blocked):
        assert_blocked('orders:create')
