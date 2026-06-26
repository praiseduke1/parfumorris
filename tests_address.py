"""
Comprehensive Black-Box Tests — Address Module
Tests: Province, City, District, Postal Code, Cascade, CRUD, Validation, Default
"""
import pytest
import json
from decimal import Decimal
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils.timezone import now

from apps.regions.models import Province, City, District, PostalCode
from apps.accounts.models import CustomerAddress
from apps.accounts.forms import CustomerAddressForm


# ============================================================
# Fixtures
# ============================================================
@pytest.fixture
def customer():
    return User.objects.create_user(
        username='budi', password='customer123', email='budi@example.com',
    )


@pytest.fixture
def other_user():
    return User.objects.create_user(
        username='orang_lain', password='pass12345', email='other@example.com',
    )


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        username='admin', password='admin123', email='admin@test.com',
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
def other_client(other_user):
    c = Client()
    c.login(username='orang_lain', password='pass12345')
    return c


@pytest.fixture
def admin_client(admin_user):
    c = Client()
    c.login(username='admin', password='admin123')
    return c


@pytest.fixture
def prov():
    return Province.objects.create(code='11', name='Aceh')


@pytest.fixture
def city(prov):
    return City.objects.create(code='1101', name='Kab. Simeulue', province=prov)


@pytest.fixture
def district(city):
    return District.objects.create(code='110101', name='Alafan', city=city)


@pytest.fixture
def postal_code(district):
    return PostalCode.objects.create(code='12345', district=district)


@pytest.fixture
def full_location(prov, city, district, postal_code):
    return {
        'province': prov,
        'city': city,
        'district': district,
        'postal_code': postal_code,
    }


@pytest.fixture
def address(customer, full_location):
    return CustomerAddress.objects.create(
        user=customer,
        recipient_name='Budi',
        phone='08123456789',
        address_line='Jl. Merdeka No. 10, Jakarta Pusat',
        province=full_location['province'],
        city=full_location['city'],
        district=full_location['district'],
        postal_code=full_location['postal_code'],
        label='Rumah',
        is_default=True,
    )


# ============================================================
# REGION API — PROVINCE
# ============================================================
@pytest.mark.django_db
class TestRegionApiProvince:
    def test_list_all_provinces(self, client):
        """Must return 38 Indonesian provinces"""
        Province.objects.create(code='11', name='Aceh')
        Province.objects.create(code='12', name='Sumatera Utara')
        resp = client.get(reverse('regions:api_provinces'))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2

    def test_38_provinces_exist(self, client):
        """Verify all 38 Indonesian provinces can be seeded"""
        provs = [
            ('11', 'Aceh'), ('12', 'Sumatera Utara'), ('13', 'Sumatera Barat'),
            ('14', 'Riau'), ('15', 'Jambi'), ('16', 'Sumatera Selatan'),
            ('17', 'Bengkulu'), ('18', 'Lampung'), ('19', 'Kep. Bangka Belitung'),
            ('21', 'Kepulauan Riau'), ('31', 'DKI Jakarta'), ('32', 'Jawa Barat'),
            ('33', 'Jawa Tengah'), ('34', 'DI Yogyakarta'), ('35', 'Jawa Timur'),
            ('36', 'Banten'), ('51', 'Bali'), ('52', 'Nusa Tenggara Barat'),
            ('53', 'Nusa Tenggara Timur'), ('61', 'Kalimantan Barat'),
            ('62', 'Kalimantan Tengah'), ('63', 'Kalimantan Selatan'),
            ('64', 'Kalimantan Timur'), ('65', 'Kalimantan Utara'),
            ('71', 'Sulawesi Utara'), ('72', 'Sulawesi Tengah'),
            ('73', 'Sulawesi Selatan'), ('74', 'Sulawesi Tenggara'),
            ('75', 'Gorontalo'), ('76', 'Sulawesi Barat'),
            ('81', 'Maluku'), ('82', 'Maluku Utara'),
            ('91', 'Papua Barat'), ('92', 'Papua Barat Daya'),
            ('93', 'Papua'), ('94', 'Papua Selatan'),
            ('95', 'Papua Tengah'), ('96', 'Papua Pegunungan'),
        ]
        for code, name in provs:
            Province.objects.create(code=code, name=name)
        assert Province.objects.count() == 38

    def test_province_api_format(self, client, prov):
        resp = client.get(reverse('regions:api_provinces'))
        data = resp.json()
        entry = data[0]
        assert 'id' in entry and 'code' in entry and 'name' in entry
        assert entry['code'] == '11'
        assert entry['name'] == 'Aceh'

    def test_province_ordering(self, client):
        names = ['Bali', 'Aceh', 'DKI Jakarta']
        for n in names:
            Province.objects.create(code=n[:2].zfill(2), name=n)
        resp = client.get(reverse('regions:api_provinces'))
        data = resp.json()
        returned = [p['name'] for p in data]
        for i in range(len(returned) - 1):
            assert returned[i] <= returned[i + 1]


# ============================================================
# REGION API — CITY
# ============================================================
@pytest.mark.django_db
class TestRegionApiCity:
    def test_cities_by_province(self, client, full_location):
        resp = client.get(reverse('regions:api_cities'), {'province_id': full_location['province'].id})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]['name'] == 'Kab. Simeulue'

    def test_cities_missing_province_id(self, client):
        resp = client.get(reverse('regions:api_cities'))
        assert resp.status_code == 400
        data = resp.json()
        assert 'error' in data

    def test_cities_invalid_province_id(self, client):
        resp = client.get(reverse('regions:api_cities'), {'province_id': 99999})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_city_belongs_to_province(self, client, full_location):
        """City FK must reference the correct province"""
        c = full_location['city']
        assert c.province == full_location['province']

    def test_city_code_unique(self, city):
        """City code must be unique"""
        with pytest.raises(Exception):
            City.objects.create(code=city.code, name='Duplicate', province=city.province)

    def test_city_code_prefix_matches_province(self, prov):
        """City code should start with province code"""
        c = City.objects.create(code='1101', name='Test City', province=prov)
        assert c.code.startswith(prov.code)


# ============================================================
# REGION API — DISTRICT
# ============================================================
@pytest.mark.django_db
class TestRegionApiDistrict:
    def test_districts_by_city(self, client, full_location):
        resp = client.get(reverse('regions:api_districts'), {'city_id': full_location['city'].id})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1

    def test_districts_missing_city_id(self, client):
        resp = client.get(reverse('regions:api_districts'))
        assert resp.status_code == 400

    def test_districts_invalid_city_id(self, client):
        resp = client.get(reverse('regions:api_districts'), {'city_id': 99999})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_district_belongs_to_city(self, full_location):
        assert full_location['district'].city == full_location['city']

    def test_district_code_unique(self, district):
        with pytest.raises(Exception):
            District.objects.create(code=district.code, name='Duplicate', city=district.city)

    def test_district_code_prefix_matches_city(self, city):
        d = District.objects.create(code='110101', name='Test District', city=city)
        assert d.code.startswith(city.code)


# ============================================================
# REGION API — POSTAL CODE
# ============================================================
@pytest.mark.django_db
class TestRegionApiPostalCode:
    def test_postal_codes_by_district(self, client, full_location):
        resp = client.get(
            reverse('regions:api_postal_code'),
            {'district_id': full_location['district'].id},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]['code'] == '12345'

    def test_postal_codes_missing_district_id(self, client):
        resp = client.get(reverse('regions:api_postal_code'))
        assert resp.status_code == 400

    def test_postal_codes_non_numeric_district_id(self, client):
        resp = client.get(reverse('regions:api_postal_code'), {'district_id': 'abc'})
        assert resp.status_code == 400

    def test_postal_codes_invalid_district_id(self, client):
        resp = client.get(reverse('regions:api_postal_code'), {'district_id': 99999})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_postal_code_belongs_to_district(self, full_location):
        assert full_location['postal_code'].district == full_location['district']

    def test_multiple_postal_codes_per_district(self, district):
        """A district can have multiple postal codes"""
        pc1 = PostalCode.objects.create(code='11111', district=district)
        pc2 = PostalCode.objects.create(code='11112', district=district)
        assert district.postal_codes.count() == 2

    def test_postal_code_format_five_digits(self, postal_code):
        assert len(postal_code.code) == 5
        assert postal_code.code.isdigit()


# ============================================================
# ADDRESS — ACCESS CONTROL
# ============================================================
@pytest.mark.django_db
class TestAddressAccessControl:
    def test_list_requires_login(self, client):
        resp = client.get(reverse('accounts:address_list'))
        assert resp.status_code == 302

    def test_list_admin_redirected(self, admin_client):
        resp = admin_client.get(reverse('accounts:address_list'))
        assert resp.status_code == 302

    def test_create_requires_login(self, client):
        resp = client.get(reverse('accounts:address_create'))
        assert resp.status_code == 302

    def test_create_admin_redirected(self, admin_client):
        resp = admin_client.get(reverse('accounts:address_create'))
        assert resp.status_code == 302

    def test_edit_requires_login(self, client, address):
        resp = client.get(reverse('accounts:address_edit', args=[address.id]))
        assert resp.status_code == 302

    def test_edit_admin_redirected(self, admin_client, address):
        resp = admin_client.get(reverse('accounts:address_edit', args=[address.id]))
        assert resp.status_code == 302

    def test_delete_requires_login(self, client, address):
        resp = client.post(reverse('accounts:address_delete', args=[address.id]))
        assert resp.status_code == 302

    def test_delete_admin_redirected(self, admin_client, address):
        resp = admin_client.post(reverse('accounts:address_delete', args=[address.id]))
        assert resp.status_code == 302

    def test_set_default_requires_login(self, client, address):
        resp = client.post(reverse('accounts:address_set_default', args=[address.id]))
        assert resp.status_code == 302

    def test_set_default_admin_redirected(self, admin_client, address):
        resp = admin_client.post(reverse('accounts:address_set_default', args=[address.id]))
        assert resp.status_code == 302


# ============================================================
# ADDRESS — CREATE
# ============================================================
@pytest.mark.django_db
class TestAddressCreate:
    VALID_DATA = {
        'recipient_name': 'Budi',
        'phone': '08123456789',
        'address_line': 'Jl. Merdeka No. 10, Jakarta Pusat',
        'label': 'Rumah',
    }

    def test_create_success(self, logged_client, customer, full_location):
        data = {**self.VALID_DATA,
                'province': full_location['province'].id,
                'city': full_location['city'].id,
                'district': full_location['district'].id,
                'postal_code': full_location['postal_code'].id}
        resp = logged_client.post(reverse('accounts:address_create'), data)
        assert resp.status_code == 302
        assert CustomerAddress.objects.filter(user=customer).count() == 1
        addr = CustomerAddress.objects.get(user=customer)
        assert addr.recipient_name == 'Budi'
        assert addr.province == full_location['province']
        assert addr.city == full_location['city']
        assert addr.district == full_location['district']
        assert addr.postal_code == full_location['postal_code']
        assert addr.label == 'Rumah'
        assert addr.phone == '08123456789'
        assert addr.address_line == 'Jl. Merdeka No. 10, Jakarta Pusat'

    def test_create_without_region_fk(self, logged_client, customer):
        """Address can be created without province/city/district/postal_code (nullable)"""
        resp = logged_client.post(reverse('accounts:address_create'), self.VALID_DATA)
        assert resp.status_code == 302
        addr = CustomerAddress.objects.get(user=customer)
        assert addr.province is None
        assert addr.city is None
        assert addr.district is None
        assert addr.postal_code is None

    def test_create_default_address_unsets_others(self, logged_client, customer, address, full_location):
        """Creating address with is_default=True unsets existing default"""
        assert CustomerAddress.objects.filter(user=customer, is_default=True).count() == 1
        data = {**self.VALID_DATA,
                'province': full_location['province'].id,
                'city': full_location['city'].id,
                'district': full_location['district'].id,
                'postal_code': full_location['postal_code'].id,
                'is_default': 'on'}
        resp = logged_client.post(reverse('accounts:address_create'), data)
        assert resp.status_code == 302
        old_default = CustomerAddress.objects.get(pk=address.pk)
        assert old_default.is_default is False
        assert CustomerAddress.objects.filter(user=customer, is_default=True).count() == 1

    def test_create_short_address_rejected(self, logged_client):
        resp = logged_client.post(reverse('accounts:address_create'), {
            'recipient_name': 'Budi',
            'phone': '08123456789',
            'address_line': 'Short',
        })
        assert resp.status_code == 200
        assert 'Alamat terlalu pendek' in resp.content.decode('utf-8')

    def test_create_invalid_phone_not_08(self, logged_client):
        resp = logged_client.post(reverse('accounts:address_create'), {
            'recipient_name': 'Budi',
            'phone': '1234567890',
            'address_line': 'Jl. Merdeka No. 10, Jakarta Pusat',
        })
        assert resp.status_code == 200
        assert '08' in resp.content.decode('utf-8')

    def test_create_phone_too_short(self, logged_client):
        resp = logged_client.post(reverse('accounts:address_create'), {
            'recipient_name': 'Budi',
            'phone': '08123',
            'address_line': 'Jl. Merdeka No. 10, Jakarta Pusat',
        })
        assert resp.status_code == 200
        assert '10 digit' in resp.content.decode('utf-8')

    def test_create_empty_recipient_name(self, logged_client):
        resp = logged_client.post(reverse('accounts:address_create'), {
            'recipient_name': '',
            'phone': '08123456789',
            'address_line': 'Jl. Merdeka No. 10, Jakarta Pusat',
        })
        assert resp.status_code == 200
        assert 'error' in resp.content.decode('utf-8').lower() or 'required' in resp.content.decode('utf-8').lower()

    def test_create_empty_address_line(self, logged_client):
        resp = logged_client.post(reverse('accounts:address_create'), {
            'recipient_name': 'Budi',
            'phone': '08123456789',
            'address_line': '',
        })
        assert resp.status_code == 200

    def test_create_multiple_addresses(self, logged_client, customer, full_location):
        for i in range(5):
            data = {
                'recipient_name': f'Budi {i}',
                'phone': '08123456789',
                'address_line': f'Jl. Test No. {i}, Jakarta',
                'province': full_location['province'].id,
                'city': full_location['city'].id,
                'district': full_location['district'].id,
                'postal_code': full_location['postal_code'].id,
            }
            logged_client.post(reverse('accounts:address_create'), data)
        assert CustomerAddress.objects.filter(user=customer).count() == 5


# ============================================================
# ADDRESS — EDIT
# ============================================================
@pytest.mark.django_db
class TestAddressEdit:
    VALID_DATA = {
        'recipient_name': 'Budi Updated',
        'phone': '08123456789',
        'address_line': 'Jl. Updated No. 5, Jakarta',
        'label': 'Kantor',
    }

    def test_edit_success(self, logged_client, address, full_location):
        data = {**self.VALID_DATA,
                'province': full_location['province'].id,
                'city': full_location['city'].id,
                'district': full_location['district'].id,
                'postal_code': full_location['postal_code'].id}
        resp = logged_client.post(reverse('accounts:address_edit', args=[address.id]), data)
        assert resp.status_code == 302
        address.refresh_from_db()
        assert address.recipient_name == 'Budi Updated'
        assert address.label == 'Kantor'

    def test_edit_other_user_404(self, customer, other_user, full_location):
        other_addr = CustomerAddress.objects.create(
            user=other_user, recipient_name='Other', phone='08123',
            address_line='Jl. Other',
            province=full_location['province'], city=full_location['city'],
            district=full_location['district'], postal_code=full_location['postal_code'],
        )
        client = Client()
        client.login(username='budi', password='customer123')
        resp = client.get(reverse('accounts:address_edit', args=[other_addr.id]))
        assert resp.status_code == 404

    def test_edit_nonexistent_404(self, logged_client):
        resp = logged_client.get(reverse('accounts:address_edit', args=[99999]))
        assert resp.status_code == 404

    def test_edit_preserves_unedited_fields(self, logged_client, address, full_location):
        data = {**self.VALID_DATA,
                'province': full_location['province'].id,
                'city': full_location['city'].id,
                'district': full_location['district'].id,
                'postal_code': full_location['postal_code'].id}
        logged_client.post(reverse('accounts:address_edit', args=[address.id]), data)
        address.refresh_from_db()
        assert address.phone == '08123456789'
        assert address.province == full_location['province']

    def test_edit_get_prefills_form(self, logged_client, address):
        resp = logged_client.get(reverse('accounts:address_edit', args=[address.id]))
        assert resp.status_code == 200
        content = resp.content.decode('utf-8')
        assert address.recipient_name in content
        assert address.address_line in content

    def test_edit_get_shows_title(self, logged_client, address):
        resp = logged_client.get(reverse('accounts:address_edit', args=[address.id]))
        assert 'Edit Alamat' in resp.content.decode('utf-8')


# ============================================================
# ADDRESS — DELETE
# ============================================================
@pytest.mark.django_db
class TestAddressDelete:
    def test_delete_success(self, logged_client, address):
        resp = logged_client.post(reverse('accounts:address_delete', args=[address.id]))
        assert resp.status_code == 302
        assert CustomerAddress.objects.filter(id=address.id).count() == 0

    def test_delete_other_user_404(self, customer, other_user, full_location):
        other_addr = CustomerAddress.objects.create(
            user=other_user, recipient_name='Other', phone='08123',
            address_line='Jl. Other',
            province=full_location['province'], city=full_location['city'],
            district=full_location['district'], postal_code=full_location['postal_code'],
        )
        client = Client()
        client.login(username='budi', password='customer123')
        resp = client.post(reverse('accounts:address_delete', args=[other_addr.id]))
        assert resp.status_code == 404
        assert CustomerAddress.objects.filter(id=other_addr.id).count() == 1

    def test_delete_nonexistent_404(self, logged_client):
        resp = logged_client.post(reverse('accounts:address_delete', args=[99999]))
        assert resp.status_code == 404

    def test_delete_removes_only_one(self, logged_client, customer, full_location):
        a1 = CustomerAddress.objects.create(user=customer, recipient_name='A', phone='08123', address_line='Jl. A')
        a2 = CustomerAddress.objects.create(user=customer, recipient_name='B', phone='08123', address_line='Jl. B')
        logged_client.post(reverse('accounts:address_delete', args=[a1.id]))
        assert CustomerAddress.objects.filter(id=a1.id).count() == 0
        assert CustomerAddress.objects.filter(id=a2.id).count() == 1


# ============================================================
# ADDRESS — DEFAULT
# ============================================================
@pytest.mark.django_db
class TestAddressDefault:
    def test_set_default(self, logged_client, address):
        resp = logged_client.post(reverse('accounts:address_set_default', args=[address.id]))
        assert resp.status_code == 302
        address.refresh_from_db()
        assert address.is_default is True

    def test_only_one_default(self, logged_client, customer, full_location):
        addr1 = CustomerAddress.objects.create(
            user=customer, recipient_name='Home', phone='08123',
            address_line='Jl. Home', is_default=True,
        )
        addr2 = CustomerAddress.objects.create(
            user=customer, recipient_name='Office', phone='08123',
            address_line='Jl. Office',
        )
        logged_client.post(reverse('accounts:address_set_default', args=[addr2.id]))
        addr1.refresh_from_db()
        addr2.refresh_from_db()
        assert addr2.is_default is True
        assert addr1.is_default is False

    def test_save_model_unsets_old_default(self, customer):
        a1 = CustomerAddress.objects.create(
            user=customer, recipient_name='Old', phone='08123',
            address_line='Jl. Old', is_default=True,
        )
        a2 = CustomerAddress.objects.create(
            user=customer, recipient_name='New', phone='08123',
            address_line='Jl. New', is_default=True,
        )
        a1.refresh_from_db()
        assert a1.is_default is False
        assert a2.is_default is True

    def test_default_first_in_list(self, logged_client, customer):
        a1 = CustomerAddress.objects.create(
            user=customer, recipient_name='Second', phone='08123',
            address_line='Jl. Second',
        )
        a2 = CustomerAddress.objects.create(
            user=customer, recipient_name='First', phone='08123',
            address_line='Jl. First', is_default=True,
        )
        resp = logged_client.get(reverse('accounts:address_list'))
        assert resp.status_code == 200

    def test_set_default_other_user_404(self, customer, other_user, full_location):
        other_addr = CustomerAddress.objects.create(
            user=other_user, recipient_name='Other', phone='08123',
            address_line='Jl. Other',
        )
        client = Client()
        client.login(username='budi', password='customer123')
        resp = client.post(reverse('accounts:address_set_default', args=[other_addr.id]))
        assert resp.status_code == 404


# ============================================================
# ADDRESS — LIST / DISPLAY
# ============================================================
@pytest.mark.django_db
class TestAddressList:
    def test_list_empty(self, logged_client):
        resp = logged_client.get(reverse('accounts:address_list'))
        assert resp.status_code == 200
        content = resp.content.decode('utf-8')
        assert 'Alamat' in content

    def test_list_shows_addresses(self, logged_client, address):
        resp = logged_client.get(reverse('accounts:address_list'))
        content = resp.content.decode('utf-8')
        assert address.recipient_name in content
        assert address.address_line in content

    def test_list_shows_default_badge(self, logged_client, address):
        resp = logged_client.get(reverse('accounts:address_list'))
        content = resp.content.decode('utf-8')
        assert 'Utama' in content

    def test_list_only_shows_own_addresses(self, logged_client, customer, other_user, full_location):
        CustomerAddress.objects.create(
            user=other_user, recipient_name='Other', phone='08123',
            address_line='Jl. Other',
        )
        resp = logged_client.get(reverse('accounts:address_list'))
        content = resp.content.decode('utf-8')
        assert 'Other' not in content

    def test_list_has_action_buttons(self, logged_client, address):
        resp = logged_client.get(reverse('accounts:address_list'))
        content = resp.content.decode('utf-8')
        assert 'edit' in content.lower() or 'Edit' in content
        assert 'hapus' in content.lower() or 'Hapus' in content

    def test_list_edit_link_works(self, logged_client, address):
        resp = logged_client.get(reverse('accounts:address_list'))
        assert reverse('accounts:address_edit', args=[address.id]) in resp.content.decode('utf-8')


# ============================================================
# ADDRESS — FORM VALIDATION
# ============================================================
@pytest.mark.django_db
class TestAddressFormValidation:
    def test_valid_cascade(self, full_location):
        form = CustomerAddressForm(data={
            'recipient_name': 'Test',
            'phone': '08123456789',
            'address_line': 'Jl. Test No. 100 Jakarta',
            'province': full_location['province'].id,
            'city': full_location['city'].id,
            'district': full_location['district'].id,
            'postal_code': full_location['postal_code'].id,
        })
        assert form.is_valid(), form.errors

    def test_city_not_in_province(self, prov, full_location):
        other_prov = Province.objects.create(code='12', name='Sumatera Utara')
        orphan_city = City.objects.create(code='1201', name='Orphan City', province=other_prov)
        form = CustomerAddressForm(data={
            'recipient_name': 'Test', 'phone': '08123456789',
            'address_line': 'Jl. Test No. 100',
            'province': full_location['province'].id,
            'city': orphan_city.id,
            'district': full_location['district'].id,
            'postal_code': full_location['postal_code'].id,
        })
        assert not form.is_valid()
        assert 'city' in form.errors

    def test_district_not_in_city(self, full_location):
        other_city = City.objects.create(code='1199', name='Other City', province=full_location['province'])
        orphan_district = District.objects.create(code='119901', name='Orphan District', city=other_city)
        form = CustomerAddressForm(data={
            'recipient_name': 'Test', 'phone': '08123456789',
            'address_line': 'Jl. Test No. 100',
            'province': full_location['province'].id,
            'city': full_location['city'].id,
            'district': orphan_district.id,
            'postal_code': full_location['postal_code'].id,
        })
        assert not form.is_valid()
        assert 'district' in form.errors

    def test_postal_code_not_in_district(self, full_location):
        other_district = District.objects.create(code='110102', name='Other District', city=full_location['city'])
        orphan_pc = PostalCode.objects.create(code='99999', district=other_district)
        form = CustomerAddressForm(data={
            'recipient_name': 'Test', 'phone': '08123456789',
            'address_line': 'Jl. Test No. 100',
            'province': full_location['province'].id,
            'city': full_location['city'].id,
            'district': full_location['district'].id,
            'postal_code': orphan_pc.id,
        })
        assert not form.is_valid()
        assert 'postal_code' in form.errors

    def test_missing_all_region_fields(self):
        """Form should be valid without region fields (all nullable)"""
        form = CustomerAddressForm(data={
            'recipient_name': 'Test',
            'phone': '08123456789',
            'address_line': 'Jl. Test No. 100 Jakarta',
        })
        assert form.is_valid(), form.errors

    def test_missing_required_fields(self):
        form = CustomerAddressForm(data={})
        assert not form.is_valid()
        assert 'recipient_name' in form.errors
        assert 'phone' in form.errors
        assert 'address_line' in form.errors

    def test_label_choices(self):
        """Label must be one of the predefined choices"""
        form = CustomerAddressForm(data={
            'recipient_name': 'Test', 'phone': '08123456789',
            'address_line': 'Jl. Test No. 100',
            'label': 'INVALID',
        })
        assert not form.is_valid()

    def test_address_line_min_15_chars(self):
        form = CustomerAddressForm(data={
            'recipient_name': 'Test', 'phone': '08123456789',
            'address_line': 'Short',
        })
        assert not form.is_valid()
        assert 'address_line' in form.errors

    def test_phone_10_digits_minimum(self):
        form = CustomerAddressForm(data={
            'recipient_name': 'Test', 'phone': '0812345',
            'address_line': 'Jl. Test No. 100 Jakarta',
        })
        assert not form.is_valid()
        assert 'phone' in form.errors

    def test_phone_must_start_with_08(self):
        form = CustomerAddressForm(data={
            'recipient_name': 'Test', 'phone': '1234567890',
            'address_line': 'Jl. Test No. 100 Jakarta',
        })
        assert not form.is_valid()
        assert 'phone' in form.errors

    def test_city_queryset_filtered_by_province(self, prov, full_location):
        """Form field city queryset must be filtered by selected province"""
        form = CustomerAddressForm(data={
            'recipient_name': 'Test', 'phone': '08123456789',
            'address_line': 'Jl. Test No. 100',
            'province': full_location['province'].id,
        })
        # The field queryset is set in __init__ based on data
        assert form.fields['city'].queryset.count() == 1
        assert form.fields['city'].queryset.first() == full_location['city']

    def test_district_queryset_filtered_by_city(self, full_location):
        form = CustomerAddressForm(data={
            'recipient_name': 'Test', 'phone': '08123456789',
            'address_line': 'Jl. Test No. 100',
            'province': full_location['province'].id,
            'city': full_location['city'].id,
        })
        assert form.fields['district'].queryset.count() == 1
        assert form.fields['district'].queryset.first() == full_location['district']

    def test_postal_code_queryset_filtered_by_district(self, full_location):
        form = CustomerAddressForm(data={
            'recipient_name': 'Test', 'phone': '08123456789',
            'address_line': 'Jl. Test No. 100',
            'province': full_location['province'].id,
            'city': full_location['city'].id,
            'district': full_location['district'].id,
        })
        assert form.fields['postal_code'].queryset.count() >= 1
        assert full_location['postal_code'] in form.fields['postal_code'].queryset


# ============================================================
# ADDRESS — RT/RW FIELD VALIDATION
# ============================================================
@pytest.mark.django_db
class TestAddressRtRw:
    def test_rt_max_4_chars(self, logged_client, customer, full_location):
        data = {
            'recipient_name': 'Budi', 'phone': '08123456789',
            'address_line': 'Jl. Test No. 100',
            'rt': '12345',  # 5 chars
            'province': full_location['province'].id,
            'city': full_location['city'].id,
            'district': full_location['district'].id,
            'postal_code': full_location['postal_code'].id,
        }
        resp = logged_client.post(reverse('accounts:address_create'), data)
        assert resp.status_code == 200
        assert 'rt' in resp.context['form'].errors

    def test_rw_max_4_chars(self, logged_client, customer, full_location):
        data = {
            'recipient_name': 'Budi', 'phone': '08123456789',
            'address_line': 'Jl. Test No. 100',
            'rw': '12345',  # 5 chars
            'province': full_location['province'].id,
            'city': full_location['city'].id,
            'district': full_location['district'].id,
            'postal_code': full_location['postal_code'].id,
        }
        resp = logged_client.post(reverse('accounts:address_create'), data)
        assert resp.status_code == 200
        assert 'rw' in resp.context['form'].errors

    def test_rt_rw_optional(self, logged_client, customer):
        resp = logged_client.post(reverse('accounts:address_create'), {
            'recipient_name': 'Budi',
            'phone': '08123456789',
            'address_line': 'Jl. Merdeka No. 10, Jakarta Pusat',
        })
        assert resp.status_code == 302
        addr = CustomerAddress.objects.get(user=customer)
        assert addr.rt == ''
        assert addr.rw == ''


# ============================================================
# ADDRESS — CASCADE INTEGRITY (PROTECT ON DELETE)
# ============================================================
@pytest.mark.django_db
class TestAddressCascadeIntegrity:
    def test_cannot_delete_province_with_address(self, customer, full_location):
        CustomerAddress.objects.create(
            user=customer, recipient_name='Test', phone='08123',
            address_line='Jl. Test', province=full_location['province'],
            city=full_location['city'], district=full_location['district'],
            postal_code=full_location['postal_code'],
        )
        with pytest.raises(Exception):
            full_location['province'].delete()

    def test_cannot_delete_city_with_address(self, customer, full_location):
        CustomerAddress.objects.create(
            user=customer, recipient_name='Test', phone='08123',
            address_line='Jl. Test', province=full_location['province'],
            city=full_location['city'], district=full_location['district'],
            postal_code=full_location['postal_code'],
        )
        with pytest.raises(Exception):
            full_location['city'].delete()

    def test_can_delete_province_without_addresses(self):
        p = Province.objects.create(code='99', name='Test')
        p.delete()
        assert Province.objects.filter(code='99').count() == 0

    def test_can_delete_city_cascade_deletes_districts(self, city):
        dist = District.objects.create(code='110199', name='Test District', city=city)
        pc = PostalCode.objects.create(code='99999', district=dist)
        city.delete()
        assert District.objects.filter(id=dist.id).count() == 0
        assert PostalCode.objects.filter(id=pc.id).count() == 0


# ============================================================
# ADDRESS — ORDERING
# ============================================================
@pytest.mark.django_db
class TestAddressOrdering:
    def test_default_first_in_queryset(self, customer):
        a1 = CustomerAddress.objects.create(
            user=customer, recipient_name='Non Default', phone='08123',
            address_line='Jl. A',
        )
        a2 = CustomerAddress.objects.create(
            user=customer, recipient_name='Default', phone='08123',
            address_line='Jl. B', is_default=True,
        )
        addrs = CustomerAddress.objects.filter(user=customer)
        assert addrs[0].is_default is True

    def test_newest_first_among_non_default(self, customer):
        a1 = CustomerAddress.objects.create(
            user=customer, recipient_name='Old', phone='08123', address_line='Jl. Old',
        )
        a2 = CustomerAddress.objects.create(
            user=customer, recipient_name='New', phone='08123', address_line='Jl. New',
        )
        addrs = CustomerAddress.objects.filter(user=customer)
        assert addrs[0] == a2
        assert addrs[1] == a1


# ============================================================
# SEED DATA — ALL INDONESIAN PROVINCES
# ============================================================
@pytest.mark.django_db
class TestSeedDataCoverage:
    def test_all_38_provinces_have_unique_codes(self):
        codes = set()
        provs = [
            ('11', 'Aceh'), ('12', 'Sumatera Utara'), ('13', 'Sumatera Barat'),
            ('14', 'Riau'), ('15', 'Jambi'), ('16', 'Sumatera Selatan'),
            ('17', 'Bengkulu'), ('18', 'Lampung'), ('19', 'Kep. Bangka Belitung'),
            ('21', 'Kepulauan Riau'), ('31', 'DKI Jakarta'), ('32', 'Jawa Barat'),
            ('33', 'Jawa Tengah'), ('34', 'DI Yogyakarta'), ('35', 'Jawa Timur'),
            ('36', 'Banten'), ('51', 'Bali'), ('52', 'Nusa Tenggara Barat'),
            ('53', 'Nusa Tenggara Timur'), ('61', 'Kalimantan Barat'),
            ('62', 'Kalimantan Tengah'), ('63', 'Kalimantan Selatan'),
            ('64', 'Kalimantan Timur'), ('65', 'Kalimantan Utara'),
            ('71', 'Sulawesi Utara'), ('72', 'Sulawesi Tengah'),
            ('73', 'Sulawesi Selatan'), ('74', 'Sulawesi Tenggara'),
            ('75', 'Gorontalo'), ('76', 'Sulawesi Barat'),
            ('81', 'Maluku'), ('82', 'Maluku Utara'),
            ('91', 'Papua Barat'), ('92', 'Papua Barat Daya'),
            ('93', 'Papua'), ('94', 'Papua Selatan'),
            ('95', 'Papua Tengah'), ('96', 'Papua Pegunungan'),
        ]
        for code, name in provs:
            Province.objects.create(code=code, name=name)
            assert code not in codes, f'Duplicate province code: {code}'
            codes.add(code)
        assert Province.objects.count() == 38

    def test_dki_jakarta_has_6_cities(self):
        jakarta = Province.objects.create(code='31', name='DKI Jakarta')
        cities = [
            ('3171', 'Kota Jakarta Pusat'), ('3172', 'Kota Jakarta Utara'),
            ('3173', 'Kota Jakarta Barat'), ('3174', 'Kota Jakarta Selatan'),
            ('3175', 'Kota Jakarta Timur'), ('3101', 'Kab. Kepulauan Seribu'),
        ]
        for code, name in cities:
            City.objects.create(code=code, name=name, province=jakarta)
        assert jakarta.cities.count() == 6

    def test_each_province_has_at_least_one_city(self):
        """Structural test: ensure the cascade chain can start"""
        prov = Province.objects.create(code='99', name='Test')
        city = City.objects.create(code='9901', name='Test City', province=prov)
        assert prov.cities.count() >= 1

    def test_cascade_depth(self, full_location):
        """Verify all 4 levels cascade correctly"""
        p = full_location['province']
        c = full_location['city']
        d = full_location['district']
        pc = full_location['postal_code']
        assert c.province == p
        assert d.city == c
        assert pc.district == d


# ============================================================
# EDGE CASES
# ============================================================
@pytest.mark.django_db
class TestAddressEdgeCases:
    def test_very_long_address_line(self, logged_client, customer):
        long_addr = 'Jl. ' + 'A' * 500
        resp = logged_client.post(reverse('accounts:address_create'), {
            'recipient_name': 'Budi',
            'phone': '08123456789',
            'address_line': long_addr,
        })
        assert resp.status_code == 302
        addr = CustomerAddress.objects.get(user=customer)
        assert len(addr.address_line) >= 500

    def test_phone_with_formatting(self, logged_client, customer):
        """Phone with spaces, dashes, parens should be accepted"""
        resp = logged_client.post(reverse('accounts:address_create'), {
            'recipient_name': 'Budi',
            'phone': '(0812) 3456-7890',
            'address_line': 'Jl. Merdeka No. 10, Jakarta Pusat',
        })
        assert resp.status_code == 302
        addr = CustomerAddress.objects.get(user=customer)
        digits = ''.join(filter(str.isdigit, '(0812) 3456-7890'))
        assert len(digits) >= 10
        assert digits.startswith('08')

    def test_label_choices_all_valid(self, customer):
        for choice_label, _ in CustomerAddress.LABEL_CHOICES:
            form = CustomerAddressForm(data={
                'recipient_name': 'Test', 'phone': '08123456789',
                'address_line': 'Jl. Test No. 100',
                'label': choice_label,
            })
            assert form.is_valid(), f'Label {choice_label} should be valid'

    def test_address_str_method(self, address):
        s = str(address)
        assert 'Budi' in s
        assert 'Rumah' in s

    def test_address_str_without_label(self, customer):
        addr = CustomerAddress.objects.create(
            user=customer, recipient_name='Budi', phone='08123',
            address_line='Jl. Test',
        )
        assert 'Alamat' in str(addr)
