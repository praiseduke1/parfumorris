import os, time, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parfumoray.settings')

import django
django.setup()

import pytest
from django.test import Client, TestCase, override_settings
from django.db import connection
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache

from apps.products.models import Product, Category, Brand
from apps.orders.models import Order
from apps.carts.models import Cart, CartItem
from apps.accounts.models import CustomerAddress


pytestmark = pytest.mark.django_db


def count_queries(client_func, *args, **kwargs):
    from django.db import connection
    q_start = len(connection.queries)
    response = client_func(*args, **kwargs)
    q_end = len(connection.queries)
    return response, q_end - q_start


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield


@pytest.fixture
def admin_user(django_user_model):
    u = django_user_model.objects.create_superuser(
        username='perfadmin', email='admin@test.com', password='testpass123'
    )
    return u


@pytest.fixture
def regular_user(django_user_model):
    u = django_user_model.objects.create_user(
        username='perfcustomer', email='cust@test.com', password='testpass123'
    )
    return u


@pytest.fixture
def seeded_data():
    from apps.products.models import Category, Brand, FragranceFamily, FragranceNote, Product, ProductVariant
    cat = Category.objects.create(name='Test Category')
    brand = Brand.objects.create(name='Test Brand')
    family = FragranceFamily.objects.create(name='Test Family')
    note = FragranceNote.objects.create(name='Test Note', note_type='TOP')
    for i in range(12):
        p = Product.objects.create(
            name=f'Test Product {i}',
            slug=f'test-product-{i}',
            category=cat,
            brand=brand,
            price=150000,
            stock=10,
            is_available=True,
        )
        p.fragrance_families.add(family)
        p.fragrance_notes.add(note)
        ProductVariant.objects.create(
            product=p, size_ml=50, price=150000, stock=10,
            sku=f'SKU-PERF-{i}'
        )
    return cat, brand, family, note


class TestPagePerformance:
    """Measure response time and DB query count for every key page."""

    def test_home_page(self, client, seeded_data, benchmark):
        url = reverse('products:home')
        q_start = len(connection.queries)

        def _load():
            return client.get(url)

        resp = benchmark(_load)
        q_end = len(connection.queries)
        queries = q_end - q_start

        assert resp.status_code == 200
        benchmark.extra_info['queries'] = queries
        benchmark.extra_info['page'] = 'Home'

    def test_product_list_page(self, client, seeded_data, benchmark):
        url = reverse('products:list')
        q_start = len(connection.queries)

        def _load():
            return client.get(url)

        resp = benchmark(_load)
        q_end = len(connection.queries)
        queries = q_end - q_start

        assert resp.status_code == 200
        benchmark.extra_info['queries'] = queries
        benchmark.extra_info['page'] = 'Product List'

    def test_product_list_with_filter(self, client, seeded_data, benchmark):
        url = reverse('products:list') + '?gender=men'
        q_start = len(connection.queries)

        def _load():
            return client.get(url)

        resp = benchmark(_load)
        q_end = len(connection.queries)
        queries = q_end - q_start

        assert resp.status_code == 200
        benchmark.extra_info['queries'] = queries
        benchmark.extra_info['page'] = 'Product List (filtered)'

    def test_product_detail(self, client, seeded_data, benchmark):
        p = Product.objects.filter(is_available=True).first()
        url = reverse('products:detail', args=[p.slug])
        q_start = len(connection.queries)

        def _load():
            return client.get(url)

        resp = benchmark(_load)
        q_end = len(connection.queries)
        queries = q_end - q_start

        assert resp.status_code == 200
        benchmark.extra_info['queries'] = queries
        benchmark.extra_info['page'] = 'Product Detail'

    def test_cart_page_empty(self, client, regular_user, benchmark):
        client.force_login(regular_user)
        url = reverse('carts:detail')
        q_start = len(connection.queries)

        def _load():
            return client.get(url)

        resp = benchmark(_load)
        q_end = len(connection.queries)
        queries = q_end - q_start

        assert resp.status_code == 200
        benchmark.extra_info['queries'] = queries
        benchmark.extra_info['page'] = 'Cart (empty)'

    def test_cart_page_with_items(self, client, regular_user, seeded_data, benchmark):
        client.force_login(regular_user)
        cart, _ = Cart.objects.get_or_create(user=regular_user)
        products = list(Product.objects.filter(is_available=True)[:3])
        for p in products:
            CartItem.objects.create(cart=cart, product=p, quantity=2)
        url = reverse('carts:detail')
        q_start = len(connection.queries)

        def _load():
            return client.get(url)

        resp = benchmark(_load)
        q_end = len(connection.queries)
        queries = q_end - q_start

        assert resp.status_code == 200
        benchmark.extra_info['queries'] = queries
        benchmark.extra_info['page'] = 'Cart (3 items)'

    def test_checkout_page_get(self, client, regular_user, seeded_data, benchmark):
        client.force_login(regular_user)
        cart, _ = Cart.objects.get_or_create(user=regular_user)
        p = Product.objects.filter(is_available=True).first()
        CartItem.objects.create(cart=cart, product=p, quantity=1)
        CustomerAddress.objects.create(
            user=regular_user,
            recipient_name='Test',
            phone='08123456789',
            address_line='Jl. Test 123',
            is_default=True,
        )
        url = reverse('orders:create')
        q_start = len(connection.queries)

        def _load():
            return client.get(url)

        resp = benchmark(_load)
        q_end = len(connection.queries)
        queries = q_end - q_start

        assert resp.status_code == 200
        benchmark.extra_info['queries'] = queries
        benchmark.extra_info['page'] = 'Checkout'

    def test_dashboard_page(self, client, regular_user, seeded_data, benchmark):
        client.force_login(regular_user)
        url = reverse('accounts:dashboard')
        q_start = len(connection.queries)

        def _load():
            return client.get(url)

        resp = benchmark(_load)
        q_end = len(connection.queries)
        queries = q_end - q_start

        assert resp.status_code == 200
        benchmark.extra_info['queries'] = queries
        benchmark.extra_info['page'] = 'Customer Dashboard'

    def test_admin_login_page(self, client, benchmark):
        url = reverse('admin:login')
        q_start = len(connection.queries)

        def _load():
            return client.get(url)

        resp = benchmark(_load)
        q_end = len(connection.queries)
        queries = q_end - q_start

        assert resp.status_code == 200
        benchmark.extra_info['queries'] = queries
        benchmark.extra_info['page'] = 'Admin Login'

    def test_admin_index(self, client, admin_user, benchmark):
        client.login(username='perfadmin', password='testpass123')
        client.cookies['admin_sessionid'] = client.cookies['sessionid'].value
        url = reverse('admin:index')
        q_start = len(connection.queries)

        def _load():
            return client.get(url)

        resp = benchmark(_load)
        q_end = len(connection.queries)
        queries = q_end - q_start

        assert resp.status_code == 200
        benchmark.extra_info['queries'] = queries
        benchmark.extra_info['page'] = 'Admin Index'

    def test_admin_dashboard_analytics(self, client, admin_user, benchmark):
        client.login(username='perfadmin', password='testpass123')
        client.cookies['admin_sessionid'] = client.cookies['sessionid'].value
        url = reverse('admin_dashboard')
        q_start = len(connection.queries)

        def _load():
            return client.get(url)

        resp = benchmark(_load)
        q_end = len(connection.queries)
        queries = q_end - q_start

        assert resp.status_code == 200
        benchmark.extra_info['queries'] = queries
        benchmark.extra_info['page'] = 'Admin Dashboard Analytics'

    def test_login_page(self, client, benchmark):
        url = reverse('accounts:login')
        q_start = len(connection.queries)

        def _load():
            return client.get(url)

        resp = benchmark(_load)
        q_end = len(connection.queries)
        queries = q_end - q_start

        assert resp.status_code == 200
        benchmark.extra_info['queries'] = queries
        benchmark.extra_info['page'] = 'Login'

    def test_register_page(self, client, benchmark):
        url = reverse('accounts:register')
        q_start = len(connection.queries)

        def _load():
            return client.get(url)

        resp = benchmark(_load)
        q_end = len(connection.queries)
        queries = q_end - q_start

        assert resp.status_code == 200
        benchmark.extra_info['queries'] = queries
        benchmark.extra_info['page'] = 'Register'

    def test_fragrance_guide(self, client, benchmark):
        url = reverse('products:fragrance_guide')
        q_start = len(connection.queries)

        def _load():
            return client.get(url)

        resp = benchmark(_load)
        q_end = len(connection.queries)
        queries = q_end - q_start

        assert resp.status_code == 200
        benchmark.extra_info['queries'] = queries
        benchmark.extra_info['page'] = 'Fragrance Guide'

    def test_about_page(self, client, benchmark):
        url = reverse('products:about')
        q_start = len(connection.queries)

        def _load():
            return client.get(url)

        resp = benchmark(_load)
        q_end = len(connection.queries)
        queries = q_end - q_start

        assert resp.status_code == 200
        benchmark.extra_info['queries'] = queries
        benchmark.extra_info['page'] = 'About'


@pytest.mark.benchmark(min_rounds=5, warmup=True)
class TestStaticAssetsPerformance:
    """Measure static asset serving performance."""

    def test_static_css(self, client, benchmark):
        url = '/static/css/output.css'
        resp = benchmark(client.get, url)
        assert resp.status_code in (200, 404)

    def test_static_js(self, client, benchmark):
        url = '/static/js/main.js'
        resp = benchmark(client.get, url)
        assert resp.status_code in (200, 404)

    def test_favicon(self, client, benchmark):
        url = '/static/favicon.svg'
        resp = benchmark(client.get, url)
        assert resp.status_code in (200, 404)
