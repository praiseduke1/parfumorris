import json
import logging
import time

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class KomerceAPIError(Exception):
    def __init__(self, message, status_code=None, response_data=None):
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class KomerceClient:
    BASE_URL = 'https://rajaongkir.komerce.id/api/v1'
    TIMEOUT = 15

    def __init__(self, api_key=None, base_url=None, timeout=None):
        self.api_key = api_key or getattr(settings, 'KOMERCE_API_KEY', '')
        self.base_url = (base_url or getattr(settings, 'KOMERCE_BASE_URL', None) or self.BASE_URL).rstrip('/')
        self.timeout = timeout or self.TIMEOUT

    def _headers(self):
        return {
            'key': self.api_key,
            'Accept': 'application/json',
        }

    def _log_request(self, method, url, headers, data, params, body_for_log):
        log_lines = [
            f'[RAJAONGKIR REQUEST]',
            f'  Method    : {method.upper()}',
            f'  URL       : {url}',
        ]
        if params:
            log_lines.append(f'  Params    : {json.dumps(params, default=str)}')
        safe_headers = {k: v for k, v in headers.items() if k.lower() != 'key'}
        log_lines.append(f'  Headers   : {json.dumps(safe_headers, default=str)}')
        log_lines.append(f'  API Key   : {self.api_key[:6]}...{self.api_key[-4:] if len(self.api_key) > 10 else ""}')
        if body_for_log:
            log_lines.append(f'  Body      : {body_for_log}')
        logger.info('\n'.join(log_lines))

    def _log_response(self, resp, elapsed, result=None):
        log_lines = [
            f'[RAJAONGKIR RESPONSE]',
            f'  Status    : {resp.status_code}',
            f'  Time      : {elapsed:.2f}s',
            f'  Headers   : {json.dumps(dict(resp.headers), default=str)[:500]}',
        ]
        if result is not None:
            log_lines.append(f'  Body      : {json.dumps(result, default=str, indent=2)[:3000]}')
        else:
            log_lines.append(f'  Body      : {resp.text[:2000]}')
        logger.info('\n'.join(log_lines))

    def _request(self, method, path, data=None, params=None, use_form_urlencoded=False):
        url = f'{self.base_url}/{path.lstrip("/")}'
        headers = self._headers()
        start = time.time()

        body_for_log = None
        if data:
            if use_form_urlencoded:
                body_for_log = '&'.join(f'{k}={v}' for k, v in data.items())
            else:
                body_for_log = json.dumps(data, default=str)

        self._log_request(method, url, headers, data, params, body_for_log)

        try:
            if use_form_urlencoded:
                headers['Content-Type'] = 'application/x-www-form-urlencoded'

            MAX_RETRIES = 3
            RETRY_DELAY = 1

            for attempt in range(MAX_RETRIES):
                try:
                    resp = requests.request(
                        method=method,
                        url=url,
                        headers=headers,
                        data=data if use_form_urlencoded else None,
                        json=data if (method.upper() == 'POST' and not use_form_urlencoded) else None,
                        params=params if (method.upper() == 'GET') else None,
                        timeout=self.timeout,
                    )
                    break
                except (requests.ConnectionError, requests.Timeout) as e:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY * (2 ** attempt))
                        logger.warning(f'Retry {attempt + 1}/{MAX_RETRIES} after error: {e}')
                        continue
                    raise
            elapsed = time.time() - start

            try:
                result = resp.json()
            except (json.JSONDecodeError, ValueError):
                self._log_response(resp, elapsed)
                logger.error('RajaOngkir invalid JSON response: %s', resp.text[:500])
                raise KomerceAPIError(
                    'Response tidak valid dari server pengiriman',
                    status_code=resp.status_code,
                )

            self._log_response(resp, elapsed, result)

            meta = result.get('meta', {})
            api_status = meta.get('status', '')
            api_code = meta.get('code', resp.status_code)

            if api_status == 'error' or api_code != 200:
                msg = meta.get('message', 'Unknown error')
                if api_code == 401:
                    raise KomerceAPIError(
                        f'RajaOngkir: API Key tidak valid (HTTP 401). '
                        f'Pesan: {msg}. Periksa KOMERCE_API_KEY di file .env',
                        status_code=api_code, response_data=result,
                    )
                elif api_code == 403:
                    raise KomerceAPIError(
                        f'RajaOngkir: Akses ditolak (HTTP 403). {msg}',
                        status_code=api_code, response_data=result,
                    )
                elif api_code == 404:
                    raise KomerceAPIError(
                        f'RajaOngkir: Data tidak ditemukan (HTTP 404). {msg}',
                        status_code=api_code, response_data=result,
                    )
                elif api_code == 422:
                    raise KomerceAPIError(
                        f'RajaOngkir: Parameter tidak valid (HTTP 422). {msg}',
                        status_code=api_code, response_data=result,
                    )
                elif api_code == 429:
                    raise KomerceAPIError(
                        f'RajaOngkir: Kuota harian API habis (HTTP 429). {msg}. '
                        f'Tunggu hingga kuota reset atau perbarui API key.',
                        status_code=api_code, response_data=result,
                    )
                elif api_code >= 500:
                    raise KomerceAPIError(
                        f'RajaOngkir: Server error (HTTP {api_code}). {msg}',
                        status_code=api_code, response_data=result,
                    )
                raise KomerceAPIError(
                    f'RajaOngkir: {msg} (HTTP {api_code})',
                    status_code=api_code, response_data=result,
                )

            return result

        except requests.ConnectionError as e:
            logger.error(
                '[RAJAONGKIR CONNECTION ERROR] URL=%s, Error=%s',
                url, e,
            )
            raise KomerceAPIError('Gagal terhubung ke server pengiriman. Periksa koneksi internet.')
        except requests.Timeout as e:
            logger.error(
                '[RAJAONGKIR TIMEOUT] URL=%s, Timeout=%ds, Error=%s',
                url, self.timeout, e,
            )
            raise KomerceAPIError('Server pengiriman tidak merespon. Coba lagi.')
        except KomerceAPIError:
            raise
        except Exception as e:
            logger.error('RajaOngkir unexpected error: %s', e, exc_info=True)
            raise KomerceAPIError('Terjadi kesalahan saat menghitung ongkir')

    def search_destination(self, query, limit=5):
        return self._request(
            'GET', 'destination/domestic-destination',
            params={'search': query, 'limit': limit},
        )

    def get_cost(self, origin, destination, weight, courier=None):
        path = 'calculate/domestic-cost'
        data = {
            'origin': origin,
            'destination': destination,
            'weight': weight,
        }
        if courier:
            data['courier'] = courier

        return self._request('POST', path, data, use_form_urlencoded=True)


def get_cached_cost(origin, destination, weight, courier):
    cache_key = f'shipping:cost:{origin}:{destination}:{weight}:{courier}'
    cached = cache.get(cache_key)
    if cached is not None:
        logger.debug('Shipping cache HIT: %s', cache_key)
        return cached

    logger.debug('Shipping cache MISS: %s', cache_key)
    client = KomerceClient()
    try:
        result = client.get_cost(origin, destination, weight, courier)
    except KomerceAPIError:
        raise

    from ..models import ShippingConfig
    config = ShippingConfig.get_config()
    ttl = config.cache_ttl * 60
    cache.set(cache_key, result, ttl)
    return result


def clear_shipping_cache(origin=None, destination=None, weight=None, courier=None):
    if origin and destination and weight:
        key = f'shipping:cost:{origin}:{destination}:{weight}:{courier or "*"}'
        cache.delete(key)
    else:
        cache.delete_pattern('shipping:cost:*')


def lookup_komerce_id(district):
    from ..models import ShippingConfig
    if district.komerce_id:
        logger.info('Using cached komerce_id=%s for district %s', district.komerce_id, district.name)
        return district.komerce_id

    query = f'{district.name} {district.city.name}'
    logger.info('Looking up Komerce ID for district: %s (query=%s)', district.name, query)

    client = KomerceClient()
    try:
        result = client.search_destination(query)
    except KomerceAPIError as e:
        logger.warning('Search destination failed for %s: %s', query, e)
        raise

    data = result.get('data', [])
    if not data:
        raise KomerceAPIError(f'Kecamatan "{district.name}" tidak ditemukan di RajaOngkir')

    target_district = district.name.upper()
    target_city = district.city.name.upper()

    for item in data:
        item_district = (item.get('district_name') or '').upper()
        item_city = (item.get('city_name') or '').upper()
        if item_district == target_district and item_city == target_city:
            kid = item['id']
            District_model = district.__class__
            District_model.objects.filter(pk=district.pk).update(komerce_id=kid)
            district.komerce_id = kid
            logger.info('Found and cached Komerce ID %s for %s', kid, district.name)
            return kid

    for item in data:
        item_district = (item.get('district_name') or '').upper()
        item_city = (item.get('city_name') or '').upper()
        if item_district == target_district:
            kid = item['id']
            District_model = district.__class__
            District_model.objects.filter(pk=district.pk).update(komerce_id=kid)
            district.komerce_id = kid
            logger.info('Found (city-fallback) Komerce ID %s for %s', kid, district.name)
            return kid

    raise KomerceAPIError(
        f'Kecamatan "{district.name}" di {district.city.name} tidak ditemukan di RajaOngkir. '
        'Coba perbarui data kecamatan.'
    )


def lookup_komerce_origin_id():
    from ..models import ShippingConfig
    config = ShippingConfig.get_config()

    if config.komerce_origin_id:
        return config.komerce_origin_id

    query = f'{config.origin_district} {config.origin_city}'
    logger.info('Looking up Komerce origin ID: %s', query)

    client = KomerceClient()
    try:
        result = client.search_destination(query)
    except KomerceAPIError as e:
        logger.warning('Search origin failed: %s', e)
        raise

    data = result.get('data', [])
    if not data:
        raise KomerceAPIError(f'Lokasi asal "{config.origin_district}" tidak ditemukan di RajaOngkir')

    target_district = config.origin_district.upper()
    target_city = config.origin_city.upper()

    for item in data:
        item_district = (item.get('district_name') or '').upper()
        item_city = (item.get('city_name') or '').upper()
        if item_district == target_district and item_city == target_city:
            kid = item['id']
            ShippingConfig.objects.filter(pk=config.pk).update(komerce_origin_id=kid)
            config.komerce_origin_id = kid
            logger.info('Found and cached origin Komerce ID %s', kid)
            return kid

    kid = data[0]['id']
    ShippingConfig.objects.filter(pk=config.pk).update(komerce_origin_id=kid)
    config.komerce_origin_id = kid
    logger.info('Found origin Komerce ID %s (first match)', kid)
    return kid
