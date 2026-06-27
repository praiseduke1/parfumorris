import os, sys, time, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'parfumoray.settings'
import django
django.setup()

from django.test.utils import setup_test_environment, teardown_test_environment
from django.test.runner import DiscoverRunner
from django.test import Client, override_settings
from django.db import connection
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth.models import User
from apps.products.models import Product, Category, Brand, FragranceFamily, FragranceNote, ProductVariant
from apps.carts.models import Cart, CartItem
from apps.accounts.models import CustomerAddress

old_config = DiscoverRunner().setup_databases()

# Avoid DisallowedHost for testserver
import django.conf
django.conf.settings.ALLOWED_HOSTS.append('testserver')

host_kw = {'HTTP_HOST': 'testserver', 'SERVER_NAME': 'testserver'}

def measure(label, func):
    cache.clear()
    connection.queries_log.clear()
    q_start = len(connection.queries)
    t_start = time.perf_counter()
    resp = func()
    t_end = time.perf_counter()
    q_end = len(connection.queries)
    status = resp.status_code
    time_ms = round((t_end - t_start) * 1000, 2)
    queries = q_end - q_start
    print(f'{label:40s} {status:4d}  {time_ms:8.2f}ms  {queries:3d} queries')
    return {'page': label, 'status': status, 'time_ms': time_ms, 'queries': queries}


def g(url, **kw):
    kwargs = {**host_kw, **kw}
    return c.get(url, **kwargs)

results = []

cat = Category.objects.create(name='Test Cat')
brand = Brand.objects.create(name='Test Brand')
family = FragranceFamily.objects.create(name='Test Fam')
note = FragranceNote.objects.create(name='Test Note', note_type='TOP')
for i in range(12):
    p = Product.objects.create(
        name=f'TP {i}', slug=f'tp-{i}', category=cat, brand=brand,
        price=150000, stock=10, is_available=True,
    )
    p.fragrance_families.add(family)
    p.fragrance_notes.add(note)
    ProductVariant.objects.create(product=p, size_ml=50, price=150000, stock=10, sku=f'SKU-{i}')

c = Client()

results.append(measure('Home', lambda: g(reverse('products:home'))))
results.append(measure('Product List', lambda: g(reverse('products:list'))))
results.append(measure('Product List (filtered)', lambda: g(reverse('products:list') + '?gender=men')))
p = Product.objects.filter(is_available=True).first()
results.append(measure('Product Detail', lambda: g(reverse('products:detail', args=[p.slug]))))
results.append(measure('Login', lambda: g(reverse('accounts:login'))))
results.append(measure('Register', lambda: g(reverse('accounts:register'))))
results.append(measure('Fragrance Guide', lambda: g(reverse('products:fragrance_guide'))))
results.append(measure('About', lambda: g(reverse('products:about'))))

u = User.objects.create_user(username='perfuser', password='testpass')
c.force_login(u)
cart = Cart.objects.create(user=u)

results.append(measure('Cart (empty)', lambda: g(reverse('carts:detail'))))

for p_obj in Product.objects.filter(is_available=True)[:3]:
    CartItem.objects.create(cart=cart, product=p_obj, quantity=2)
CustomerAddress.objects.create(user=u, recipient_name='T', phone='081', address_line='J', is_default=True)

results.append(measure('Cart (3 items)', lambda: g(reverse('carts:detail'))))
results.append(measure('Checkout', lambda: g(reverse('orders:create'))))
results.append(measure('Dashboard', lambda: g(reverse('accounts:dashboard'))))

c.logout()
admin = User.objects.create_superuser(username='perfadmin', password='testpass')
c.login(username='perfadmin', password='testpass')
c.cookies['admin_sessionid'] = c.cookies['sessionid'].value

results.append(measure('Admin Login', lambda: g(reverse('admin:login'))))
results.append(measure('Admin Index', lambda: g(reverse('admin:index'))))
results.append(measure('Admin Dashboard', lambda: g(reverse('admin_dashboard'))))

print()
print('--- Summary ---')
header = f'{"Page":40s} {"Status":>6s} {"Time(ms)":>10s} {"Queries":>8s}'
print(header)
print('-' * 66)
for r in results:
    print(f'{r["page"]:40s} {r["status"]:6d} {r["time_ms"]:10.2f} {r["queries"]:8d}')

with open('.benchmarks/query_results.json', 'w') as f:
    json.dump(results, f, indent=2)

DiscoverRunner().teardown_databases(old_config)
