from django.core.cache import cache
from django.db import models


class Province(models.Model):
    code = models.CharField('Kode Provinsi', max_length=2, unique=True)
    name = models.CharField('Provinsi', max_length=100)

    class Meta:
        verbose_name = 'Provinsi'
        verbose_name_plural = 'Provinsi'
        ordering = ['name']

    def __str__(self):
        return self.name


class City(models.Model):
    province = models.ForeignKey(
        Province, on_delete=models.CASCADE, related_name='cities',
        verbose_name='Provinsi',
    )
    code = models.CharField('Kode Kota', max_length=5, unique=True)
    name = models.CharField('Kota/Kabupaten', max_length=100)

    class Meta:
        verbose_name = 'Kota/Kabupaten'
        verbose_name_plural = 'Kota/Kabupaten'
        ordering = ['name']
        indexes = [models.Index(fields=['province'])]

    def __str__(self):
        return self.name


class District(models.Model):
    city = models.ForeignKey(
        City, on_delete=models.CASCADE, related_name='districts',
        verbose_name='Kota/Kabupaten',
    )
    code = models.CharField('Kode Kecamatan', max_length=8, unique=True)
    name = models.CharField('Kecamatan', max_length=100)
    komerce_id = models.PositiveIntegerField('ID Komerce', null=True, blank=True, unique=True)

    class Meta:
        verbose_name = 'Kecamatan'
        verbose_name_plural = 'Kecamatan'
        ordering = ['name']
        indexes = [models.Index(fields=['city'])]

    def __str__(self):
        return self.name


class PostalCode(models.Model):
    district = models.ForeignKey(
        District, on_delete=models.CASCADE, related_name='postal_codes',
        verbose_name='Kecamatan',
    )
    code = models.CharField('Kode Pos', max_length=5)

    class Meta:
        verbose_name = 'Kode Pos'
        verbose_name_plural = 'Kode Pos'
        ordering = ['code']
        unique_together = [['district', 'code']]
        indexes = [models.Index(fields=['district'])]

    def __str__(self):
        return self.code


def get_cached_provinces():
    key = 'regions:provinces'
    data = cache.get(key)
    if data is None:
        data = list(Province.objects.values('id', 'code', 'name'))
        cache.set(key, data, 86400)
    return data


def get_cached_cities(province_id):
    key = f'regions:cities:{province_id}'
    data = cache.get(key)
    if data is None:
        data = list(City.objects.filter(province_id=province_id).values('id', 'code', 'name'))
        cache.set(key, data, 86400)
    return data


def get_cached_districts(city_id):
    key = f'regions:districts:{city_id}'
    data = cache.get(key)
    if data is None:
        data = list(District.objects.filter(city_id=city_id).values('id', 'code', 'name'))
        cache.set(key, data, 86400)
    return data


def get_cached_postal_codes(district_id):
    key = f'regions:postal_codes:{district_id}'
    data = cache.get(key)
    if data is None:
        data = list(PostalCode.objects.filter(district_id=district_id).values('id', 'code'))
        cache.set(key, data, 86400)
    return data
