import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from apps.accounts.forms import CustomerAddressForm, RegisterForm, ProfileUpdateForm
from apps.accounts.models import CustomerAddress, MemberProfile, PointTransaction, Wishlist
from apps.regions.models import Province, City, District, PostalCode


@pytest.mark.django_db
class TestRegisterForm:
    def test_valid_registration(self):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'Str0ng!Pass',
            'password2': 'Str0ng!Pass',
        }
        form = RegisterForm(data)
        assert form.is_valid()

    def test_duplicate_email(self):
        User.objects.create_user(username='existing', email='dup@example.com', password='pass12345')
        data = {
            'username': 'newuser',
            'email': 'dup@example.com',
            'password1': 'Str0ng!Pass',
            'password2': 'Str0ng!Pass',
        }
        form = RegisterForm(data)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_password_mismatch(self):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'password1',
            'password2': 'password2',
        }
        form = RegisterForm(data)
        assert not form.is_valid()


@pytest.mark.django_db
class TestProfileUpdateForm:
    def test_valid_update(self):
        user = User.objects.create_user(username='testuser', email='test@example.com', password='pass12345')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'phone': '08123456789',
            'address': 'Jl. Test No. 1',
        }
        form = ProfileUpdateForm(data, user=user, instance=user.profile)
        assert form.is_valid()

    def test_duplicate_username(self):
        User.objects.create_user(username='other', email='other@example.com', password='pass12345')
        user = User.objects.create_user(username='testuser', email='test@example.com', password='pass12345')
        data = {
            'username': 'other',
            'email': 'test@example.com',
        }
        form = ProfileUpdateForm(data, user=user, instance=user.profile)
        assert not form.is_valid()
        assert 'username' in form.errors

    def test_duplicate_email(self):
        User.objects.create_user(username='other', email='other@example.com', password='pass12345')
        user = User.objects.create_user(username='testuser', email='test@example.com', password='pass12345')
        data = {
            'username': 'testuser',
            'email': 'other@example.com',
        }
        form = ProfileUpdateForm(data, user=user, instance=user.profile)
        assert not form.is_valid()
        assert 'email' in form.errors


@pytest.mark.django_db
class TestAuthViews:
    def test_login_page(self):
        client = Client()
        response = client.get(reverse('accounts:login'))
        assert response.status_code == 200

    def test_register_page(self):
        client = Client()
        response = client.get(reverse('accounts:register'))
        assert response.status_code == 200

    def test_successful_register_creates_profile(self):
        client = Client()
        response = client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'Str0ng!Pass123',
            'password2': 'Str0ng!Pass123',
        })
        assert response.status_code == 302
        assert response.url == reverse('accounts:login')
        user = User.objects.get(username='newuser')
        assert hasattr(user, 'profile')

    def test_register_redirects_to_login(self):
        client = Client()
        response = client.post(reverse('accounts:register'), {
            'username': 'redirectuser',
            'email': 'redirect@example.com',
            'password1': 'Str0ng!Pass123',
            'password2': 'Str0ng!Pass123',
        })
        assert response.status_code == 302
        assert response.url == reverse('accounts:login')

    def test_register_does_not_auto_login(self):
        client = Client()
        response = client.post(reverse('accounts:register'), {
            'username': 'noautologin',
            'email': 'noauto@example.com',
            'password1': 'Str0ng!Pass123',
            'password2': 'Str0ng!Pass123',
        })
        assert response.status_code == 302
        assert response.url == reverse('accounts:login')
        response = client.get(reverse('accounts:dashboard'))
        assert response.status_code == 302
        response2 = client.get(reverse('products:list'))
        content = response2.content.decode('utf-8').lower()
        assert 'noautologin' not in content

    def test_register_shows_success_message(self):
        client = Client()
        response = client.post(reverse('accounts:register'), {
            'username': 'messagetest',
            'email': 'message@example.com',
            'password1': 'Str0ng!Pass123',
            'password2': 'Str0ng!Pass123',
        }, follow=True)
        messages_list = list(response.context['messages'])
        assert len(messages_list) == 1
        assert 'Registrasi berhasil' in str(messages_list[0])

    def test_dashboard_requires_login(self):
        client = Client()
        response = client.get(reverse('accounts:dashboard'))
        assert response.status_code == 302

    def test_dashboard_logged_in(self):
        client = Client()
        user = User.objects.create_user(username='testuser', password='pass12345')
        client.force_login(user)
        response = client.get(reverse('accounts:dashboard'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestPasswordReset:
    def test_forgot_password_page(self):
        client = Client()
        response = client.get(reverse('accounts:forgot_password'))
        assert response.status_code == 200
        assert 'accounts/forgot_password.html' in [t.name for t in response.templates if t.name]

    def test_forgot_password_submit_valid_email(self):
        client = Client()
        User.objects.create_user(username='testuser', email='test@example.com', password='oldpass123')
        response = client.post(reverse('accounts:forgot_password'), {'email': 'test@example.com'})
        assert response.status_code == 302
        assert response.url == reverse('accounts:password_reset_sent')

    def test_forgot_password_submit_unknown_email(self):
        client = Client()
        response = client.post(reverse('accounts:forgot_password'), {'email': 'unknown@example.com'})
        assert response.status_code == 302
        assert response.url == reverse('accounts:password_reset_sent')

    def test_password_reset_sent_page(self):
        client = Client()
        response = client.get(reverse('accounts:password_reset_sent'))
        assert response.status_code == 200

    def test_create_new_password_valid_token_redirects(self):
        client = Client()
        user = User.objects.create_user(username='testuser', email='test@example.com', password='oldpass123')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        response = client.get(reverse('accounts:create_new_password', kwargs={'uidb64': uid, 'token': token}))
        assert response.status_code == 302
        assert '/set-password/' in response.url

    def test_create_new_password_invalid_token(self):
        client = Client()
        user = User.objects.create_user(username='testuser', email='test@example.com', password='oldpass123')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        response = client.get(reverse('accounts:create_new_password', kwargs={'uidb64': uid, 'token': 'invalid-token-123'}))
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'Tautan Tidak Valid' in content or 'invalid' in content.lower()

    def test_create_new_password_expired_token(self):
        client = Client()
        user = User.objects.create_user(username='testuser', email='test@example.com', password='oldpass123')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        user.set_password('newpassword')
        user.save()
        response = client.get(reverse('accounts:create_new_password', kwargs={'uidb64': uid, 'token': token}))
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'Tautan Tidak Valid' in content or 'invalid' in content.lower()

    def test_create_new_password_submit_success(self):
        client = Client()
        user = User.objects.create_user(username='testuser', email='test@example.com', password='oldpass123')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        response = client.get(reverse('accounts:create_new_password', kwargs={'uidb64': uid, 'token': token}))
        assert response.status_code == 302
        set_password_url = response.url
        response = client.post(set_password_url, {
            'new_password1': 'StrongNewPass456!',
            'new_password2': 'StrongNewPass456!',
        })
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.check_password('StrongNewPass456!')
        assert not user.check_password('oldpass123')

    def test_password_reset_success_page(self):
        client = Client()
        response = client.get(reverse('accounts:password_reset_success'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestWishlist:
    def test_wishlist_requires_login(self):
        client = Client()
        response = client.get(reverse('accounts:wishlist_list'))
        assert response.status_code == 302

    def test_wishlist_requires_customer(self):
        client = Client()
        user = User.objects.create_superuser(username='admin', password='admin123', email='admin@test.com')
        client.force_login(user)
        response = client.get(reverse('accounts:wishlist_list'))
        assert response.status_code == 302

    def test_wishlist_list_empty(self):
        client = Client()
        user = User.objects.create_user(username='testuser', password='pass12345')
        client.force_login(user)
        response = client.get(reverse('accounts:wishlist_list'))
        assert response.status_code == 200
        assert 'Wishlist Masih Kosong' in response.content.decode('utf-8')

    def test_wishlist_add(self):
        client = Client()
        user = User.objects.create_user(username='testuser', password='pass12345')
        client.force_login(user)
        from apps.products.models import Product, Category, Brand
        cat = Category.objects.create(name='Test', slug='test')
        brand = Brand.objects.create(name='Test', slug='test')
        product = Product.objects.create(name='Test Perfume', slug='test-perfume', category=cat, brand=brand, price=100000, stock=10)
        response = client.post(reverse('accounts:wishlist_add', args=[product.id]))
        assert response.status_code == 302
        assert Wishlist.objects.filter(user=user, product=product).exists()

    def test_wishlist_no_duplicate(self):
        client = Client()
        user = User.objects.create_user(username='testuser', password='pass12345')
        client.force_login(user)
        from apps.products.models import Product, Category, Brand
        cat = Category.objects.create(name='Test', slug='test')
        brand = Brand.objects.create(name='Test', slug='test')
        product = Product.objects.create(name='Test Perfume', slug='test-perfume', category=cat, brand=brand, price=100000, stock=10)
        Wishlist.objects.create(user=user, product=product)
        response = client.post(reverse('accounts:wishlist_add', args=[product.id]))
        assert response.status_code == 302
        assert Wishlist.objects.filter(user=user, product=product).count() == 1

    def test_wishlist_remove(self):
        client = Client()
        user = User.objects.create_user(username='testuser', password='pass12345')
        client.force_login(user)
        from apps.products.models import Product, Category, Brand
        cat = Category.objects.create(name='Test', slug='test')
        brand = Brand.objects.create(name='Test', slug='test')
        product = Product.objects.create(name='Test Perfume', slug='test-perfume', category=cat, brand=brand, price=100000, stock=10)
        Wishlist.objects.create(user=user, product=product)
        response = client.post(reverse('accounts:wishlist_remove', args=[product.id]))
        assert response.status_code == 302
        assert not Wishlist.objects.filter(user=user, product=product).exists()

    def test_wishlist_add_ajax(self):
        client = Client()
        user = User.objects.create_user(username='testuser', password='pass12345')
        client.force_login(user)
        from apps.products.models import Product, Category, Brand
        cat = Category.objects.create(name='Test', slug='test')
        brand = Brand.objects.create(name='Test', slug='test')
        product = Product.objects.create(name='Test Perfume', slug='test-perfume', category=cat, brand=brand, price=100000, stock=10)
        response = client.post(
            reverse('accounts:wishlist_add', args=[product.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        assert response.status_code == 200
        data = response.json()
        assert data['saved'] is True
        assert data['in_wishlist'] is True

    def test_wishlist_remove_ajax(self):
        client = Client()
        user = User.objects.create_user(username='testuser', password='pass12345')
        client.force_login(user)
        from apps.products.models import Product, Category, Brand
        cat = Category.objects.create(name='Test', slug='test')
        brand = Brand.objects.create(name='Test', slug='test')
        product = Product.objects.create(name='Test Perfume', slug='test-perfume', category=cat, brand=brand, price=100000, stock=10)
        Wishlist.objects.create(user=user, product=product)
        response = client.post(
            reverse('accounts:wishlist_remove', args=[product.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        assert response.status_code == 200
        data = response.json()
        assert data['removed'] is True
        assert data['in_wishlist'] is False

    def test_wishlist_product_ids_context_processor(self):
        client = Client()
        user = User.objects.create_user(username='testuser', password='pass12345')
        client.force_login(user)
        from apps.products.models import Product, Category, Brand
        cat = Category.objects.create(name='Test', slug='test')
        brand = Brand.objects.create(name='Test', slug='test')
        product = Product.objects.create(name='Test Perfume', slug='test-perfume', category=cat, brand=brand, price=100000, stock=10)
        Wishlist.objects.create(user=user, product=product)

        response = client.get(reverse('products:list'))
        assert 'wishlist_product_ids' in response.context
        assert product.id in response.context['wishlist_product_ids']

    def test_wishlist_page_shows_items(self):
        client = Client()
        user = User.objects.create_user(username='testuser', password='pass12345')
        client.force_login(user)
        from apps.products.models import Product, Category, Brand
        cat = Category.objects.create(name='Test', slug='test')
        brand = Brand.objects.create(name='Test', slug='test')
        product = Product.objects.create(name='Test Perfume', slug='test-perfume', category=cat, brand=brand, price=100000, stock=10)
        Wishlist.objects.create(user=user, product=product)

        response = client.get(reverse('accounts:wishlist_list'))
        content = response.content.decode('utf-8')
        assert product.name in content


@pytest.mark.django_db
class TestMemberProfile:
    def test_member_profile_created_on_register(self):
        client = Client()
        response = client.post(reverse('accounts:register'), {
            'username': 'loyaluser',
            'email': 'loyal@example.com',
            'password1': 'Str0ng!Pass',
            'password2': 'Str0ng!Pass',
        })
        assert response.status_code == 302
        assert response.url == reverse('accounts:login')
        user = User.objects.get(username='loyaluser')
        member = MemberProfile.objects.get(user=user)
        assert member.level == 'SILVER'
        assert member.total_points == 0
        assert member.total_spending == 0

    def test_member_dashboard_requires_login(self):
        response = Client().get(reverse('accounts:member_dashboard'))
        assert response.status_code == 302

    def test_member_dashboard_shows_level_and_points(self):
        from decimal import Decimal
        client = Client()
        user = User.objects.create_user(username='loyaluser', password='pass12345')
        member, _ = MemberProfile.objects.get_or_create(user=user)
        member.total_spending = Decimal('150000')
        member.save(update_fields=['total_spending'])
        member.earn_points(150000)
        member.upgrade_level()
        client.force_login(user)
        response = client.get(reverse('accounts:member_dashboard'))
        assert response.status_code == 200
        member = response.context['member']
        assert member.total_points >= 15
        assert member.total_spending >= 150000
        content = response.content.decode('utf-8')
        assert 'Silver' in content
        assert 'Rp' in content

    def test_member_dashboard_shows_point_history(self):
        client = Client()
        user = User.objects.create_user(username='pointuser', password='pass12345')
        member, _ = MemberProfile.objects.get_or_create(user=user)
        member.earn_points(500000)
        client.force_login(user)
        response = client.get(reverse('accounts:member_dashboard'))
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'Poin dari pembelian' in content

    def test_earn_points(self):
        user = User.objects.create_user(username='earnuser', password='pass12345')
        member, _ = MemberProfile.objects.get_or_create(user=user)
        member.earn_points(500000)
        assert member.total_points == 500
        assert PointTransaction.objects.filter(user=user, type='EARN', points=500).exists()

    def test_level_upgrade_to_gold(self):
        user = User.objects.create_user(username='golduser', password='pass12345')
        member, _ = MemberProfile.objects.get_or_create(user=user)
        member.total_spending = 1000000
        member.upgrade_level()
        assert member.level == 'GOLD'

    def test_level_upgrade_to_platinum(self):
        user = User.objects.create_user(username='platuser', password='pass12345')
        member, _ = MemberProfile.objects.get_or_create(user=user)
        member.total_spending = 5000000
        member.upgrade_level()
        assert member.level == 'PLATINUM'

    def test_upgrade_logs_transaction(self):
        user = User.objects.create_user(username='upuser', password='pass12345')
        member, _ = MemberProfile.objects.get_or_create(user=user)
        member.total_spending = 1000000
        member.upgrade_level()
        assert PointTransaction.objects.filter(user=user, type='UPGRADE').exists()


@pytest.mark.django_db
class TestCustomerAddressHierarchy:
    def _setup_regions(self):
        prov = Province.objects.create(code='11', name='Test Province')
        city = City.objects.create(code='1101', name='Test City', province=prov)
        other_city = City.objects.create(code='1102', name='Other City', province=prov)
        dist = District.objects.create(code='110101', name='Test District', city=city)
        pc = PostalCode.objects.create(code='11111', district=dist)
        return prov, city, other_city, dist, pc

    def test_valid_hierarchy(self):
        prov, city, _, dist, pc = self._setup_regions()
        form = CustomerAddressForm(data={
            'recipient_name': 'Test', 'phone': '08123456789',
            'address_line': 'Jl. Test No. 100',
            'province': prov.id, 'city': city.id,
            'district': dist.id, 'postal_code': pc.id,
        })
        assert form.is_valid(), form.errors

    def test_city_not_in_province(self):
        prov, _, _, dist, pc = self._setup_regions()
        other_prov = Province.objects.create(code='12', name='Other Province')
        orphan_city = City.objects.create(code='1201', name='Orphan City', province=other_prov)
        form = CustomerAddressForm(data={
            'recipient_name': 'Test', 'phone': '08123456789',
            'address_line': 'Jl. Test No. 100',
            'province': prov.id, 'city': orphan_city.id,
            'district': dist.id, 'postal_code': pc.id,
        })
        assert not form.is_valid()
        assert 'city' in form.errors

    def test_district_not_in_city(self):
        prov, city, _, _, pc = self._setup_regions()
        other_city = City.objects.create(code='1103', name='Other City', province=prov)
        orphan_dist = District.objects.create(code='110301', name='Orphan District', city=other_city)
        form = CustomerAddressForm(data={
            'recipient_name': 'Test', 'phone': '08123456789',
            'address_line': 'Jl. Test No. 100',
            'province': prov.id, 'city': city.id,
            'district': orphan_dist.id, 'postal_code': pc.id,
        })
        assert not form.is_valid()
        assert 'district' in form.errors

    def test_postal_code_not_in_district(self):
        prov, city, _, dist, _ = self._setup_regions()
        other_dist = District.objects.create(code='110102', name='Other District', city=city)
        orphan_pc = PostalCode.objects.create(code='22222', district=other_dist)
        form = CustomerAddressForm(data={
            'recipient_name': 'Test', 'phone': '08123456789',
            'address_line': 'Jl. Test No. 100',
            'province': prov.id, 'city': city.id,
            'district': dist.id, 'postal_code': orphan_pc.id,
        })
        assert not form.is_valid()
        assert 'postal_code' in form.errors
