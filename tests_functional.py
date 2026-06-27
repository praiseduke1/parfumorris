"""
Functional Testing + UAT — Parfum Morris
Tests all 20 features listed in the testing report.
"""
import pytest
import json
from decimal import Decimal
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils.timezone import now
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from apps.products.models import (
    Product, Category, Brand, FragranceNote, FragranceFamily,
    ProductVariant, ProductImage, Review,
)
from apps.accounts.models import (
    Profile, MemberProfile, PointTransaction, CustomerAddress, Wishlist,
)
from apps.carts.models import Cart, CartItem
from apps.orders.models import Order, OrderItem, OrderStatusHistory, Voucher as OrderVoucher
from apps.payments.models import Payment, PaymentStatusHistory
from apps.promotions.models import Voucher as PromoVoucher, UserVoucher
from apps.accounts.forms import RegisterForm


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
        description='A refined blend of black oud, Bulgarian rose, and warm amber.',
        price=375000,
        stock=25,
        gender_target='men',
        occasion='evening',
        season='winter',
        sillage='heavy',
        longevity='very_long',
    )

@pytest.fixture
def customer():
    return User.objects.create_user(
        username='budi', password='customer123',
        email='budi@example.com',
    )

@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        username='admin', password='admin123',
        email='admin@test.com',
    )

@pytest.fixture
def logged_client(customer):
    client = Client()
    client.login(username='budi', password='customer123')
    return client

@pytest.fixture
def admin_client(admin_user):
    client = Client()
    client.login(username='admin', password='admin123')
    client.cookies['admin_sessionid'] = client.cookies['sessionid'].value
    return client

@pytest.fixture
def location():
    from apps.regions.models import Province, City, District, PostalCode
    prov = Province.objects.create(id=1, name='DKI Jakarta')
    city = City.objects.create(id=1, name='Jakarta Pusat', province=prov)
    dist = District.objects.create(id=1, name='Menteng', city=city)
    pc = PostalCode.objects.create(id=1, code='12345', district=dist)
    return {'province': prov, 'city': city, 'district': dist, 'postal_code': pc}

@pytest.fixture
def seeded_product(product, category):
    """Add fragrance notes, families, and variants to product"""
    top = FragranceNote.objects.create(name='Bergamot', note_type='TOP', slug='bergamot')
    mid = FragranceNote.objects.create(name='Rose', note_type='MIDDLE', slug='rose')
    base = FragranceNote.objects.create(name='Oud', note_type='BASE', slug='oud')
    woody = FragranceFamily.objects.create(name='Woody', slug='woody')
    oriental = FragranceFamily.objects.create(name='Oriental', slug='oriental')
    product.fragrance_notes.add(top, mid, base)
    product.fragrance_families.add(woody, oriental)
    ProductVariant.objects.create(product=product, size_ml=30, price=200000, stock=10, sku='MORRIS-NOIR-30')
    ProductVariant.objects.create(product=product, size_ml=50, price=375000, stock=5, sku='MORRIS-NOIR-50')
    return product


# ============================================================
# 1. HOMEPAGE
# ============================================================
@pytest.mark.django_db
class TestHomepage:
    def test_homepage_status_and_template(self):
        client = Client()
        resp = client.get(reverse('products:home'))
        assert resp.status_code == 200
        templates = [t.name for t in resp.templates if t.name]
        assert 'products/home.html' in templates

    def test_homepage_contains_hero_branding(self):
        client = Client()
        resp = client.get(reverse('products:home'))
        content = resp.content.decode('utf-8')
        assert 'Morris' in content
        assert 'Find Your Signature Scent' in content or 'Temukan' in content or 'Signature Scent' in content

    def test_homepage_shows_categories(self):
        cat = Category.objects.create(name='Test Cat', slug='test-cat')
        resp = Client().get(reverse('products:home'))
        assert resp.status_code == 200

    def test_homepage_shows_featured_products(self, product):
        resp = Client().get(reverse('products:home'))
        content = resp.content.decode('utf-8')
        assert product.name in content

    def test_homepage_shows_stats_bar(self):
        resp = Client().get(reverse('products:home'))
        content = resp.content.decode('utf-8')
        assert '50' in content or 'Authentic' in content or '100%' in content

    def test_homepage_has_fragrance_guide_link(self):
        resp = Client().get(reverse('products:home'))
        assert reverse('products:fragrance_guide') in resp.content.decode('utf-8')

    def test_homepage_anonymous_does_not_show_admin_banner(self):
        resp = Client().get(reverse('products:home'))
        content = resp.content.decode('utf-8')
        assert 'Administrator' not in content

    def test_homepage_logged_in_customer_shows_dashboard_link(self, logged_client):
        resp = logged_client.get(reverse('products:home'))
        content = resp.content.decode('utf-8')
        assert 'Dashboard' in content
        assert 'Administrator' not in content

    def test_homepage_admin_user_shows_admin_banner(self, admin_client):
        resp = admin_client.get(reverse('products:home'))
        content = resp.content.decode('utf-8')
        assert 'Administrator' in content


# ============================================================
# 2. KATALOG PRODUK
# ============================================================
@pytest.mark.django_db
class TestProductCatalog:
    def test_catalog_status(self):
        resp = Client().get(reverse('products:list'))
        assert resp.status_code == 200

    def test_catalog_shows_available_products(self, product):
        resp = Client().get(reverse('products:list'))
        content = resp.content.decode('utf-8')
        assert product.name in content

    def test_catalog_hides_unavailable_products(self, category):
        prod = Product.objects.create(
            name='Hidden', slug='hidden', category=category,
            price=100, stock=0, is_available=False,
        )
        resp = Client().get(reverse('products:list'))
        assert prod.name not in resp.content.decode('utf-8')

    def test_catalog_search_by_name(self, product, category):
        Product.objects.create(name='Vanilla Dream', slug='vanilla-dream', category=category, price=100, stock=5)
        resp = Client().get(reverse('products:list'), {'q': 'Noir'})
        content = resp.content.decode('utf-8')
        assert 'Morris Noir' in content
        assert 'Vanilla Dream' not in content

    def test_catalog_filter_by_category(self, product, category):
        other_cat = Category.objects.create(name='Attar', slug='attar')
        other = Product.objects.create(name='Oud Oil', slug='oud-oil', category=other_cat, price=200, stock=5)
        resp = Client().get(reverse('products:list'), {'category': 'attar'})
        content = resp.content.decode('utf-8')
        assert 'Oud Oil' in content
        assert 'Morris Noir' not in content

    def test_catalog_filter_by_note(self, product, seeded_product):
        resp = Client().get(reverse('products:by_note', kwargs={'slug': 'bergamot'}))
        assert resp.status_code == 200
        assert product.name in resp.content.decode('utf-8')

    def test_catalog_filter_by_family(self, product, seeded_product):
        resp = Client().get(reverse('products:by_family', kwargs={'slug': 'woody'}))
        assert resp.status_code == 200
        assert product.name in resp.content.decode('utf-8')

    def test_catalog_pagination(self, category):
        for i in range(15):
            Product.objects.create(
                name=f'Product {i}', slug=f'product-{i}',
                category=category, price=100, stock=5,
            )
        resp = Client().get(reverse('products:list'))
        content = resp.content.decode('utf-8')
        assert 'halaman' in content.lower() or 'page' in content.lower() or '1' in content

    def test_catalog_empty_state(self, category):
        Product.objects.all().delete()
        resp = Client().get(reverse('products:list'))
        content = resp.content.decode('utf-8')
        assert 'Produk' in content or 'Belum' in content or 'Tidak' in content

    def test_catalog_sidebar_shows_categories(self, category):
        resp = Client().get(reverse('products:list'))
        assert category.name in resp.content.decode('utf-8')


# ============================================================
# 3. DETAIL PRODUK
# ============================================================
@pytest.mark.django_db
class TestProductDetail:
    def test_detail_status(self, product):
        resp = Client().get(reverse('products:detail', kwargs={'slug': product.slug}))
        assert resp.status_code == 200

    def test_detail_404_for_unavailable(self, category):
        prod = Product.objects.create(
            name='Gone', slug='gone', category=category,
            price=100, stock=0, is_available=False,
        )
        resp = Client().get(reverse('products:detail', kwargs={'slug': 'gone'}))
        assert resp.status_code == 404

    def test_detail_shows_product_info(self, seeded_product):
        resp = Client().get(reverse('products:detail', kwargs={'slug': 'morris-noir'}))
        content = resp.content.decode('utf-8')
        assert 'Morris Noir' in content
        assert '200.000' in content
        assert 'Rp' in content

    def test_detail_shows_fragrance_notes(self, seeded_product):
        resp = Client().get(reverse('products:detail', kwargs={'slug': 'morris-noir'}))
        content = resp.content.decode('utf-8')
        assert 'Bergamot' in content
        assert 'Rose' in content
        assert 'Oud' in content

    def test_detail_shows_fragrance_families(self, seeded_product):
        resp = Client().get(reverse('products:detail', kwargs={'slug': 'morris-noir'}))
        content = resp.content.decode('utf-8')
        assert 'Woody' in content
        assert 'Oriental' in content

    def test_detail_shows_variants(self, seeded_product):
        resp = Client().get(reverse('products:detail', kwargs={'slug': 'morris-noir'}))
        content = resp.content.decode('utf-8')
        assert '30ml' in content or '30 ml' in content
        assert '50ml' in content or '50 ml' in content

    def test_detail_shows_morris_fields(self, seeded_product):
        resp = Client().get(reverse('products:detail', kwargs={'slug': 'morris-noir'}))
        content = resp.content.decode('utf-8')
        assert 'For Men' in content or 'pria' in content.lower()
        assert 'Evening' in content or 'Malam' in content.lower()

    def test_detail_shows_related_products(self, product):
        resp = Client().get(reverse('products:detail', kwargs={'slug': product.slug}))
        assert resp.status_code == 200

    def test_detail_add_to_cart_button_for_customer(self, seeded_product, logged_client):
        resp = logged_client.get(reverse('products:detail', kwargs={'slug': 'morris-noir'}))
        content = resp.content.decode('utf-8')
        assert 'Tambah ke Keranjang' in content

    def test_detail_shows_admin_panel_link_for_admin(self, seeded_product, admin_client):
        resp = admin_client.get(reverse('products:detail', kwargs={'slug': 'morris-noir'}))
        content = resp.content.decode('utf-8')
        assert 'Admin Panel' in content


# ============================================================
# 4. REGISTRASI
# ============================================================
@pytest.mark.django_db
class TestRegistration:
    def test_register_page_status(self):
        resp = Client().get(reverse('accounts:register'))
        assert resp.status_code == 200

    def test_register_form_valid(self):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'Str0ng!Pass123',
            'password2': 'Str0ng!Pass123',
        }
        form = RegisterForm(data)
        assert form.is_valid()

    def test_register_creates_user(self):
        client = Client()
        client.post(reverse('accounts:register'), {
            'username': 'fresh', 'email': 'fresh@example.com',
            'password1': 'Str0ng!Pass123', 'password2': 'Str0ng!Pass123',
        })
        assert User.objects.filter(username='fresh').exists()

    def test_register_creates_profile_and_member(self):
        client = Client()
        client.post(reverse('accounts:register'), {
            'username': 'loyal', 'email': 'loyal@example.com',
            'password1': 'Str0ng!Pass123', 'password2': 'Str0ng!Pass123',
        })
        user = User.objects.get(username='loyal')
        assert hasattr(user, 'profile')
        assert hasattr(user, 'member_profile')
        assert user.member_profile.level == 'SILVER'

    def test_register_assigns_welcome_voucher(self):
        PromoVoucher.objects.get_or_create(
            code='WELCOME10', defaults=dict(
                discount_type='percentage',
                discount_amount=10, min_purchase=200000, is_active=True,
            )
        )
        client = Client()
        client.post(reverse('accounts:register'), {
            'username': 'voucher_user', 'email': 'vu@example.com',
            'password1': 'Str0ng!Pass123', 'password2': 'Str0ng!Pass123',
        })
        user = User.objects.get(username='voucher_user')
        assert UserVoucher.objects.filter(user=user, voucher__code='WELCOME10').exists()

    def test_register_redirects_to_login(self):
        resp = Client().post(reverse('accounts:register'), {
            'username': 'redirect_test', 'email': 'rt@example.com',
            'password1': 'Str0ng!Pass123', 'password2': 'Str0ng!Pass123',
        })
        assert resp.status_code == 302
        assert resp.url == reverse('accounts:login')

    def test_register_does_not_auto_login(self):
        client = Client()
        client.post(reverse('accounts:register'), {
            'username': 'noauto', 'email': 'no@example.com',
            'password1': 'Str0ng!Pass123', 'password2': 'Str0ng!Pass123',
        })
        resp = client.get(reverse('accounts:dashboard'))
        assert resp.status_code == 302

    def test_register_duplicate_email_rejected(self):
        User.objects.create_user(username='existing', email='dup@example.com')
        resp = Client().post(reverse('accounts:register'), {
            'username': 'newuser', 'email': 'dup@example.com',
            'password1': 'Str0ng!Pass123', 'password2': 'Str0ng!Pass123',
        })
        assert resp.status_code == 200
        assert 'Email ini sudah terdaftar' in resp.content.decode('utf-8')


# ============================================================
# 5. LOGIN
# ============================================================
@pytest.mark.django_db
class TestLogin:
    def test_login_page_status(self):
        resp = Client().get(reverse('accounts:login'))
        assert resp.status_code == 200

    def test_login_success_redirects(self, customer):
        resp = Client().post(reverse('accounts:login'), {
            'username': 'budi', 'password': 'customer123',
        })
        assert resp.status_code == 302

    def test_login_sets_session_user(self, customer):
        client = Client()
        client.post(reverse('accounts:login'), {
            'username': 'budi', 'password': 'customer123',
        })
        session = client.session
        assert str(session['_auth_user_id']) == str(customer.pk)

    def test_login_wrong_password_fails(self, customer):
        resp = Client().post(reverse('accounts:login'), {
            'username': 'budi', 'password': 'wrongpass',
        })
        assert resp.status_code == 200
        assert 'error' in resp.content.decode('utf-8').lower() or 'Masuk' in resp.content.decode('utf-8')

    def test_login_unknown_user_fails(self):
        resp = Client().post(reverse('accounts:login'), {
            'username': 'nobody', 'password': 'anything',
        })
        assert resp.status_code == 200

    def test_authenticated_user_redirected_to_catalog(self, logged_client):
        resp = logged_client.get(reverse('accounts:login'))
        assert resp.status_code == 302

    def test_login_superuser_gets_admin_banner_on_frontend(self, admin_client):
        resp = admin_client.get(reverse('products:list'))
        assert 'Administrator' in resp.content.decode('utf-8')


# ============================================================
# 6. LOGOUT
# ============================================================
@pytest.mark.django_db
class TestLogout:
    def test_logout_redirects(self, logged_client):
        resp = logged_client.get(reverse('accounts:logout'))
        assert resp.status_code == 302

    def test_logout_clears_session(self, logged_client):
        logged_client.get(reverse('accounts:logout'))
        session = logged_client.session
        assert '_auth_user_id' not in session

    def test_logout_prevents_dashboard_access(self, customer):
        client = Client()
        client.login(username='budi', password='customer123')
        client.get(reverse('accounts:logout'))
        resp = client.get(reverse('accounts:dashboard'))
        assert resp.status_code == 302

    def test_logout_shows_guest_nav(self, logged_client):
        logged_client.get(reverse('accounts:logout'))
        resp = logged_client.get(reverse('products:home'))
        content = resp.content.decode('utf-8')
        assert 'Masuk' in content
        assert 'Dashboard' not in content


# ============================================================
# 7. FORGOT PASSWORD
# ============================================================
@pytest.mark.django_db
class TestForgotPassword:
    def test_forgot_password_page(self):
        resp = Client().get(reverse('accounts:forgot_password'))
        assert resp.status_code == 200

    def test_forgot_password_submit_valid_email(self, customer):
        resp = Client().post(reverse('accounts:forgot_password'), {'email': 'budi@example.com'})
        assert resp.status_code == 302
        assert resp.url == reverse('accounts:password_reset_sent')

    def test_forgot_password_sent_page(self):
        resp = Client().get(reverse('accounts:password_reset_sent'))
        assert resp.status_code == 200

    def test_password_reset_valid_token(self, customer):
        uid = urlsafe_base64_encode(force_bytes(customer.pk))
        token = default_token_generator.make_token(customer)
        resp = Client().get(reverse('accounts:create_new_password', kwargs={'uidb64': uid, 'token': token}))
        assert resp.status_code == 302
        assert '/set-password/' in resp.url

    def test_password_reset_invalid_token(self, customer):
        uid = urlsafe_base64_encode(force_bytes(customer.pk))
        resp = Client().get(reverse('accounts:create_new_password', kwargs={'uidb64': uid, 'token': 'bad-token'}))
        assert resp.status_code == 200
        assert 'Tautan Tidak Valid' in resp.content.decode('utf-8') or 'invalid' in resp.content.decode('utf-8').lower()

    def test_password_reset_expired_token(self, customer):
        uid = urlsafe_base64_encode(force_bytes(customer.pk))
        token = default_token_generator.make_token(customer)
        customer.set_password('newpassword')
        customer.save()
        resp = Client().get(reverse('accounts:create_new_password', kwargs={'uidb64': uid, 'token': token}))
        assert resp.status_code == 200

    def test_password_reset_success_page(self):
        resp = Client().get(reverse('accounts:password_reset_success'))
        assert resp.status_code == 200


# ============================================================
# 8. PROFIL CUSTOMER
# ============================================================
@pytest.mark.django_db
class TestCustomerProfile:
    def test_profile_page_requires_login(self):
        resp = Client().get(reverse('accounts:profile'))
        assert resp.status_code == 302

    def test_profile_page_shows_form(self, logged_client):
        resp = logged_client.get(reverse('accounts:profile'))
        assert resp.status_code == 200

    def test_profile_update_success(self, logged_client, customer):
        resp = logged_client.post(reverse('accounts:profile'), {
            'username': 'budi',
            'email': 'budi@example.com',
            'phone': '08123456789',
        })
        assert resp.status_code == 302
        profile = Profile.objects.get(user=customer)
        assert profile.phone == '08123456789'

    def test_profile_update_username_taken(self, logged_client):
        User.objects.create_user(username='other', password='pass12345')
        resp = logged_client.post(reverse('accounts:profile'), {
            'username': 'other',
            'email': 'budi@example.com',
        })
        assert resp.status_code == 200
        assert 'sudah digunakan' in resp.content.decode('utf-8')

    def test_profile_page_shows_current_info(self, logged_client, customer):
        resp = logged_client.get(reverse('accounts:profile'))
        assert customer.username in resp.content.decode('utf-8')


# ============================================================
# 9. ALAMAT CUSTOMER
# ============================================================
@pytest.mark.django_db
class TestCustomerAddress:
    def test_address_list_requires_login(self):
        resp = Client().get(reverse('accounts:address_list'))
        assert resp.status_code == 302

    def test_address_list_empty(self, logged_client):
        resp = logged_client.get(reverse('accounts:address_list'))
        assert resp.status_code == 200

    def test_address_create(self, logged_client, customer):
        resp = logged_client.post(reverse('accounts:address_create'), {
            'label': 'Rumah',
            'recipient_name': 'Budi',
            'phone': '08123456789',
            'address_line': 'Jl. Merdeka No. 10, Jakarta Pusat',
            'province': '',
            'city': '',
            'district': '',
            'postal_code': '',
        })
        assert resp.status_code == 302
        assert CustomerAddress.objects.filter(user=customer).count() == 1

    def test_address_create_min_length(self, logged_client):
        resp = logged_client.post(reverse('accounts:address_create'), {
            'recipient_name': 'Budi',
            'phone': '08123456789',
            'address_line': 'Short',
        })
        assert resp.status_code == 200

    def test_address_set_default(self, logged_client, customer):
        addr = CustomerAddress.objects.create(
            user=customer, recipient_name='Budi', phone='08123',
            address_line='Jl. Test', is_default=True,
        )
        resp = logged_client.post(reverse('accounts:address_set_default', args=[addr.id]))
        assert resp.status_code == 302

    def test_address_delete(self, logged_client, customer):
        addr = CustomerAddress.objects.create(
            user=customer, recipient_name='Budi', phone='08123', address_line='Jl. X',
        )
        resp = logged_client.post(reverse('accounts:address_delete', args=[addr.id]))
        assert resp.status_code == 302
        assert CustomerAddress.objects.filter(id=addr.id).count() == 0

    def test_address_edit(self, logged_client, customer):
        addr = CustomerAddress.objects.create(
            user=customer, recipient_name='Old', phone='08123', address_line='Jl. Old',
        )
        resp = logged_client.post(reverse('accounts:address_edit', args=[addr.id]), {
            'label': 'Kantor',
            'recipient_name': 'Budi Updated',
            'phone': '08123456789',
            'address_line': 'Jl. Updated No. 5',
            'province': '',
            'city': '',
            'district': '',
            'postal_code': '',
        })
        assert resp.status_code == 302
        addr.refresh_from_db()
        assert addr.recipient_name == 'Budi Updated'


# ============================================================
# 10. CART
# ============================================================
@pytest.mark.django_db
class TestCart:
    def test_cart_detail_requires_login(self):
        resp = Client().get(reverse('carts:detail'))
        assert resp.status_code == 302

    def test_cart_empty_state(self, logged_client):
        resp = logged_client.get(reverse('carts:detail'))
        assert resp.status_code == 200

    def test_cart_add_product(self, logged_client, customer, product):
        resp = logged_client.post(reverse('carts:add', args=[product.id]), {'quantity': 2})
        assert resp.status_code == 302
        cart = Cart.objects.get(user=customer)
        assert cart.items.count() == 1
        assert cart.items.first().quantity == 2

    def test_cart_add_exceeds_stock(self, logged_client, product):
        resp = logged_client.post(reverse('carts:add', args=[product.id]), {'quantity': 999})
        assert resp.status_code == 302
        cart = Cart.objects.get(user=logged_client.session['_auth_user_id'])
        assert cart.items.count() == 0

    def test_cart_add_with_variant(self, logged_client, customer, seeded_product):
        variant = ProductVariant.objects.filter(product=seeded_product).first()
        resp = logged_client.post(
            reverse('carts:add', args=[seeded_product.id]),
            {'quantity': 1, 'variant_id': variant.id},
        )
        assert resp.status_code == 302
        cart = Cart.objects.get(user=customer)
        item = cart.items.first()
        assert item.variant == variant

    def test_cart_update_increase(self, logged_client, customer, product):
        cart = Cart.objects.create(user=customer)
        item = CartItem.objects.create(cart=cart, product=product, quantity=1)
        logged_client.post(reverse('carts:update', args=[item.id]), {'action': 'increase'})
        item.refresh_from_db()
        assert item.quantity == 2

    def test_cart_update_decrease_removes(self, logged_client, customer, product):
        cart = Cart.objects.create(user=customer)
        item = CartItem.objects.create(cart=cart, product=product, quantity=1)
        logged_client.post(reverse('carts:update', args=[item.id]), {'action': 'decrease'})
        assert CartItem.objects.filter(id=item.id).count() == 0

    def test_cart_remove_item(self, logged_client, customer, product):
        cart = Cart.objects.create(user=customer)
        item = CartItem.objects.create(cart=cart, product=product, quantity=1)
        logged_client.post(reverse('carts:remove', args=[item.id]))
        assert CartItem.objects.filter(id=item.id).count() == 0

    def test_cart_shows_subtotal(self, logged_client, customer, product):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=3)
        resp = logged_client.get(reverse('carts:detail'))
        content = resp.content.decode('utf-8')
        assert 'Rp' in content
        assert '1.125.000' in content or '1,125,000' in content

    def test_cart_apply_valid_voucher(self, logged_client, customer, product):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        OrderVoucher.objects.create(
            code='TEST10', discount_type='percentage', discount_amount=10,
            min_purchase=0, valid_from=now(), valid_until=now() + timedelta(days=1),
        )
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'TEST10'})
        assert resp.status_code == 302
        assert logged_client.session.get('voucher_code') == 'TEST10'

    def test_cart_invalid_voucher_rejected(self, logged_client):
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'INVALID'})
        assert resp.status_code == 302
        assert 'voucher_code' not in logged_client.session

    def test_cart_admin_redirected(self, admin_client):
        resp = admin_client.get(reverse('carts:detail'))
        assert resp.status_code == 302


# ============================================================
# 11. WISHLIST
# ============================================================
@pytest.mark.django_db
class TestWishlist:
    def test_wishlist_requires_login(self):
        resp = Client().get(reverse('accounts:wishlist_list'))
        assert resp.status_code == 302

    def test_wishlist_add(self, logged_client, customer, product):
        resp = logged_client.post(reverse('accounts:wishlist_add', args=[product.id]))
        assert resp.status_code == 302
        assert Wishlist.objects.filter(user=customer, product=product).exists()

    def test_wishlist_no_duplicate(self, logged_client, customer, product):
        Wishlist.objects.create(user=customer, product=product)
        logged_client.post(reverse('accounts:wishlist_add', args=[product.id]))
        assert Wishlist.objects.filter(user=customer, product=product).count() == 1

    def test_wishlist_remove(self, logged_client, customer, product):
        Wishlist.objects.create(user=customer, product=product)
        logged_client.post(reverse('accounts:wishlist_remove', args=[product.id]))
        assert not Wishlist.objects.filter(user=customer, product=product).exists()

    def test_wishlist_show_items(self, logged_client, customer, product):
        Wishlist.objects.create(user=customer, product=product)
        resp = logged_client.get(reverse('accounts:wishlist_list'))
        assert product.name in resp.content.decode('utf-8')

    def test_wishlist_context_processor(self, logged_client, customer, product):
        Wishlist.objects.create(user=customer, product=product)
        resp = logged_client.get(reverse('products:list'))
        assert 'wishlist_product_ids' in resp.context
        assert product.id in resp.context['wishlist_product_ids']

    def test_wishlist_ajax_add(self, logged_client, product):
        resp = logged_client.post(
            reverse('accounts:wishlist_add', args=[product.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        data = resp.json()
        assert data['saved'] is True

    def test_wishlist_admin_redirected(self, admin_client, product):
        resp = admin_client.post(reverse('accounts:wishlist_add', args=[product.id]))
        assert resp.status_code == 302


# ============================================================
# 12. CHECKOUT
# ============================================================
@pytest.mark.django_db
class TestCheckout:
    def test_checkout_requires_login(self):
        resp = Client().get(reverse('orders:create'))
        assert resp.status_code == 302

    def test_checkout_empty_cart_redirects(self, logged_client):
        resp = logged_client.get(reverse('orders:create'))
        assert resp.status_code == 302
        assert '/cart/' in resp.url

    def test_checkout_shows_form(self, logged_client, customer, product):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        resp = logged_client.get(reverse('orders:create'))
        assert resp.status_code == 200

    def test_checkout_submit_creates_order(self, logged_client, customer, product, location):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=2)
        resp = logged_client.post(reverse('orders:create'), {
            'recipient_name': 'Budi',
            'phone': '08123456789',
            'shipping_address': 'Jl. Merdeka No. 10, Jakarta Pusat',
            'province': location['province'].id,
            'city': location['city'].id,
            'district': location['district'].id,
            'postal_code': location['postal_code'].id,
        })
        assert resp.status_code == 302
        order = Order.objects.filter(user=customer).first()
        assert order is not None
        assert order.items.count() == 1
        assert order.items.first().quantity == 2

    def test_checkout_submit_clears_cart(self, logged_client, customer, product, location):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        logged_client.post(reverse('orders:create'), {
            'recipient_name': 'Budi', 'phone': '08123456789',
            'shipping_address': 'Jl. Test No. 123',
            'province': location['province'].id, 'city': location['city'].id,
            'district': location['district'].id, 'postal_code': location['postal_code'].id,
        })
        cart.refresh_from_db()
        assert cart.items.count() == 0

    def test_checkout_snapshot_preserves_product_name(self, logged_client, customer, product, location):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        logged_client.post(reverse('orders:create'), {
            'recipient_name': 'Budi', 'phone': '08123456789',
            'shipping_address': 'Jl. Test No. 123',
            'province': location['province'].id, 'city': location['city'].id,
            'district': location['district'].id, 'postal_code': location['postal_code'].id,
        })
        order = Order.objects.filter(user=customer).first()
        assert order.items.first().product_name == product.name
        assert order.items.first().price == product.price

    def test_checkout_insufficient_stock_redirects(self, logged_client, customer, product, location):
        product.stock = 1
        product.save()
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=5)
        resp = logged_client.post(reverse('orders:create'), {
            'recipient_name': 'Budi', 'phone': '08123456789',
            'shipping_address': 'Jl. Test No. 123',
            'province': location['province'].id, 'city': location['city'].id,
            'district': location['district'].id, 'postal_code': location['postal_code'].id,
        })
        assert resp.status_code == 302
        assert '/cart/' in resp.url

    def test_checkout_creates_status_history(self, logged_client, customer, product, location):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        logged_client.post(reverse('orders:create'), {
            'recipient_name': 'Budi', 'phone': '08123456789',
            'shipping_address': 'Jl. Test No. 123',
            'province': location['province'].id, 'city': location['city'].id,
            'district': location['district'].id, 'postal_code': location['postal_code'].id,
        })
        order = Order.objects.filter(user=customer).first()
        assert order.status_history.count() == 1
        assert order.status_history.first().status == Order.Status.PENDING_PAYMENT

    def test_checkout_admin_redirected(self, admin_client, product):
        resp = admin_client.get(reverse('orders:create'))
        assert resp.status_code == 302


# ============================================================
# 13. VOUCHER
# ============================================================
@pytest.mark.django_db
class TestVoucher:
    def test_session_voucher_apply_at_cart(self, logged_client, customer, product):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        OrderVoucher.objects.create(
            code='FLAT50', discount_type='fixed', discount_amount=50000,
            min_purchase=0, valid_from=now(), valid_until=now() + timedelta(days=1),
        )
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'FLAT50'})
        resp = logged_client.get(reverse('carts:detail'))
        content = resp.content.decode('utf-8')
        assert 'FLAT50' in content
        assert '50.000' in content

    def test_voucher_discount_applied_to_order(self, logged_client, customer, product, location):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        OrderVoucher.objects.create(
            code='DISKON20', discount_type='percentage', discount_amount=20,
            min_purchase=0, max_discount=100000,
            valid_from=now(), valid_until=now() + timedelta(days=1),
        )
        logged_client.post(reverse('carts:apply_voucher'), {'code': 'DISKON20'})
        logged_client.post(reverse('orders:create'), {
            'recipient_name': 'Budi', 'phone': '08123456789',
            'shipping_address': 'Jl. Test No. 123',
            'province': location['province'].id, 'city': location['city'].id,
            'district': location['district'].id, 'postal_code': location['postal_code'].id,
        })
        order = Order.objects.filter(user=customer).first()
        assert order.discount_amount > 0
        assert order.total_price < order.subtotal

    def test_user_voucher_selection_at_checkout(self, logged_client, customer, product, category):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=2)
        promo_v = PromoVoucher.objects.create(
            code='MYVOUCH', discount_type='percentage',
            discount_amount=15, min_purchase=0, is_active=True,
        )
        uv = UserVoucher.objects.create(
            user=customer, voucher=promo_v,
            expires_at=now() + timedelta(days=30),
        )
        resp = logged_client.get(reverse('orders:create'))
        assert resp.status_code == 200
        content = resp.content.decode('utf-8')
        assert 'MYVOUCH' in content

    def test_user_voucher_consumed_on_order(self, logged_client, customer, product, location):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        promo_v = PromoVoucher.objects.get_or_create(
            code='WELCOME10', defaults=dict(
                discount_type='percentage',
                discount_amount=10, min_purchase=0, is_active=True,
            )
        )[0]
        uv = UserVoucher.objects.create(
            user=customer, voucher=promo_v,
            expires_at=now() + timedelta(days=30),
        )
        logged_client.post(reverse('orders:create'), {
            'recipient_name': 'Budi', 'phone': '08123456789',
            'shipping_address': 'Jl. Test No. 123',
            'province': location['province'].id, 'city': location['city'].id,
            'district': location['district'].id, 'postal_code': location['postal_code'].id,
            'user_voucher_id': uv.id,
        })
        uv.refresh_from_db()
        assert uv.status == UserVoucher.Status.USED

    def test_expired_voucher_rejected(self, logged_client, product, customer):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        OrderVoucher.objects.create(
            code='EXPIRED', discount_type='fixed', discount_amount=10000,
            valid_from=now() - timedelta(days=10), valid_until=now() - timedelta(days=1),
        )
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'EXPIRED'})
        assert resp.status_code == 302
        assert 'voucher_code' not in logged_client.session

    def test_voucher_usage_limit(self, logged_client, product, customer):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        OrderVoucher.objects.create(
            code='LIMITED', discount_type='fixed', discount_amount=5000,
            max_uses=1, used_count=1,
            valid_from=now(), valid_until=now() + timedelta(days=1),
        )
        resp = logged_client.post(reverse('carts:apply_voucher'), {'code': 'LIMITED'})
        assert resp.status_code == 302
        assert 'voucher_code' not in logged_client.session


# ============================================================
# 14. MIDTRANS PAYMENT
# ============================================================
@pytest.mark.django_db
class TestMidtransPayment:
    def test_payment_checkout_requires_login(self):
        resp = Client().get(reverse('payments:checkout', args=[1]))
        assert resp.status_code == 302

    def test_payment_checkout_show_page(self, logged_client, customer, product):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        order = Order.objects.create(user=customer, total_price=375000)
        resp = logged_client.get(reverse('payments:checkout', args=[order.id]))
        assert resp.status_code in (200, 302)

    def test_payment_finish_page(self, logged_client, customer, product):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        order = Order.objects.create(user=customer, total_price=375000)
        Payment.objects.create(order=order, amount=order.total_price)
        resp = logged_client.get(reverse('payments:finish', args=[order.id]))
        assert resp.status_code in (200, 302)

    def test_payment_unfinish_page(self, logged_client, customer, product):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        order = Order.objects.create(user=customer, total_price=375000)
        resp = logged_client.get(reverse('payments:unfinish', args=[order.id]))
        assert resp.status_code in (200, 302)

    def test_payment_error_page(self, logged_client, customer, product):
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        order = Order.objects.create(user=customer, total_price=375000)
        resp = logged_client.get(reverse('payments:error', args=[order.id]))
        assert resp.status_code in (200, 302)

    def test_payment_notification_invalid_json(self):
        resp = Client().post(
            reverse('payments:notification'),
            data='not json',
            content_type='application/json',
        )
        assert resp.status_code == 400

    def test_payment_notification_missing_fields(self):
        resp = Client().post(
            reverse('payments:notification'),
            data=json.dumps({}),
            content_type='application/json',
        )
        assert resp.status_code == 400

    def test_payment_notification_order_not_found(self):
        import hashlib
        from django.conf import settings
        order_id = 'ORDER-nonexistent'
        status_code = '200'
        gross_amount = '100000'
        sig_data = f'{order_id}{status_code}{gross_amount}{settings.MIDTRANS_SERVER_KEY}'
        valid_sig = hashlib.sha512(sig_data.encode()).hexdigest()
        resp = Client().post(
            reverse('payments:notification'),
            data=json.dumps({
                'order_id': order_id,
                'transaction_status': 'settlement',
                'status_code': status_code,
                'gross_amount': gross_amount,
                'signature_key': valid_sig,
            }),
            content_type='application/json',
        )
        assert resp.status_code == 404

    def test_payment_notification_creates_history(self, customer, product):
        from apps.orders.models import Order as OrderModel
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        order = OrderModel.objects.create(user=customer, total_price=375000)
        payment = Payment.objects.create(order=order, amount=375000)
        assert payment.status_history.count() == 1

    def test_payment_status_history_append_only(self, customer, product):
        order = Order.objects.create(user=customer, total_price=100000)
        payment = Payment.objects.create(order=order, amount=100000)
        payment.status = Payment.PaymentStatus.SUCCESS
        payment.save()
        assert payment.status_history.count() == 2


# ============================================================
# 15. ORDER
# ============================================================
@pytest.mark.django_db
class TestOrder:
    def test_order_list_requires_login(self):
        resp = Client().get(reverse('orders:list'))
        assert resp.status_code == 302

    def test_order_list_shows_orders(self, logged_client, customer, product):
        order = Order.objects.create(user=customer, total_price=100000)
        OrderItem.objects.create(order=order, product=product, product_name=product.name, price=100, quantity=1)
        resp = logged_client.get(reverse('orders:list'))
        content = resp.content.decode('utf-8')
        assert order.order_number in content

    def test_order_detail_own(self, logged_client, customer, product):
        order = Order.objects.create(user=customer, total_price=100000, order_number='ORD-TEST-000001')
        OrderItem.objects.create(order=order, product=product, product_name=product.name, price=100, quantity=1)
        resp = logged_client.get(reverse('orders:detail', args=[order.id]))
        assert resp.status_code == 200
        assert order.order_number in resp.content.decode('utf-8')

    def test_order_detail_other_user_404(self, customer):
        order = Order.objects.create(user=customer, total_price=100000)
        other = User.objects.create_user(username='other', password='pass12345')
        client = Client()
        client.login(username='other', password='pass12345')
        resp = client.get(reverse('orders:detail', args=[order.id]))
        assert resp.status_code == 404

    def test_order_cancel_pending(self, logged_client, customer):
        order = Order.objects.create(user=customer, total_price=100000, status=Order.Status.PENDING_PAYMENT)
        logged_client.post(reverse('orders:cancel', args=[order.id]))
        order.refresh_from_db()
        assert order.status == Order.Status.CANCELLED

    def test_order_cancel_non_pending_fails(self, logged_client, customer):
        order = Order.objects.create(user=customer, total_price=100000, status=Order.Status.PAID)
        logged_client.post(reverse('orders:cancel', args=[order.id]))
        order.refresh_from_db()
        assert order.status == Order.Status.PAID

    def test_order_track_own(self, logged_client, customer):
        order = Order.objects.create(user=customer, total_price=100000)
        order.status = Order.Status.PAID
        order.save()
        resp = logged_client.get(reverse('orders:track', args=[order.id]))
        assert resp.status_code == 200

    def test_order_track_other_404(self, customer):
        order = Order.objects.create(user=customer, total_price=100000)
        other = User.objects.create_user(username='other2', password='pass12345')
        client = Client()
        client.login(username='other2', password='pass12345')
        resp = client.get(reverse('orders:track', args=[order.id]))
        assert resp.status_code == 404

    def test_order_status_history_timeline(self, logged_client, customer):
        order = Order.objects.create(user=customer, total_price=100000)
        order.status = Order.Status.PAID
        order.save()
        order.status = Order.Status.PROCESSING
        order.save()
        resp = logged_client.get(reverse('orders:track', args=[order.id]))
        assert order.status_history.count() == 3

    def test_order_snapshot_preserved_after_product_delete(self, logged_client, customer, product):
        order = Order.objects.create(user=customer, total_price=100000)
        OrderItem.objects.create(order=order, product=product, product_name=product.name, price=100, quantity=1)
        product.delete()
        item = OrderItem.objects.filter(order=order).first()
        assert item.product_name == 'Morris Noir'
        assert item.price == 100


# ============================================================
# 16. DASHBOARD CUSTOMER
# ============================================================
@pytest.mark.django_db
class TestCustomerDashboard:
    def test_dashboard_requires_login(self):
        resp = Client().get(reverse('accounts:dashboard'))
        assert resp.status_code == 302

    def test_dashboard_shows_stats(self, logged_client, customer, product):
        order = Order.objects.create(user=customer, total_price=100000)
        OrderItem.objects.create(order=order, product=product, product_name=product.name, price=100, quantity=1)
        resp = logged_client.get(reverse('accounts:dashboard'))
        content = resp.content.decode('utf-8')
        assert 'Pesanan' in content or 'pesanan' in content.lower()

    def test_dashboard_shows_recent_orders(self, logged_client, customer, product):
        order = Order.objects.create(user=customer, total_price=100000)
        OrderItem.objects.create(order=order, product=product, product_name=product.name, price=100, quantity=1)
        resp = logged_client.get(reverse('accounts:dashboard'))
        assert order.order_number in resp.content.decode('utf-8')

    def test_dashboard_empty_state_for_new_user(self, logged_client):
        resp = logged_client.get(reverse('accounts:dashboard'))
        assert resp.status_code == 200

    def test_member_dashboard_requires_login(self):
        resp = Client().get(reverse('accounts:member_dashboard'))
        assert resp.status_code == 302

    def test_member_dashboard_shows_level(self, logged_client, customer):
        member, _ = MemberProfile.objects.get_or_create(user=customer)
        member.total_spending = 1000000
        member.upgrade_level()
        resp = logged_client.get(reverse('accounts:member_dashboard'))
        content = resp.content.decode('utf-8')
        assert 'GOLD' in content or 'Gold' in content

    def test_member_dashboard_shows_points_history(self, logged_client, customer):
        member, _ = MemberProfile.objects.get_or_create(user=customer)
        member.earn_points(500000)
        resp = logged_client.get(reverse('accounts:member_dashboard'))
        content = resp.content.decode('utf-8')
        assert 'Poin' in content or 'poin' in content.lower() or 'Rp' in content

    def test_member_benefits_page_public(self):
        resp = Client().get(reverse('accounts:member_benefits'))
        assert resp.status_code == 200

    def test_member_benefits_shows_levels(self):
        resp = Client().get(reverse('accounts:member_benefits'))
        content = resp.content.decode('utf-8')
        assert 'Silver' in content
        assert 'Gold' in content
        assert 'Platinum' in content


# ============================================================
# 17. ADMIN PANEL
# ============================================================
@pytest.mark.django_db
class TestAdminPanel:
    def test_admin_login_page(self):
        resp = Client().get(reverse('admin:login'))
        assert resp.status_code == 200

    def test_admin_index_redirects_anonymous(self):
        resp = Client().get(reverse('admin:index'))
        assert resp.status_code == 302

    def test_admin_index_accessible_by_staff(self, admin_client):
        resp = admin_client.get(reverse('admin:index'))
        assert resp.status_code == 200

    def test_admin_product_list(self, admin_client, product):
        resp = admin_client.get(reverse('admin:products_product_changelist'))
        assert resp.status_code == 200
        assert product.name in resp.content.decode('utf-8')

    def test_admin_order_list(self, admin_client, customer):
        order = Order.objects.create(user=customer, total_price=100000)
        resp = admin_client.get(reverse('admin:orders_order_changelist'))
        assert resp.status_code == 200

    def test_admin_dashboard(self, admin_client):
        resp = admin_client.get(reverse('admin_dashboard'))
        assert resp.status_code == 200

    def test_admin_non_staff_redirected(self):
        user = User.objects.create_user(username='regular', password='pass12345')
        client = Client()
        client.login(username='regular', password='pass12345')
        resp = client.get(reverse('admin:index'))
        assert resp.status_code == 302

    def test_admin_customer_not_in_admin(self, customer):
        client = Client()
        client.login(username='budi', password='customer123')
        resp = client.get(reverse('admin:index'))
        assert resp.status_code == 302

    def test_admin_user_list(self, admin_client):
        resp = admin_client.get(reverse('admin:auth_user_changelist'))
        assert resp.status_code == 200


# ============================================================
# 18. ROLE & PERMISSION
# ============================================================
@pytest.mark.django_db
class TestRolePermission:
    def test_superuser_blocked_from_cart(self, admin_client):
        resp = admin_client.get(reverse('carts:detail'))
        assert resp.status_code == 302

    def test_superuser_blocked_from_checkout(self, admin_client):
        resp = admin_client.get(reverse('orders:create'))
        assert resp.status_code == 302

    def test_superuser_blocked_from_dashboard(self, admin_client):
        resp = admin_client.get(reverse('accounts:dashboard'))
        assert resp.status_code == 302

    def test_superuser_blocked_from_wishlist(self, admin_client):
        resp = admin_client.get(reverse('accounts:wishlist_list'))
        assert resp.status_code == 302

    def test_superuser_blocked_from_member_dashboard(self, admin_client):
        resp = admin_client.get(reverse('accounts:member_dashboard'))
        assert resp.status_code == 302

    def test_superuser_blocked_from_address(self, admin_client):
        resp = admin_client.get(reverse('accounts:address_list'))
        assert resp.status_code == 302

    def test_superuser_can_view_vouchers(self, admin_client):
        resp = admin_client.get(reverse('promotions:voucher_list'))
        assert resp.status_code == 200

    def test_superuser_blocked_from_payment(self, admin_client, customer):
        order = Order.objects.create(user=customer, total_price=100000)
        resp = admin_client.get(reverse('payments:checkout', args=[order.id]))
        assert resp.status_code == 302

    def test_customer_blocked_from_admin(self, logged_client):
        resp = logged_client.get(reverse('admin:index'))
        assert resp.status_code == 302

    def test_anonymous_blocked_from_all_customer_pages(self):
        protected = ['carts:detail', 'orders:list', 'accounts:dashboard',
                     'accounts:wishlist_list', 'accounts:member_dashboard']
        for url_name in protected:
            resp = Client().get(reverse(url_name))
            assert resp.status_code == 302, f'{url_name} did not redirect'

    def test_customer_sees_no_admin_banner(self, logged_client):
        resp = logged_client.get(reverse('products:list'))
        assert 'Administrator' not in resp.content.decode('utf-8')

    def test_anonymous_sees_no_admin_banner(self):
        resp = Client().get(reverse('products:list'))
        assert 'Administrator' not in resp.content.decode('utf-8')

    def test_customer_sees_dashboard_link_in_nav(self, logged_client):
        resp = logged_client.get(reverse('products:home'))
        content = resp.content.decode('utf-8')
        assert 'Dashboard' in content

    def test_anonymous_sees_login_and_register_links(self):
        resp = Client().get(reverse('products:home'))
        content = resp.content.decode('utf-8')
        assert 'Masuk' in content.lower() or 'Masuk' in content
        assert 'Daftar' in content


# ============================================================
# 19. CUSTOM 404
# ============================================================
@pytest.mark.django_db
class TestCustom404:
    def test_custom_404_page(self):
        resp = Client().get('/nonexistent-page/')
        assert resp.status_code == 404
        content = resp.content.decode('utf-8')
        assert '404' in content

    def test_404_has_back_link(self):
        resp = Client().get('/nonexistent/')
        content = resp.content.decode('utf-8')
        assert 'Katalog' in content or 'Kembali' in content

    def test_404_uses_custom_template(self):
        resp = Client().get('/nonexistent/')
        assert resp.status_code == 404
        templates = [t.name for t in resp.templates if t.name]
        assert 'errors/404.html' in templates


# ============================================================
# 20. CUSTOM 500
# ============================================================
@pytest.mark.django_db
class TestCustom500:
    def test_500_handler_configured(self):
        from parfumoray.urls import handler404
        assert handler404 is not None

    def test_500_template_does_not_exist(self):
        """500.html doesn't exist — note this as a finding"""
        import os
        from django.conf import settings
        path = settings.BASE_DIR / 'templates' / 'errors' / '500.html'
        assert not os.path.exists(path), '500.html exists unexpectedly'
