from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.http import HttpRequest
from unittest.mock import patch, MagicMock
import json

from apps.products.models import Product, ProductVariant, Category
from apps.carts.models import Cart, CartItem
from apps.accounts.models import CustomerAddress, Profile
from apps.regions.models import Province, City, District, PostalCode
from .models import ShippingConfig
from .utils import get_cart_total_weight, format_courier_services


class WeightCalculationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            price=100000,
            stock=10,
            weight=200,
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size_ml=50,
            price=150000,
            stock=10,
            weight=250,
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart, product=self.product, variant=self.variant, quantity=2,
        )

    def test_total_weight_with_variant(self):
        weight = get_cart_total_weight(self.user)
        self.assertEqual(weight, 500)

    def test_total_weight_without_variant(self):
        self.cart_item.variant = None
        self.cart_item.save()
        weight = get_cart_total_weight(self.user)
        self.assertEqual(weight, 400)

    def test_total_weight_empty_cart(self):
        self.cart_item.delete()
        weight = get_cart_total_weight(self.user)
        self.assertEqual(weight, 0)

    def test_default_weight_when_product_has_no_weight(self):
        self.product.weight = 0
        self.product.save()
        self.cart_item.variant = None
        self.cart_item.save()
        config = ShippingConfig.load()
        weight = get_cart_total_weight(self.user)
        self.assertEqual(weight, 0)


class FormatCourierServicesTests(TestCase):
    def test_format_standard_response(self):
        raw = {
            'rajaongkir': {
                'results': [
                    {
                        'code': 'jne',
                        'name': 'JNE',
                        'costs': [
                            {
                                'service': 'REG',
                                'description': 'Layanan Reguler',
                                'cost': [
                                    {'value': 15000, 'etd': '2-3', 'note': ''}
                                ],
                            }
                        ],
                    }
                ]
            }
        }
        services = format_courier_services(raw)
        self.assertEqual(len(services), 1)
        self.assertEqual(services[0]['courier_code'], 'jne')
        self.assertEqual(services[0]['cost'], 15000)
        self.assertEqual(services[0]['etd'], '2-3 hari')

    def test_empty_response(self):
        self.assertEqual(format_courier_services(None), [])
        self.assertEqual(format_courier_services({}), [])

    def test_multiple_couriers(self):
        raw = {
            'results': [
                {
                    'code': 'jne',
                    'name': 'JNE',
                    'costs': [
                        {'service': 'OKE', 'cost': [{'value': 10000, 'etd': '3-4'}]},
                        {'service': 'REG', 'cost': [{'value': 15000, 'etd': '2-3'}]},
                    ],
                },
                {
                    'code': 'jnt',
                    'name': 'J&T',
                    'costs': [
                        {'service': 'EZ', 'cost': [{'value': 12000, 'etd': '2-3'}]},
                    ],
                },
            ]
        }
        services = format_courier_services(raw)
        self.assertEqual(len(services), 3)
        self.assertEqual(services[0]['cost'], 10000)
        self.assertEqual(services[0]['courier_code'], 'jne')

    def test_rajaongkir_v2_flat_format(self):
        raw = {
            'meta': {'message': 'Success', 'code': 200, 'status': 'success'},
            'data': [
                {'name': 'JNE', 'code': 'jne', 'service': 'CTC', 'description': 'City Courier', 'cost': 8000, 'etd': '3 day'},
                {'name': 'JNE', 'code': 'jne', 'service': 'JTR', 'description': 'Trucking', 'cost': 50000, 'etd': '5 day'},
                {'name': 'SiCepat', 'code': 'sicepat', 'service': 'REG', 'description': 'Reguler', 'cost': 10000, 'etd': '1-2'},
            ]
        }
        services = format_courier_services(raw)
        self.assertEqual(len(services), 3)
        self.assertEqual(services[0]['courier_code'], 'jne')
        self.assertEqual(services[0]['service'], 'CTC')
        self.assertEqual(services[0]['cost'], 8000)
        self.assertEqual(services[0]['etd'], '3 hari')
        self.assertEqual(services[1]['courier_code'], 'sicepat')
        self.assertEqual(services[1]['cost'], 10000)
        self.assertEqual(services[1]['etd'], '1-2 hari')
        self.assertEqual(services[2]['courier_code'], 'jne')
        self.assertEqual(services[2]['cost'], 50000)
        self.assertEqual(services[2]['etd'], '5 hari')


class ShippingConfigTests(TestCase):
    def test_default_config_created(self):
        config = ShippingConfig.load()
        self.assertIsNotNone(config)
        self.assertEqual(config.origin_district, 'Purwokerto')
        self.assertEqual(config.default_weight, 500)
        self.assertEqual(config.cache_ttl, 10)
        self.assertIn('jne', config.get_enabled_couriers())

    def test_singleton_config(self):
        config1 = ShippingConfig.load()
        config2 = ShippingConfig.load()
        self.assertEqual(config1.pk, config2.pk)


class AddressValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='addruser', password='testpass123')
        self.province = Province.objects.create(code='33', name='Jawa Tengah')
        self.city = City.objects.create(province=self.province, code='3302', name='Kabupaten Banyumas')
        self.district = District.objects.create(city=self.city, code='3302010', name='Purwokerto')
        self.postal_code = PostalCode.objects.create(district=self.district, code='53111')

    def test_address_with_district(self):
        addr = CustomerAddress.objects.create(
            user=self.user,
            recipient_name='Test',
            phone='08123456789',
            address_line='Jl. Test No. 1',
            province=self.province,
            city=self.city,
            district=self.district,
            postal_code=self.postal_code,
        )
        self.assertIsNotNone(addr.district)
        self.assertEqual(addr.district.code, '3302010')

    def test_address_without_district(self):
        addr = CustomerAddress.objects.create(
            user=self.user,
            recipient_name='Test',
            phone='08123456789',
            address_line='Jl. Test No. 1',
        )
        self.assertIsNone(addr.district)
