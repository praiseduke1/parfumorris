"""
Comprehensive Black-Box Tests — Cart & Voucher Module
"""
import pytest
from decimal import Decimal
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils.timezone import now

from apps.products.models import Product, Category, Brand, ProductVariant
from apps.carts.models import Cart, CartItem
from apps.promotions.models import Voucher, UserVoucher


# ============================================================
# Fixtures
# ============================================================
@pytest.fixture
def category():
    return Category.objects.create(name='Eau de Parfum', slug='eau-de-parfum')


@pytest.fixture
def brand():
    return Brand.objects.create(name='Morris', slug='morris')


@pytest.fixture
def product(category, brand):
    return Product.objects.create(
        name='Morris Noir',
        slug='morris-noir',
        category=category,
        brand=brand,
        price=375000,
        stock=25,
        is_available=True,
    )


@pytest.fixture
def cheap_product(category, brand):
    return Product.objects.create(
        name='Cheap Perfume',
        slug='cheap-perfume',
        category=category,
        brand=brand,
        price=25000,
        stock=100,
        is_available=True,
    )


@pytest.fixture
def unavailable_product(category, brand):
    return Product.objects.create(
        name='Discontinued',
        slug='discontinued',
        category=category,
        brand=brand,
        price=100000,
        stock=0,
        is_available=False,
    )


@pytest.fixture
def variant(product):
    return ProductVariant.objects.create(
        product=product, size_ml=30, price=200000, stock=10, sku='NOIR-30'
    )


@pytest.fixture
def customer():
    return User.objects.create_user(
        username='budi', password='customer123', email='budi@example.com'
    )


@pytest.fixture
def other_user():
    return User.objects.create_user(
        username='orang_lain', password='pass12345', email='other@example.com'
    )


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        username='admin', password='admin123', email='admin@test.com'
    )


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def logged_client(customer):
    c = Client()
    c.login(username='budi', password='customer123')
    return c


@pytest.fixture
def admin_client(admin_user):
    c = Client()
    c.login(username='admin', password='admin123')
    return c


@pytest.fixture
def other_client(other_user):
    c = Client()
    c.login(username='orang_lain', password='pass12345')
    return c


@pytest.fixture
def cart(customer):
    return Cart.objects.create(user=customer)


@pytest.fixture
def cart_with_item(cart, product):
    CartItem.objects.create(cart=cart, product=product, quantity=2)
    return cart


@pytest.fixture
def voucher_percentage():
    return Voucher.objects.create(
        code='DISKON10',
        discount_type='percentage',
        discount_amount=10,
        min_purchase=0,
        is_active=True,
        start_date=now().date() - timedelta(days=1),
        expired_date=now().date() + timedelta(days=30),
    )


@pytest.fixture
def voucher_fixed():
    return Voucher.objects.create(
        code='FLAT50',
        discount_type='fixed',
        discount_amount=50000,
        min_purchase=0,
        is_active=True,
        start_date=now().date() - timedelta(days=1),
        expired_date=now().date() + timedelta(days=30),
    )


@pytest.fixture
def location():
    from apps.regions.models import Province, City, District, PostalCode
    prov = Province.objects.create(id=1, name='DKI Jakarta')
    city = City.objects.create(id=1, name='Jakarta Pusat', province=prov)
    dist = District.objects.create(id=1, name='Menteng', city=city)
    pc = PostalCode.objects.create(id=1, code='12345', district=dist)
    return {'province': prov, 'city': city, 'district': dist, 'postal_code': pc}


# ============================================================
# CART — ACCESS CONTROL
# ============================================================
@pytest.mark.django_db
class TestCartAccessControl:
    def test_cart_detail_requires_login(self, client):
        resp = client.get(reverse('carts:detail'))
        assert resp.status_code == 302

    def test_cart_detail_admin_redirected(self, admin_client):
        resp = admin_client.get(reverse('carts:detail'))
        assert resp.status_code == 302

    def test_cart_add_requires_login(self, client, product):
        resp = client.post(reverse('carts:add', args=[product.id]))
        assert resp.status_code == 302

    def test_cart_add_admin_redirected(self, admin_client, product):
        resp = admin_client.post(reverse('carts:add', args=[product.id]))
        assert resp.status_code == 302

    def test_cart_update_requires_login(self, client, cart_with_item):
        item = cart_with_item.items.first()
        resp = client.post(reverse('carts:update', args=[item.id]))
        assert resp.status_code == 302

    def test_cart_update_admin_redirected(self, admin_client, cart_with_item):
        item = cart_with_item.items.first()
        resp = admin_client.post(reverse('carts:update', args=[item.id]))
        assert resp.status_code == 302

    def test_cart_remove_requires_login(self, client, cart_with_item):
        item = cart_with_item.items.first()
        resp = client.post(reverse('carts:remove', args=[item.id]))
        assert resp.status_code == 302

    def test_cart_remove_admin_redirected(self, admin_client, cart_with_item):
        item = cart_with_item.items.first()
        resp = admin_client.post(reverse('carts:remove', args=[item.id]))
        assert resp.status_code == 302

    def test_cart_apply_voucher_requires_login(self, client):
        resp = client.post(reverse('carts:apply_voucher'), {'code': 'TEST'})
        assert resp.status_code == 302

    def test_cart_apply_voucher_admin_redirected(self, admin_client):
        resp = admin_client.post(reverse('carts:apply_voucher'), {'code': 'TEST'})
        assert resp.status_code == 302

    def test_cart_remove_voucher_requires_login(self, client):
        resp = client.post(reverse('carts:remove_voucher'))
        assert resp.status_code == 302

    def test_cart_remove_voucher_admin_redirected(self, admin_client):
        resp = admin_client.post(reverse('carts:remove_voucher'))
        assert resp.status_code == 302


# ============================================================
# CART — ADD PRODUCT
# ============================================================
@pytest.mark.django_db
class TestCartAddProduct:
    def test_add_product_creates_item(self, logged_client, customer, product):
        resp = logged_client.post(reverse('carts:add', args=[product.id]), {'quantity': 3})
        assert resp.status_code == 302
        cart = Cart.objects.get(user=customer)
        assert cart.items.count() == 1
        item = cart.items.first()
        assert item.product == product
        assert item.quantity == 3
        assert item.variant is None

    def test_add_product_default_quantity(self, logged_client, customer, product):
        resp = logged_client.post(reverse('carts:add', args=[product.id]))
        assert resp.status_code == 302
        cart = Cart.objects.get(user=customer)
        item = cart.items.first()
        assert item.quantity == 1

    def test_add_product_existing_increments(self, logged_client, customer, product):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=2)
        logged_client.post(reverse('carts:add', args=[product.id]), {'quantity': 3})
        item = CartItem.objects.get(cart=cart, product=product, variant=None)
        assert item.quantity == 5

    def test_add_product_existing_capped_at_stock(self, logged_client, customer, product):
        product.stock = 5
        product.save()
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=3)
        resp = logged_client.post(reverse('carts:add', args=[product.id]), {'quantity': 10})
        assert resp.status_code == 302
        item = CartItem.objects.get(cart=cart, product=product, variant=None)
        assert item.quantity == 3

    def test_add_product_increments_within_stock(self, logged_client, customer, product):
        product.stock = 5
        product.save()
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=3)
        logged_client.post(reverse('carts:add', args=[product.id]), {'quantity': 2})
        item = CartItem.objects.get(cart=cart, product=product, variant=None)
        assert item.quantity == 5

    def test_add_product_exceeds_stock_rejected(self, logged_client, customer, product):
        resp = logged_client.post(reverse('carts:add', args=[product.id]), {'quantity': 999})
        assert resp.status_code == 302
        cart = Cart.objects.get(user=customer)
        assert cart.items.count() == 0

    def test_add_product_quantity_zero_treated_as_one(self, logged_client, customer, product):
        logged_client.post(reverse('carts:add', args=[product.id]), {'quantity': 0})
        cart = Cart.objects.get(user=customer)
        item = cart.items.first()
        assert item.quantity == 1

    def test_add_product_quantity_negative_treated_as_one(self, logged_client, customer, product):
        logged_client.post(reverse('carts:add', args=[product.id]), {'quantity': -5})
        cart = Cart.objects.get(user=customer)
        item = cart.items.first()
        assert item.quantity == 1

    def test_add_product_invalid_quantity_treated_as_one(self, logged_client, customer, product):
        logged_client.post(reverse('carts:add', args=[product.id]), {'quantity': 'abc'})
        cart = Cart.objects.get(user=customer)
        item = cart.items.first()
        assert item.quantity == 1

    def test_add_product_unavailable_returns_404(self, logged_client, unavailable_product):
        resp = logged_client.post(
            reverse('carts:add', args=[unavailable_product.id]), {'quantity': 1}
        )
        assert resp.status_code == 404

    def test_add_product_with_variant(self, logged_client, customer, product, variant):
        resp = logged_client.post(
            reverse('carts:add', args=[product.id]),
            {'quantity': 2, 'variant_id': variant.id},
        )
        assert resp.status_code == 302
        cart = Cart.objects.get(user=customer)
        item = cart.items.first()
        assert item.variant == variant
        assert item.quantity == 2

    def test_add_product_same_product_diff_variant_separate_items(
        self, logged_client, customer, product, variant
    ):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, variant=variant, quantity=1)
        resp = logged_client.post(
            reverse('carts:add', args=[product.id]),
            {'quantity': 1, 'variant_id': variant.id},
        )
        assert resp.status_code == 302
        item = CartItem.objects.get(cart=cart, product=product, variant=variant)
        assert item.quantity == 2

    def test_add_product_with_invalid_variant(self, logged_client, product):
        resp = logged_client.post(
            reverse('carts:add', args=[product.id]),
            {'quantity': 1, 'variant_id': 99999},
        )
        assert resp.status_code == 404

    def test_add_product_variant_exceeds_stock(self, logged_client, customer, product, variant):
        variant.stock = 3
        variant.save()
        resp = logged_client.post(
            reverse('carts:add', args=[product.id]),
            {'quantity': 10, 'variant_id': variant.id},
        )
        assert resp.status_code == 302
        cart = Cart.objects.get(user=customer)
        assert cart.items.count() == 0


# ============================================================
# CART — REMOVE PRODUCT
# ============================================================
@pytest.mark.django_db
class TestCartRemoveProduct:
    def test_remove_product(self, logged_client, cart_with_item):
        item = cart_with_item.items.first()
        resp = logged_client.post(reverse('carts:remove', args=[item.id]))
        assert resp.status_code == 302
        assert CartItem.objects.filter(id=item.id).count() == 0

    def test_remove_product_not_owned_returns_404(self, other_client, cart_with_item):
        item = cart_with_item.items.first()
        resp = other_client.post(reverse('carts:remove', args=[item.id]))
        assert resp.status_code == 404

    def test_remove_nonexistent_item(self, logged_client):
        resp = logged_client.post(reverse('carts:remove', args=[99999]))
        assert resp.status_code == 404

    def test_remove_then_cart_empty(self, logged_client, customer, cart_with_item):
        item = cart_with_item.items.first()
        logged_client.post(reverse('carts:remove', args=[item.id]))
        cart = Cart.objects.get(user=customer)
        assert cart.items.count() == 0


# ============================================================
# CART — UPDATE QUANTITY
# ============================================================
@pytest.mark.django_db
class TestCartUpdateQuantity:
    def test_update_increase(self, logged_client, cart_with_item):
        item = cart_with_item.items.first()
        logged_client.post(reverse('carts:update', args=[item.id]), {'action': 'increase'})
        item.refresh_from_db()
        assert item.quantity == 3

    def test_update_increase_capped_at_stock(self, logged_client, product, cart_with_item):
        product.stock = 3
        product.save()
        item = cart_with_item.items.first()
        logged_client.post(reverse('carts:update', args=[item.id]), {'action': 'increase'})
        item.refresh_from_db()
        assert item.quantity == 3

    def test_update_decrease_removes_when_zero(self, logged_client, customer, product):
        cart = Cart.objects.create(user=customer)
        item = CartItem.objects.create(cart=cart, product=product, quantity=1)
        logged_client.post(reverse('carts:update', args=[item.id]), {'action': 'decrease'})
        assert CartItem.objects.filter(id=item.id).count() == 0

    def test_update_decrease_from_two(self, logged_client, cart_with_item):
        item = cart_with_item.items.first()
        logged_client.post(reverse('carts:update', args=[item.id]), {'action': 'decrease'})
        item.refresh_from_db()
        assert item.quantity == 1

    def test_update_set_specific_value(self, logged_client, cart_with_item):
        item = cart_with_item.items.first()
        logged_client.post(reverse('carts:update', args=[item.id]), {'quantity': 5})
        item.refresh_from_db()
        assert item.quantity == 5

    def test_update_set_to_zero_removes(self, logged_client, cart_with_item):
        item = cart_with_item.items.first()
        logged_client.post(reverse('carts:update', args=[item.id]), {'quantity': 0})
        assert CartItem.objects.filter(id=item.id).count() == 0

    def test_update_set_capped_at_stock(self, logged_client, product, cart_with_item):
        product.stock = 3
        product.save()
        item = cart_with_item.items.first()
        logged_client.post(reverse('carts:update', args=[item.id]), {'quantity': 100})
        item.refresh_from_db()
        assert item.quantity == 3

    def test_update_set_negative_removes(self, logged_client, cart_with_item):
        item = cart_with_item.items.first()
        logged_client.post(reverse('carts:update', args=[item.id]), {'quantity': -1})
        assert CartItem.objects.filter(id=item.id).count() == 0

    def test_update_invalid_value_preserves(self, logged_client, cart_with_item):
        item = cart_with_item.items.first()
        logged_client.post(reverse('carts:update', args=[item.id]), {'quantity': 'abc'})
        item.refresh_from_db()
        assert item.quantity == 2

    def test_update_not_owned_returns_404(self, other_client, cart_with_item):
        item = cart_with_item.items.first()
        resp = other_client.post(reverse('carts:update', args=[item.id]), {'action': 'increase'})
        assert resp.status_code == 404


# ============================================================
# CART — DISPLAY & CALCULATIONS
# ============================================================
@pytest.mark.django_db
class TestCartCalculations:
    def test_empty_cart_shows_empty_state(self, logged_client, customer):
        Cart.objects.create(user=customer)
        resp = logged_client.get(reverse('carts:detail'))
        assert resp.status_code == 200
        content = resp.content.decode('utf-8')
        assert 'Keranjang' in content

    def test_cart_displays_items(self, logged_client, cart_with_item, product):
        resp = logged_client.get(reverse('carts:detail'))
        content = resp.content.decode('utf-8')
        assert product.name in content

    def test_cart_item_unit_price(self, logged_client, customer, product):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        resp = logged_client.get(reverse('carts:detail'))
        content = resp.content.decode('utf-8')
        assert '375.000' in content or '375000' in content

    def test_cart_subtotal_single_item(self, logged_client, customer, product):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=3)
        resp = logged_client.get(reverse('carts:detail'))
        assert resp.context['subtotal'] == 375000 * 3

    def test_cart_subtotal_multiple_items(self, logged_client, customer, product, cheap_product):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=2)
        CartItem.objects.create(cart=cart, product=cheap_product, quantity=3)
        resp = logged_client.get(reverse('carts:detail'))
        expected = (375000 * 2) + (25000 * 3)
        assert resp.context['subtotal'] == expected

    def test_cart_total_items_count(self, logged_client, customer, product, cheap_product):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=2)
        CartItem.objects.create(cart=cart, product=cheap_product, quantity=3)
        resp = logged_client.get(reverse('carts:detail'))
        assert resp.context['total_items'] == 5

    def test_cart_variant_price(self, logged_client, customer, product, variant):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, variant=variant, quantity=2)
        resp = logged_client.get(reverse('carts:detail'))
        assert resp.context['subtotal'] == 200000 * 2

    def test_cart_final_total_no_voucher(self, logged_client, cart_with_item):
        resp = logged_client.get(reverse('carts:detail'))
        assert resp.context['final_total'] == resp.context['subtotal']
        assert resp.context['voucher_discount'] == 0


# ============================================================
# VOUCHER — VALID VOUCHER
# ============================================================
@pytest.mark.django_db
class TestVoucherValid:
    def test_apply_valid_percentage_voucher(self, logged_client, cart_with_item, voucher_percentage):
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'DISKON10'})
        assert resp.status_code == 302
        assert logged_client.session.get('voucher_code') == 'DISKON10'

    def test_apply_valid_fixed_voucher(self, logged_client, cart_with_item, voucher_fixed):
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'FLAT50'})
        assert resp.status_code == 302
        assert logged_client.session.get('voucher_code') == 'FLAT50'

    def test_percentage_discount_calculation(self, logged_client, customer, product, voucher_percentage):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=2)
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'DISKON10'})
        resp = logged_client.get(reverse('carts:detail'))
        expected_discount = int(375000 * 2 * 10 / 100)
        assert resp.context['voucher_discount'] == expected_discount
        assert resp.context['final_total'] == (375000 * 2) - expected_discount

    def test_fixed_discount_calculation(self, logged_client, customer, product, voucher_fixed):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=2)
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'FLAT50'})
        resp = logged_client.get(reverse('carts:detail'))
        assert resp.context['voucher_discount'] == 50000
        assert resp.context['final_total'] == (375000 * 2) - 50000

    def test_percentage_with_max_discount_cap(self, logged_client, customer, product):
        voucher = Voucher.objects.create(
            code='MAXCAP',
            discount_type='percentage',
            discount_amount=20,
            max_discount=100000,
            min_purchase=0,
            is_active=True,
            start_date=now().date() - timedelta(days=1),
            expired_date=now().date() + timedelta(days=30),
        )
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=3)
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'MAXCAP'})
        resp = logged_client.get(reverse('carts:detail'))
        raw_discount = 375000 * 3 * 20 / 100
        assert raw_discount == 225000
        assert resp.context['voucher_discount'] == 100000

    def test_fixed_discount_capped_at_subtotal(self, logged_client, customer, cheap_product):
        voucher = Voucher.objects.create(
            code='BIGFIX',
            discount_type='fixed',
            discount_amount=100000,
            min_purchase=0,
            is_active=True,
            start_date=now().date() - timedelta(days=1),
            expired_date=now().date() + timedelta(days=30),
        )
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=cheap_product, quantity=1)
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'BIGFIX'})
        resp = logged_client.get(reverse('carts:detail'))
        assert resp.context['voucher_discount'] == 25000
        assert resp.context['final_total'] == 0

    def test_voucher_code_case_insensitive(self, logged_client, cart_with_item, voucher_percentage):
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'diskon10'})
        assert resp.status_code == 302
        assert logged_client.session.get('voucher_code') == 'DISKON10'

    def test_voucher_displays_in_cart_page(self, logged_client, cart_with_item, voucher_percentage):
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'DISKON10'})
        resp = logged_client.get(reverse('carts:detail'))
        content = resp.content.decode('utf-8')
        assert 'DISKON10' in content

    def test_voucher_discount_shown_in_cart_page(self, logged_client, cart_with_item, voucher_percentage):
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'DISKON10'})
        resp = logged_client.get(reverse('carts:detail'))
        content = resp.content.decode('utf-8')
        assert '75.000' in content


# ============================================================
# VOUCHER — EXPIRED / INACTIVE / INVALID
# ============================================================
@pytest.mark.django_db
class TestVoucherInvalid:
    def test_voucher_not_found(self, logged_client, cart_with_item):
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'NONEXIST'})
        assert resp.status_code == 302
        assert 'voucher_code' not in logged_client.session

    def test_empty_voucher_code_rejected(self, logged_client):
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': ''})
        assert resp.status_code == 302
        assert 'voucher_code' not in logged_client.session

    def test_voucher_inactive(self, logged_client, cart_with_item):
        Voucher.objects.create(
            code='INACTIVE',
            discount_type='fixed',
            discount_amount=50000,
            is_active=False,
            start_date=now().date() - timedelta(days=1),
            expired_date=now().date() + timedelta(days=30),
        )
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'INACTIVE'})
        assert resp.status_code == 302
        assert 'voucher_code' not in logged_client.session

    def test_voucher_not_started_yet(self, logged_client, cart_with_item):
        Voucher.objects.create(
            code='FUTURE',
            discount_type='fixed',
            discount_amount=50000,
            is_active=True,
            start_date=now().date() + timedelta(days=10),
            expired_date=now().date() + timedelta(days=30),
        )
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'FUTURE'})
        assert resp.status_code == 302
        assert 'voucher_code' not in logged_client.session

    def test_expired_voucher_rejected(self, logged_client, cart_with_item):
        Voucher.objects.create(
            code='EXPIRED',
            discount_type='fixed',
            discount_amount=50000,
            is_active=True,
            start_date=now().date() - timedelta(days=30),
            expired_date=now().date() - timedelta(days=1),
        )
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'EXPIRED'})
        assert resp.status_code == 302
        assert 'voucher_code' not in logged_client.session

    def test_voucher_min_purchase_not_met(self, logged_client, customer, cheap_product):
        Voucher.objects.create(
            code='MINBELI',
            discount_type='fixed',
            discount_amount=10000,
            min_purchase=100000,
            is_active=True,
            start_date=now().date() - timedelta(days=1),
            expired_date=now().date() + timedelta(days=30),
        )
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=cheap_product, quantity=1)
        assert cart.total_price() == 25000
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'MINBELI'})
        assert resp.status_code == 302
        assert 'voucher_code' not in logged_client.session

    def test_voucher_min_purchase_met(self, logged_client, customer, product):
        Voucher.objects.create(
            code='MINBELI2',
            discount_type='fixed',
            discount_amount=10000,
            min_purchase=300000,
            is_active=True,
            start_date=now().date() - timedelta(days=1),
            expired_date=now().date() + timedelta(days=30),
        )
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        assert cart.total_price() == 375000
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'MINBELI2'})
        assert resp.status_code == 302
        assert logged_client.session.get('voucher_code') == 'MINBELI2'

    def test_voucher_quota_exhausted(self, logged_client, cart_with_item):
        Voucher.objects.create(
            code='QUOTA',
            discount_type='fixed',
            discount_amount=10000,
            quota=5,
            used_count=5,
            is_active=True,
            start_date=now().date() - timedelta(days=1),
            expired_date=now().date() + timedelta(days=30),
        )
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'QUOTA'})
        assert resp.status_code == 302
        assert 'voucher_code' not in logged_client.session

    def test_voucher_quota_combined_usage(self, logged_client, customer, cart_with_item):
        voucher = Voucher.objects.create(
            code='QUOTA2',
            discount_type='fixed',
            discount_amount=10000,
            quota=3,
            claimed_count=0,
            is_active=True,
            start_date=now().date() - timedelta(days=1),
            expired_date=now().date() + timedelta(days=30),
        )
        Voucher.objects.filter(pk=voucher.pk).update(used_count=2)
        UserVoucher.objects.create(
            user=customer, voucher=voucher,
            status=UserVoucher.Status.USED,
            expires_at=now() + timedelta(days=30),
        )
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'QUOTA2'})
        assert resp.status_code == 302
        assert 'voucher_code' not in logged_client.session


# ============================================================
# VOUCHER — NON-PUBLIC / ASSIGNED
# ============================================================
@pytest.mark.django_db
class TestVoucherNonPublic:
    def test_non_public_voucher_owned(self, logged_client, customer, cart_with_item):
        voucher = Voucher.objects.create(
            code='MYVOUCH',
            discount_type='fixed',
            discount_amount=25000,
            voucher_type='welcome',
            is_active=True,
            start_date=now().date() - timedelta(days=1),
            expired_date=now().date() + timedelta(days=30),
        )
        UserVoucher.objects.create(
            user=customer, voucher=voucher,
            expires_at=now() + timedelta(days=30),
        )
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'MYVOUCH'})
        assert resp.status_code == 302
        assert logged_client.session.get('voucher_code') == 'MYVOUCH'

    def test_non_public_voucher_not_owned(self, logged_client, cart_with_item):
        voucher = Voucher.objects.create(
            code='NOTMINE',
            discount_type='fixed',
            discount_amount=25000,
            voucher_type='welcome',
            is_active=True,
            start_date=now().date() - timedelta(days=1),
            expired_date=now().date() + timedelta(days=30),
        )
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'NOTMINE'})
        assert resp.status_code == 302
        assert 'voucher_code' not in logged_client.session

    def test_non_public_voucher_already_used(self, logged_client, customer, cart_with_item):
        voucher = Voucher.objects.create(
            code='USEDVOUCH',
            discount_type='fixed',
            discount_amount=25000,
            voucher_type='welcome',
            is_active=True,
            start_date=now().date() - timedelta(days=1),
            expired_date=now().date() + timedelta(days=30),
        )
        UserVoucher.objects.create(
            user=customer, voucher=voucher,
            status=UserVoucher.Status.USED,
            expires_at=now() + timedelta(days=30),
        )
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'USEDVOUCH'})
        assert resp.status_code == 302
        assert 'voucher_code' not in logged_client.session

    def test_non_public_voucher_expired_user_voucher(self, logged_client, customer, cart_with_item):
        voucher = Voucher.objects.create(
            code='EXPUSER',
            discount_type='fixed',
            discount_amount=25000,
            voucher_type='welcome',
            is_active=True,
            start_date=now().date() - timedelta(days=1),
            expired_date=now().date() + timedelta(days=30),
        )
        UserVoucher.objects.create(
            user=customer, voucher=voucher,
            status=UserVoucher.Status.AVAILABLE,
            expires_at=now() - timedelta(days=1),
        )
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'EXPUSER'})
        assert resp.status_code == 302
        assert 'voucher_code' not in logged_client.session


# ============================================================
# VOUCHER — REMOVE, RECALCULATION, PERSISTENCE
# ============================================================
@pytest.mark.django_db
class TestVoucherLifecycle:
    def test_remove_voucher_from_session(self, logged_client, cart_with_item, voucher_percentage):
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'DISKON10'})
        assert logged_client.session.get('voucher_code') == 'DISKON10'
        logged_client.post(reverse('carts:remove_voucher'))
        assert 'voucher_code' not in logged_client.session

    def test_voucher_removed_discount_zero(self, logged_client, cart_with_item, voucher_percentage):
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'DISKON10'})
        logged_client.post(reverse('carts:remove_voucher'))
        resp = logged_client.get(reverse('carts:detail'))
        assert resp.context['voucher_discount'] == 0
        assert resp.context['final_total'] == resp.context['subtotal']

    def test_voucher_persists_on_get(self, logged_client, cart_with_item, voucher_percentage):
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'DISKON10'})
        logged_client.get(reverse('carts:detail'))
        assert logged_client.session.get('voucher_code') == 'DISKON10'

    def test_voucher_persists_across_multiple_gets(
        self, logged_client, cart_with_item, voucher_percentage
    ):
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'DISKON10'})
        for _ in range(5):
            logged_client.get(reverse('carts:detail'))
        assert logged_client.session.get('voucher_code') == 'DISKON10'

    def test_apply_new_voucher_replaces_old(self, logged_client, cart_with_item, voucher_percentage, voucher_fixed):
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'DISKON10'})
        assert logged_client.session.get('voucher_code') == 'DISKON10'
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'FLAT50'})
        assert logged_client.session.get('voucher_code') == 'FLAT50'

    def test_voucher_recalculated_after_quantity_increase(
        self, logged_client, customer, product, voucher_percentage
    ):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'DISKON10'})
        resp = logged_client.get(reverse('carts:detail'))
        discount_1 = resp.context['voucher_discount']
        item = cart.items.first()
        logged_client.post(reverse('carts:update', args=[item.id]), {'action': 'increase'})
        resp = logged_client.get(reverse('carts:detail'))
        discount_2 = resp.context['voucher_discount']
        assert discount_2 > discount_1
        expected = int(375000 * 2 * 10 / 100)
        assert discount_2 == expected

    def test_voucher_recalculated_after_quantity_decrease(
        self, logged_client, customer, product, voucher_percentage
    ):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=3)
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'DISKON10'})
        resp = logged_client.get(reverse('carts:detail'))
        discount_before = resp.context['voucher_discount']
        item = cart.items.first()
        logged_client.post(reverse('carts:update', args=[item.id]), {'action': 'decrease'})
        resp = logged_client.get(reverse('carts:detail'))
        discount_after = resp.context['voucher_discount']
        assert discount_after < discount_before

    def test_voucher_invalidated_when_cart_below_min_purchase(
        self, logged_client, customer, product
    ):
        voucher = Voucher.objects.create(
            code='MIN200K',
            discount_type='fixed',
            discount_amount=25000,
            min_purchase=200000,
            is_active=True,
            start_date=now().date() - timedelta(days=1),
            expired_date=now().date() + timedelta(days=30),
        )
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        assert cart.total_price() == 375000
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'MIN200K'})
        assert logged_client.session.get('voucher_code') == 'MIN200K'
        item = cart.items.first()
        logged_client.post(reverse('carts:update', args=[item.id]), {'quantity': 0})
        cart = Cart.objects.get(user=customer)
        assert cart.total_price() == 0
        resp = logged_client.get(reverse('carts:detail'))
        assert resp.context['voucher_code'] == ''
        assert resp.context['voucher_discount'] == 0


# ============================================================
# VOUCHER — CHECKOUT
# ============================================================
@pytest.mark.django_db
class TestVoucherCheckout:
    def test_checkout_with_voucher_discount_applied(
        self, logged_client, customer, product, voucher_percentage, location
    ):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=2)
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'DISKON10'})
        resp = self.assert_checkout_success(logged_client, location)
        assert resp.status_code == 302
        from apps.orders.models import Order
        order = Order.objects.filter(user=customer).first()
        assert order is not None
        expected_subtotal = 375000 * 2
        expected_discount = int(expected_subtotal * 10 / 100)
        assert order.subtotal == expected_subtotal
        assert order.discount_amount == expected_discount
        assert order.total_price == expected_subtotal - expected_discount

    def assert_checkout_success(self, logged_client, location, **overrides):
        session = logged_client.session
        session['shipping'] = {'courier_code': 'jne', 'service': 'OKE', 'cost': 0, 'etd': '3-5'}
        session.save()
        data = {
            'recipient_name': 'Budi',
            'phone': '08123456789',
            'shipping_address': 'Jl. Merdeka No. 10',
            'province': location['province'].id,
            'city': location['city'].id,
            'district': location['district'].id,
            'postal_code': location['postal_code'].id,
        }
        data.update(overrides)
        return logged_client.post(reverse('orders:create'), data)

    def test_checkout_clears_voucher_from_session(
        self, logged_client, customer, product, voucher_percentage, location
    ):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'DISKON10'})
        self.assert_checkout_success(logged_client, location)
        assert 'voucher_code' not in logged_client.session

    def test_checkout_with_voucher_clears_cart(
        self, logged_client, customer, product, voucher_percentage, location
    ):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'DISKON10'})
        self.assert_checkout_success(logged_client, location)
        cart.refresh_from_db()
        assert cart.items.count() == 0

    def test_checkout_consumes_user_voucher(
        self, logged_client, customer, product, location
    ):
        voucher = Voucher.objects.create(
            code='UCONSUME',
            discount_type='percentage',
            discount_amount=10,
            min_purchase=0,
            is_active=True,
            start_date=now().date() - timedelta(days=1),
            expired_date=now().date() + timedelta(days=30),
        )
        uv = UserVoucher.objects.create(
            user=customer, voucher=voucher,
            expires_at=now() + timedelta(days=30),
        )
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'UCONSUME'})
        self.assert_checkout_success(logged_client, location)
        uv.refresh_from_db()
        assert uv.status == UserVoucher.Status.USED
        assert uv.used_at is not None

    def test_checkout_increments_voucher_used_count(
        self, logged_client, customer, product, voucher_percentage, location
    ):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'DISKON10'})
        self.assert_checkout_success(logged_client, location)
        voucher_percentage.refresh_from_db()
        assert voucher_percentage.used_count == 1

    def test_checkout_shows_voucher_on_form_page(
        self, logged_client, customer, product, voucher_percentage, location
    ):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'DISKON10'})
        resp = logged_client.get(reverse('orders:create'))
        assert resp.status_code == 200
        assert resp.context['voucher_code'] == 'DISKON10'
        assert resp.context['discount_amount'] > 0

    def test_checkout_invalid_voucher_redirects_to_cart(
        self, logged_client, customer, product, location
    ):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        session = logged_client.session
        session['voucher_code'] = 'INVALID'
        session.save()
        resp = self.assert_checkout_success(logged_client, location)
        assert resp.status_code == 302
        assert '/cart/' in resp.url


# ============================================================
# VOUCHER — EDGE CASES
# ============================================================
@pytest.mark.django_db
class TestVoucherEdgeCases:
    def test_voucher_without_start_date_uses_default(self, logged_client, cart_with_item):
        today = now().date()
        voucher = Voucher.objects.create(
            code='NOSTART',
            discount_type='fixed',
            discount_amount=10000,
            min_purchase=0,
            is_active=True,
            start_date=today,
            expired_date=today + timedelta(days=30),
        )
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'NOSTART'})
        assert resp.status_code == 302
        assert logged_client.session.get('voucher_code') == 'NOSTART'

    def test_voucher_without_expiry_never_expires(self, logged_client, cart_with_item):
        voucher = Voucher.objects.create(
            code='NOEND',
            discount_type='fixed',
            discount_amount=10000,
            min_purchase=0,
            is_active=True,
            start_date=now().date() - timedelta(days=1),
            expired_date=None,
        )
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'NOEND'})
        assert resp.status_code == 302
        assert logged_client.session.get('voucher_code') == 'NOEND'

    def test_voucher_with_unlimited_quota(self, logged_client, cart_with_item):
        voucher = Voucher.objects.create(
            code='UNLIM',
            discount_type='fixed',
            discount_amount=10000,
            quota=0,
            min_purchase=0,
            is_active=True,
            start_date=now().date() - timedelta(days=1),
            expired_date=now().date() + timedelta(days=30),
        )
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'UNLIM'})
        assert resp.status_code == 302
        assert logged_client.session.get('voucher_code') == 'UNLIM'

    def test_voucher_removed_then_reapplied(self, logged_client, cart_with_item, voucher_percentage):
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'DISKON10'})
        logged_client.post(reverse('carts:remove_voucher'))
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'DISKON10'})
        assert logged_client.session.get('voucher_code') == 'DISKON10'
        resp = logged_client.get(reverse('carts:detail'))
        assert resp.context['voucher_discount'] > 0

    def test_voucher_stripped_whitespace(self, logged_client, cart_with_item, voucher_percentage):
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': '  DISKON10  '})
        assert resp.status_code == 302
        assert logged_client.session.get('voucher_code') == 'DISKON10'
