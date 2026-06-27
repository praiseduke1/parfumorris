import logging

from django.http import JsonResponse

from .models import get_cached_provinces, get_cached_cities, get_cached_districts, get_cached_postal_codes

logger = logging.getLogger(__name__)


def api_provinces(request):
    provinces = get_cached_provinces()
    logger.debug('api_provinces: returning %d provinces', len(provinces))
    return JsonResponse(provinces, safe=False)


def api_cities(request):
    province_id = request.GET.get('province_id')
    logger.debug('api_cities: province_id=%s', province_id)
    if not province_id:
        return JsonResponse({'error': 'province_id required'}, status=400)
    cities = get_cached_cities(province_id)
    logger.debug('api_cities: province_id=%s → %d cities', province_id, len(cities))
    return JsonResponse(cities, safe=False)


def api_districts(request):
    city_id = request.GET.get('city_id')
    logger.debug('api_districts: city_id=%s', city_id)
    if not city_id:
        return JsonResponse({'error': 'city_id required'}, status=400)
    districts = get_cached_districts(city_id)
    logger.debug('api_districts: city_id=%s → %d districts', city_id, len(districts))
    return JsonResponse(districts, safe=False)


def api_postal_code(request):
    district_id = request.GET.get('district_id')
    logger.debug('api_postal_code: district_id=%s (type=%s)', district_id, type(district_id).__name__)
    if not district_id:
        logger.warning('api_postal_code: district_id parameter missing')
        return JsonResponse({'error': 'district_id required'}, status=400)

    # Validate district_id is numeric
    try:
        district_id_int = int(district_id)
    except (ValueError, TypeError):
        logger.error('api_postal_code: district_id "%s" is not a valid integer', district_id)
        return JsonResponse({'error': 'district_id must be an integer'}, status=400)

    codes = get_cached_postal_codes(district_id)

    if not codes:
        from .models import District
        district_exists = District.objects.filter(id=district_id_int).exists()
        if not district_exists:
            logger.warning(
                'api_postal_code: district_id=%s not found in database',
                district_id,
            )
        else:
            pc_count = District.objects.get(id=district_id_int).postal_codes.count()
            logger.warning(
                'api_postal_code: district_id=%s exists but has %d postal codes in DB',
                district_id, pc_count,
            )

    logger.debug(
        'api_postal_code: district_id=%s → %d codes returned',
        district_id, len(codes),
    )
    return JsonResponse(codes, safe=False)
