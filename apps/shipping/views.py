import json
import logging
import traceback

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404

import traceback

from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404

from apps.accounts.models import CustomerAddress
from apps.regions.models import District
from apps.core.decorators import customer_required
from .services.komerce import (
    get_cached_cost, KomerceAPIError,
    lookup_komerce_id, lookup_komerce_origin_id,
)
from .services.fallback import get_fallback_services
from .utils import get_cart_total_weight, format_courier_services
from .models import ShippingConfig

logger = logging.getLogger(__name__)


def _build_fallback_response(config, district, weight, courier_code):
    """Return fallback shipping data if in development mode."""
    services = get_fallback_services(
        config.origin_district, config.origin_city,
        weight, courier_code,
    )
    if not services:
        return None
    logger.warning(
        '[SHIPPING FALLBACK] Using dummy data instead of RajaOngkir API. '
        'DEBUG=%s, origin=%s, destination=%s, weight=%d, courier=%s',
        settings.DEBUG, config.origin_district, district.name if district else '?',
        weight, courier_code or 'all',
    )
    dest_name = f'{district.name}, {district.city.name}' if district else '—'
    return JsonResponse({
        'services': services,
        'weight': weight,
        'origin': f'{config.origin_district}, {config.origin_city}',
        'destination': dest_name,
        'is_fallback': True,
        'errors': [],
    })


@login_required
@customer_required
@require_POST
def api_shipping_cost(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    district_id = data.get('district_id')
    if not district_id:
        return JsonResponse({'error': 'Pilih kecamatan terlebih dahulu'}, status=400)

    try:
        district_id = int(district_id)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Kecamatan tidak valid'}, status=400)

    district = get_object_or_404(District, id=district_id)
    config = ShippingConfig.get_config()
    weight = get_cart_total_weight(request.user)

    if weight <= 0:
        weight = config.default_weight

    courier_code = data.get('courier_code', '').strip().lower()
    enabled_couriers = config.get_enabled_couriers()

    if courier_code:
        if courier_code not in enabled_couriers:
            return JsonResponse({'error': f'Kurir "{courier_code}" tidak tersedia'}, status=400)
        enabled_couriers = [courier_code]

    try:
        origin_id = lookup_komerce_origin_id()
    except KomerceAPIError as e:
        logger.error('Failed to lookup origin ID: %s', e)
        fallback = _build_fallback_response(config, district, weight, courier_code)
        if fallback:
            return fallback
        return JsonResponse({
            'error': 'Gagal menentukan lokasi asal pengiriman',
            'detail': str(e),
        }, status=502)

    try:
        dest_id = lookup_komerce_id(district)
    except KomerceAPIError as e:
        logger.error('Failed to lookup destination ID for %s: %s', district.name, e)
        fallback = _build_fallback_response(config, district, weight, courier_code)
        if fallback:
            return fallback
        return JsonResponse({
            'error': 'Gagal menentukan lokasi tujuan pengiriman',
            'detail': str(e),
        }, status=502)

    logger.info(
        '[SHIPPING COST LOOKUP] origin=%s, destination=%s, weight=%d, couriers=%s, '
        'origin_district=%s, origin_city=%s, dest_district=%s, dest_city=%s',
        origin_id, dest_id, weight, enabled_couriers,
        config.origin_district, config.origin_city,
        district.name, district.city.name,
    )

    all_services = []
    errors = []
    is_rate_limited = False

    for courier in enabled_couriers:
        try:
            result = get_cached_cost(origin_id, dest_id, weight, courier)
            services = format_courier_services(result)
            if services:
                logger.info('Courier %s: got %d services', courier, len(services))
            else:
                logger.warning(
                    '[SHIPPING EMPTY] Courier %s: no services returned, '
                    'raw=%s', courier, json.dumps(result, default=str)[:500],
                )
            all_services.extend(services)
        except KomerceAPIError as e:
            if e.status_code == 429:
                is_rate_limited = True
            logger.warning(
                '[SHIPPING API ERROR] Courier=%s, Status=%s, Message=%s, '
                'ResponseData=%s',
                courier, e.status_code, str(e),
                json.dumps(e.response_data, default=str) if e.response_data else 'N/A',
            )
            errors.append({
                'courier': courier,
                'message': str(e),
                'status_code': e.status_code,
                'response_data': e.response_data,
            })
        except Exception as e:
            logger.error(
                '[SHIPPING UNEXPECTED ERROR] Courier=%s, Error=%s',
                courier, e, exc_info=True,
            )
            errors.append({'courier': courier, 'message': 'Terjadi kesalahan'})

    if not all_services and errors:
        logger.error(
            '[SHIPPING ALL FAILED] No services from any courier. '
            'Errors: %s', json.dumps(errors, default=str),
        )

        fallback = _build_fallback_response(config, district, weight, courier_code)
        if fallback:
            return fallback

        error_msg = errors[0]['message']
        if is_rate_limited:
            error_msg = (
                'Kuota harian API RajaOngkir habis. '
                'Silakan coba lagi besok atau hubungi admin untuk memperbarui API key.'
            )
        return JsonResponse({
            'error': error_msg,
            'detail': errors[0]['message'],
            'errors': errors,
        }, status=502)

    all_services.sort(key=lambda x: x['cost'])

    response_data = {
        'services': all_services,
        'weight': weight,
        'origin': f'{config.origin_district}, {config.origin_city}',
        'destination': f'{district.name}, {district.city.name}',
        'is_fallback': False,
        'errors': errors,
    }
    logger.info('Shipping cost response: %d services, %d errors', len(all_services), len(errors))
    return JsonResponse(response_data)


@login_required
@customer_required
@require_POST
def api_select_shipping(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    courier_code = data.get('courier_code')
    service = data.get('service')
    cost = data.get('cost')
    etd = data.get('etd')

    if not all([courier_code, service, cost]):
        return JsonResponse({'error': 'Data pengiriman tidak lengkap'}, status=400)

    request.session['shipping'] = {
        'courier_code': courier_code,
        'service': service,
        'cost': int(cost),
        'etd': etd or '',
    }

    logger.debug('Shipping selected: %s %s Rp%s', courier_code, service, cost)
    return JsonResponse({'ok': True})


@login_required
@customer_required
@require_POST
def api_clear_shipping(request):
    if 'shipping' in request.session:
        del request.session['shipping']
    return JsonResponse({'ok': True})
