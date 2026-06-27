import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parfumoray.settings')

import django
django.setup()

import json, hashlib
from datetime import timedelta
from django.utils.timezone import now
from django.test import Client, override_settings
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User
from unittest.mock import patch

from apps.products.models import Product, Category, Brand, FragranceFamily, ProductVariant
from apps.orders.models import Order
from apps.carts.models import Cart, CartItem
from apps.accounts.models import CustomerAddress, Wishlist
from apps.promotions.models import Voucher, UserVoucher
from apps.regions.models import Province, City, District, PostalCode

import pytest

pytestmark = pytest.mark.django_db


# ─────────────────────────────────────────────
# Fixtures: seed data for all UAT scenarios
# ─────────────────────────────────────────────
@pytest.fixture
def seed_data():
    cat = Category.objects.create(name='Eau de Parfum', slug='eau-de-parfum')
    brand = Brand.objects.create(name='Test Brand')
    family = FragranceFamily.objects.create(name='Citrus')
    prod = Product.objects.create(
        name='Morris Noir',
        slug='morris-noir',
        category=cat,
        brand=brand,
        price=375000,
        stock=25,
        is_available=True,
        description='A luxurious woody fragrance',
    )
    prod.fragrance_families.add(family)
    # Also create a second product for browsing
    prod2 = Product.objects.create(
        name='Citrus Morning',
        slug='citrus-morning',
        category=cat,
        brand=brand,
        price=195000,
        stock=50,
        is_available=True,
        description='Fresh citrus scent',
    )
    prod2.fragrance_families.add(family)
    # Variant for the first product
    variant = ProductVariant.objects.create(
        product=prod, size_ml=50, price=375000, stock=25, sku='MN-50'
    )
    # Region data
    prov = Province.objects.create(name='DKI Jakarta')
    city = City.objects.create(name='Jakarta Pusat', province=prov)
    dist = District.objects.create(name='Menteng', city=city)
    pc = PostalCode.objects.create(code='10310', district=dist)
    # Voucher (public)
    voucher = Voucher.objects.create(
        code='DISKON10',
        voucher_type='public',
        discount_type='percentage',
        discount_amount=10,
        min_purchase=100000,
        max_discount=50000,
        is_active=True,
        start_date=now().date() - timedelta(days=1),
        expired_date=now().date() + timedelta(days=30),
        quota=100,
    )
    # WELCOME10 is seeded by data migration 0002_seed_welcome10_voucher.py
    # — already exists in test DB
    return {
        'category': cat,
        'brand': brand,
        'family': family,
        'product': prod,
        'product2': prod2,
        'variant': variant,
        'province': prov,
        'city': city,
        'district': dist,
        'postal_code': pc,
        'voucher': voucher,
    }


class TestUAT:
    """Complete User Acceptance Testing — real customer simulation."""

    def test_full_customer_journey(self, seed_data):
        d = seed_data
        client = Client()
        results = []
        self.results = results

        def record(step, expected, actual, bug=None):
            a = str(actual).strip()
            e = str(expected).strip()
            status = 'PASS' if (a == e or a.startswith(e) or e.startswith(a)) else 'FAIL'
            results.append({
                'step': step,
                'expected': expected,
                'actual': actual,
                'status': status,
                'bug': bug or '',
            })
            print(f'  [{status}] {step}: {actual}')

        # ── Step 1: Register ──────────────────────────
        print('\n=== 1. REGISTER ===')
        resp = client.post(reverse('accounts:register'), {
            'username': 'budi',
            'email': 'budi@example.com',
            'password1': 'Str0ng!Pass123',
            'password2': 'Str0ng!Pass123',
        })
        user = User.objects.filter(username='budi').first()
        expected = '302'
        actual = str(resp.status_code)
        record('Register', expected, actual)

        # Verify user created
        assert user is not None, 'User not created'
        record('User created in DB', 'True', str(user is not None))

        # Verify welcome voucher assigned
        welcome_v = UserVoucher.objects.filter(user=user, voucher__code='WELCOME10').first()
        if welcome_v:
            record('Welcome voucher assigned', 'True', f'True (code={welcome_v.voucher.code})')
        else:
            record('Welcome voucher assigned', 'True', 'False — no WELCOME10 voucher assigned')

        # ── Step 2: Login ──────────────────────────────
        print('\n=== 2. LOGIN ===')
        resp = client.post(reverse('accounts:login'), {
            'username': 'budi',
            'password': 'Str0ng!Pass123',
        }, follow=False)
        expected = '302'
        actual = str(resp.status_code)
        record('Login', expected, actual)
        assert resp.status_code == 302

        # Verify session active
        resp2 = client.get(reverse('accounts:dashboard'))
        record('Dashboard accessible after login', '200', str(resp2.status_code))

        # ── Step 3: Browse Product ──────────────────────
        print('\n=== 3. BROWSE PRODUCT ===')
        resp = client.get(reverse('products:list'))
        record('Product list page', '200', str(resp.status_code))
        assert resp.status_code == 200
        has_products = 'Morris Noir' in resp.content.decode() or d['product'].name in resp.content.decode()
        record('Product list contains products', 'True', str(has_products))

        # Browse by category
        resp = client.get(reverse('products:list'), {'category': 'eau-de-parfum'})
        record('Browse by category filter', '200', str(resp.status_code))
        assert resp.status_code == 200

        # Browse by family
        resp = client.get(reverse('products:by_family', kwargs={'slug': 'citrus'}))
        record('Browse by fragrance family', '200', str(resp.status_code))
        assert resp.status_code == 200

        # Product detail
        resp = client.get(reverse('products:detail', kwargs={'slug': 'morris-noir'}))
        record('Product detail page', '200', str(resp.status_code))
        assert resp.status_code == 200
        has_detail = d['product'].name in resp.content.decode()
        record('Product detail shows name', 'True', str(has_detail))

        # ── Step 4: Search Product ──────────────────────
        print('\n=== 4. SEARCH PRODUCT ===')
        resp = client.get(reverse('products:list'), {'q': 'morris'})
        record('Search by product name', '200', str(resp.status_code))
        assert resp.status_code == 200
        found = d['product'].name.lower() in resp.content.decode().lower()
        record('Search finds matching product', 'True', str(found))

        resp = client.get(reverse('products:list'), {'q': 'woody'})
        record('Search by description keyword', '200', str(resp.status_code))
        assert resp.status_code == 200
        found_desc = 'woody' in resp.content.decode().lower()
        record('Search finds product by description', 'True', str(found_desc))

        resp = client.get(reverse('products:list'), {'q': 'nonexistent_xyz'})
        record('Search with no results', '200', str(resp.status_code))
        no_results = d['product'].name not in resp.content.decode()
        record('No results shown for unmatched query', 'True', str(no_results))

        # ── Step 5: Wishlist ────────────────────────────
        print('\n=== 5. WISHLIST ===')
        resp = client.post(reverse('accounts:wishlist_add', kwargs={'product_id': d['product'].id}))
        record('Add to wishlist', '302', str(resp.status_code))
        assert Wishlist.objects.filter(user=user, product=d['product']).exists()
        record('Wishlist item in DB', 'True', 'True')

        resp = client.get(reverse('accounts:wishlist_list'))
        record('Wishlist page', '200', str(resp.status_code))
        assert resp.status_code == 200
        on_wishlist = d['product'].name in resp.content.decode()
        record('Wishlist shows added product', 'True', str(on_wishlist))

        # Duplicate add should not error
        resp2 = client.post(reverse('accounts:wishlist_add', kwargs={'product_id': d['product'].id}))
        record('Add duplicate to wishlist (idempotent)', '302', str(resp2.status_code))

        # Remove from wishlist
        resp = client.post(reverse('accounts:wishlist_remove', kwargs={'product_id': d['product'].id}))
        record('Remove from wishlist', '302', str(resp.status_code))
        assert not Wishlist.objects.filter(user=user, product=d['product']).exists()
        record('Wishlist item removed from DB', 'True', 'True')

        # Re-add for later steps
        client.post(reverse('accounts:wishlist_add', kwargs={'product_id': d['product'].id}))

        # ── Step 6: Add to Cart ─────────────────────────
        print('\n=== 6. ADD TO CART ===')
        resp = client.post(reverse('carts:add', kwargs={'product_id': d['product'].id}), {
            'variant_id': d['variant'].id,
            'quantity': 2,
        })
        record('Add item to cart', '302', str(resp.status_code))
        assert resp.status_code == 302
        cart = Cart.objects.get(user=user)
        cart_item = CartItem.objects.filter(cart=cart).first()
        record('Cart item created in DB', 'True', str(cart_item is not None))
        assert cart_item is not None
        record(f'Cart item quantity={cart_item.quantity}', '2', str(cart_item.quantity))

        # View cart
        resp = client.get(reverse('carts:detail'))
        record('Cart detail page', '200', str(resp.status_code))
        assert resp.status_code == 200
        on_cart = d['product'].name in resp.content.decode()
        record('Cart shows product', 'True', str(on_cart))

        # Add second product
        resp = client.post(reverse('carts:add', kwargs={'product_id': d['product2'].id}), {
            'quantity': 1,
        })
        record('Add second product to cart', '302', str(resp.status_code))
        assert resp.status_code == 302
        assert CartItem.objects.filter(cart=cart).count() == 2
        record('2 items in cart', '2', str(CartItem.objects.filter(cart=cart).count()))

        # Update cart item quantity
        ci = CartItem.objects.filter(cart=cart, product=d['product2']).first()
        resp = client.post(reverse('carts:update', kwargs={'item_id': ci.id}), {
            'action': 'increase',
        })
        record('Increase cart item quantity', '302', str(resp.status_code))
        ci.refresh_from_db()
        record(f'Quantity after increase', '2', str(ci.quantity))

        # ── Step 7: Apply Voucher ───────────────────────
        print('\n=== 7. APPLY VOUCHER ===')
        resp = client.post(reverse('carts:apply_voucher'), {'code': 'DISKON10'})
        record('Apply voucher to cart', '302', str(resp.status_code))
        assert resp.status_code == 302
        # Check voucher in session
        session = client.session
        has_voucher = session.get('voucher_code') == 'DISKON10'
        record('Voucher code in session', 'True', str(has_voucher))

        # View cart with voucher applied
        resp = client.get(reverse('carts:detail'))
        record('Cart page with voucher applied', '200', str(resp.status_code))
        resp_text = resp.content.decode()
        shows_discount = 'DISKON10' in resp_text or 'diskon' in resp_text.lower() or '10%' in resp_text
        record('Cart shows voucher discount info', 'True', str(shows_discount))

        # Remove voucher
        resp = client.post(reverse('carts:remove_voucher'))
        record('Remove voucher from cart', '302', str(resp.status_code))
        session = client.session
        voucher_removed = session.get('voucher_code') is None
        record('Voucher removed from session', 'True', str(voucher_removed))

        # Re-apply for checkout
        client.post(reverse('carts:apply_voucher'), {'code': 'DISKON10'})

        # ── Step 8: Add Address ─────────────────────────
        print('\n=== 8. ADD ADDRESS ===')
        resp = client.post(reverse('accounts:address_create'), {
            'recipient_name': 'Budi Santoso',
            'phone': '08123456789',
            'address_line': 'Jl. Menteng Raya No. 10, RT 05 RW 02',
            'province': d['province'].id,
            'city': d['city'].id,
            'district': d['district'].id,
            'postal_code': d['postal_code'].id,
            'label': 'Rumah',
        })
        record('Add shipping address', '302', str(resp.status_code))
        assert resp.status_code == 302
        addr = CustomerAddress.objects.filter(user=user).first()
        record('Address created in DB', 'True', str(addr is not None))
        assert addr is not None

        # View address list
        resp = client.get(reverse('accounts:address_list'))
        record('Address list page', '200', str(resp.status_code))
        assert resp.status_code == 200
        has_addr = 'Jl. Menteng Raya' in resp.content.decode()
        record('Address list shows saved address', 'True', str(has_addr))

        # Note: Checkout uses CheckoutForm in orders/forms.py, not CustomerAddress directly.
        # The form takes inline address fields, not a pre-saved address ID.

        # ── Step 9: Checkout ────────────────────────────
        print('\n=== 9. CHECKOUT ===')
        resp = client.post(reverse('orders:create'), {
            'recipient_name': 'Budi Santoso',
            'phone': '08123456789',
            'shipping_address': 'Jl. Menteng Raya No. 10, RT 05 RW 02',
            'province': d['province'].id,
            'city': d['city'].id,
            'district': d['district'].id,
            'postal_code': d['postal_code'].id,
            'notes': 'Tolong dibungkus kado',
        })
        record('Checkout (create order)', '302', str(resp.status_code))
        assert resp.status_code == 302
        assert 'payment' in resp.url.lower() or 'checkout' in resp.url.lower(), \
            f'Expected redirect to payment, got {resp.url}'

        order = Order.objects.filter(user=user).order_by('-id').first()
        record('Order created in DB', 'True', str(order is not None))
        assert order is not None

        record(f'Order status', 'pending_payment', str(order.status))
        record(f'Order number', str(order.order_number), str(order.order_number))
        record(f'Order total price > 0', 'True', str(order.total_price > 0))
        record(f'Voucher applied to order', 'True', str(order.discount_amount > 0))

        order_items = order.items.all()
        record(f'Order items count', '2', str(order_items.count()))
        assert order_items.count() == 2

        # Cart should be cleared after checkout
        cart_items_left = CartItem.objects.filter(cart=cart).count()
        record('Cart cleared after checkout', '0', str(cart_items_left))

        # ── Step 10: Midtrans Payment (mocked) ──────────
        print('\n=== 10. MIDTRANS PAYMENT ===')
        with patch('apps.payments.views.create_transaction') as mock_create:
            mock_create.return_value = {
                'token': 'mock-snap-token-12345',
                'redirect_url': 'https://app.sandbox.midtrans.com/snap/v3/redirection/mock',
            }
            resp = client.get(reverse('payments:checkout', kwargs={'order_id': order.id}))
            record('Payment checkout page', '200', str(resp.status_code))
            assert resp.status_code == 200
            mock_create.assert_called_once()

        # Simulate Midtrans notification webhook (settlement)
        midtrans_order_id = order.midtrans_order_id
        raw_order_id = f'ORDER-{midtrans_order_id}'
        gross_amount = str(int(order.total_price))
        # Build signature_key = hashlib.sha512(order_id + status_code + gross_amount + server_key).hexdigest()
        status_code_str = '200'
        sig_raw = raw_order_id + status_code_str + gross_amount + settings.MIDTRANS_SERVER_KEY
        signature_key = hashlib.sha512(sig_raw.encode()).hexdigest()

        notification_data = {
            'order_id': raw_order_id,
            'transaction_status': 'settlement',
            'transaction_id': 'TRX-MID-123456789',
            'payment_type': 'bank_transfer',
            'fraud_status': 'accept',
            'transaction_time': now().strftime('%Y-%m-%d %H:%M:%S'),
            'status_code': status_code_str,
            'gross_amount': gross_amount,
            'signature_key': signature_key,
        }

        resp = client.post(
            reverse('payments:notification'),
            json.dumps(notification_data),
            content_type='application/json',
        )
        record('Payment notification webhook', '200 OK', str(resp.status_code))
        assert resp.status_code == 200

        # Refresh order and check status
        order.refresh_from_db()
        record(f'Order status after settlement', 'paid', str(order.status))
        assert order.status == 'paid' or order.status == 'processing', \
            f'Expected order.status to be "paid" or "processing", got "{order.status}"'

        # Check payment record
        payment = getattr(order, 'payment', None)
        record('Payment record created', 'True', str(payment is not None))
        if payment:
            record(f'Payment status', 'success', str(payment.status))
            record(f'Payment transaction_id', 'TRX-MID-123456789', str(payment.transaction_id))

        # Check stock decremented
        d['variant'].refresh_from_db()
        d['product'].refresh_from_db()
        record(f'Product.stock decremented', '23 (from 25)', str(d['product'].stock))
        record(f'ProductVariant.stock decremented', '23 (from 25) [BUG: still 25]', str(d['variant'].stock))
        # Product.stock IS decremented (the code does this correctly)
        assert d['product'].stock == 23, f'Expected Product.stock=23, got {d["product"].stock}'
        # BUG: ProductVariant.stock is NOT decremented — the payment handler only updates
        # Product.stock via Product.objects.filter(id=item.product_id).update(stock=F('stock') - item.quantity).
        # Since OrderItem has no variant FK, variant stock is never reduced.
        # This is a known bug — documented in UAT report.

        # ── Step 11: View Order ─────────────────────────
        print('\n=== 11. VIEW ORDER ===')
        resp = client.get(reverse('orders:list'))
        record('Order list page', '200', str(resp.status_code))
        assert resp.status_code == 200
        has_order = order.order_number in resp.content.decode()
        record('Order list shows created order', 'True', str(has_order))

        resp = client.get(reverse('orders:detail', kwargs={'order_id': order.id}))
        record('Order detail page', '200', str(resp.status_code))
        assert resp.status_code == 200
        has_status = 'paid' in resp.content.decode().lower()
        record('Order detail shows status', 'True', str(has_status))

        resp = client.get(reverse('orders:track', kwargs={'order_id': order.id}))
        record('Order tracking page', '200', str(resp.status_code))
        assert resp.status_code == 200

        # ── Step 12: Logout ─────────────────────────────
        print('\n=== 12. LOGOUT ===')
        resp = client.get(reverse('accounts:logout'))
        record('Logout', '302', str(resp.status_code))
        assert resp.status_code == 302

        # Verify session is cleared
        resp = client.get(reverse('accounts:dashboard'))
        record('Dashboard inaccessible after logout', '302', str(resp.status_code))
        assert resp.status_code == 302  # Redirected to login

        # Verify wishlist page requires login
        resp = client.get(reverse('accounts:wishlist_list'))
        record('Wishlist inaccessible after logout', '302', str(resp.status_code))

        # ── Summary ─────────────────────────────────────
        print('\n' + '=' * 70)
        print('UAT RESULTS SUMMARY')
        print('=' * 70)
        pass_count = sum(1 for r in results if r['status'] == 'PASS')
        fail_count = sum(1 for r in results if r['status'] == 'FAIL')
        print(f'Total: {len(results)} | PASS: {pass_count} | FAIL: {fail_count}')
        for r in results:
            icon = 'PASS' if r['status'] == 'PASS' else 'FAIL'
            bug = f' -- BUG: {r["bug"]}' if r['bug'] else ''
            print(f'  [{icon}] {r["step"]}: {r["actual"]}{bug}')

        # If any failures, print details
        failures = [r for r in results if r['status'] == 'FAIL']
        if failures:
            print('\n--- FAILURES ---')
            for f in failures:
                print(f'  [{f["step"]}] expected="{f["expected"]}" actual="{f["actual"]}"')
            pytest.fail(f'{len(failures)} UAT step(s) failed')

        return results
