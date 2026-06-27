import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def _can_fallback():
    """Fallback hanya aktif saat DEBUG=True atau ENVIRONMENT=development."""
    env = getattr(settings, 'ENVIRONMENT', '').lower()
    if settings.DEBUG:
        return True
    if env in ('development', 'local', 'dev'):
        return True
    return False


FALLBACK_SERVICES = [
    {
        'courier_code': 'jne',
        'courier_name': 'JNE',
        'courier_logo': 'https://cdn.jsdelivr.net/gh/parfumoray/courier-logos@main/jne.png',
        'service': 'REG',
        'description': 'Layanan Reguler',
        'cost': 18000,
        'etd': '2-3 hari',
        'note': '',
    },
    {
        'courier_code': 'jne',
        'courier_name': 'JNE',
        'courier_logo': 'https://cdn.jsdelivr.net/gh/parfumoray/courier-logos@main/jne.png',
        'service': 'YES',
        'description': 'Yakin Esok Sampai',
        'cost': 32000,
        'etd': '1 hari',
        'note': '',
    },
    {
        'courier_code': 'jnt',
        'courier_name': 'J&T',
        'courier_logo': 'https://cdn.jsdelivr.net/gh/parfumoray/courier-logos@main/jnt.png',
        'service': 'EZ',
        'description': 'Economy',
        'cost': 20000,
        'etd': '2 hari',
        'note': '',
    },
    {
        'courier_code': 'sicepat',
        'courier_name': 'SiCepat',
        'courier_logo': 'https://cdn.jsdelivr.net/gh/parfumoray/courier-logos@main/sicepat.png',
        'service': 'REG',
        'description': 'SiCepat Reguler',
        'cost': 17000,
        'etd': '2-3 hari',
        'note': '',
    },
    {
        'courier_code': 'pos',
        'courier_name': 'POS Indonesia',
        'courier_logo': 'https://cdn.jsdelivr.net/gh/parfumoray/courier-logos@main/pos.png',
        'service': 'Kilat',
        'description': 'POS Kilat',
        'cost': 16000,
        'etd': '3-5 hari',
        'note': '',
    },
]


def get_fallback_services(origin, destination, weight, courier_code=None):
    if not _can_fallback():
        return []

    services = FALLBACK_SERVICES
    if courier_code:
        services = [s for s in services if s['courier_code'] == courier_code]

    services = [dict(s) for s in services]
    services.sort(key=lambda x: x['cost'])

    logger.info(
        '[SHIPPING FALLBACK] Using dummy data. origin=%s, destination=%s, '
        'weight=%d, courier=%s, services=%d',
        origin, destination, weight, courier_code or 'all', len(services),
    )
    return services
