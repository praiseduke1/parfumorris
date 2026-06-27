import logging
import re

from django.db.models import Sum, F, Case, When, Value, IntegerField
from django.contrib.auth.models import User

from apps.products.models import Product, ProductVariant
from apps.carts.models import Cart
from apps.accounts.models import CustomerAddress

logger = logging.getLogger(__name__)


def get_cart_total_weight(user):
    cart = Cart.objects.filter(user=user).first()
    if not cart:
        return 0

    items = cart.items.select_related('product', 'variant').all()
    total = 0

    for item in items:
        if item.variant:
            weight = item.variant.weight
        else:
            weight = item.product.weight
        if not weight or weight <= 0:
            continue
        total += weight * item.quantity

    return total


def get_destination_district(address):
    if not address or not address.district:
        return None
    return address.district.code or str(address.district_id)


def get_courier_logo_url(code):
    from .models import Courier
    defaults = Courier.get_default_couriers()
    info = defaults.get(code)
    if info:
        return info.get('logo', '')
    return ''


def get_courier_name(code):
    from .models import Courier
    info = Courier.get_default_couriers().get(code)
    if info:
        return info['name']
    return code.upper()


import re

def _normalize_etd(etd):
    etd = str(etd).strip().lower()
    if not etd or etd in ('0', '-', ''):
        return ''
    etd = re.sub(r'\bday\b', 'hari', etd)
    etd = re.sub(r'\bdays\b', 'hari', etd)
    etd = re.sub(r'\bh\b', 'hari', etd)
    etd = re.sub(r'\bhari\s*hari\b', 'hari', etd)
    etd = etd.strip()
    if etd and not etd.endswith('hari'):
        etd = f'{etd} hari'
    return etd


def format_courier_services(raw_response):
    if not raw_response:
        return []

    services_data = raw_response.get('data') or raw_response.get('result') or raw_response.get('results') or []

    if not services_data and isinstance(raw_response, list):
        services_data = raw_response

    if not services_data and isinstance(raw_response, dict):
        for key in ('rajaongkir', 'data'):
            val = raw_response.get(key)
            if isinstance(val, dict):
                services_data = val.get('results') or val.get('data') or []
                break

    if not services_data:
        return []

    formatted = []
    for entry in services_data:
        if isinstance(entry, dict) and 'costs' in entry:
            code = entry.get('code', '').lower()
            name = entry.get('name', '')
            logo = get_courier_logo_url(code)

            for service in entry.get('costs', []):
                service_name = service.get('service', '')
                description = service.get('description', '')
                cost_info = service.get('cost', service)
                if isinstance(cost_info, list):
                    cost_info = cost_info[0] if cost_info else {}

                cost_value = cost_info.get('value', cost_info.get('price', 0))
                etd = _normalize_etd(cost_info.get('etd', cost_info.get('estimation', '')))

                if not cost_value:
                    continue

                formatted.append({
                    'courier_code': code,
                    'courier_name': name,
                    'courier_logo': logo,
                    'service': service_name,
                    'description': description or service_name,
                    'cost': int(cost_value),
                    'etd': str(etd),
                    'note': cost_info.get('note', ''),
                })

        elif isinstance(entry, dict) and 'service' in entry:
            code = entry.get('code', '').lower()
            name = get_courier_name(code) or entry.get('name', entry.get('courier_name', code.upper()))
            logo = get_courier_logo_url(code)
            service_name = entry.get('service', '')
            description = entry.get('description', service_name)
            cost_value = entry.get('cost', 0)
            etd = _normalize_etd(entry.get('etd', ''))

            if not cost_value:
                continue

            formatted.append({
                'courier_code': code,
                'courier_name': name,
                'courier_logo': logo,
                'service': service_name,
                'description': description,
                'cost': int(cost_value),
                'etd': str(etd),
                'note': '',
            })

    formatted.sort(key=lambda x: x['cost'])
    return formatted
