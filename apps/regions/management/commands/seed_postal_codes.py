"""
Seed postal codes from the static POSTAL_CODES dictionary.

This is a re-runnable version of the postal code seeding logic extracted
from the original seed_indonesia_regions.py. It matches districts by
(city_code, district_name) and creates PostalCode records.

After running cleanup_duplicate_districts, run this to recreate postal
codes for the correct (new BPS-coded) districts.
"""

import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.regions.models import District, PostalCode

logger = logging.getLogger(__name__)

POSTAL_CODES = {
    '3171': {'Cempaka Putih': '10510', 'Gambir': '10110', 'Johar Baru': '10540',
             'Kemayoran': '10610', 'Menteng': '10310', 'Sawah Besar': '10710',
             'Senen': '10410', 'Tanah Abang': '10210'},
    '3172': {'Cilincing': '14110', 'Kelapa Gading': '14240', 'Koja': '14220',
             'Pademangan': '14410', 'Penjaringan': '14410', 'Tanjung Priok': '14310'},
    '3173': {'Cengkareng': '11710', 'Grogol Petamburan': '11410', 'Kalideres': '11810',
             'Kebon Jeruk': '11510', 'Kembangan': '11610', 'Palmerah': '11410',
             'Taman Sari': '11110', 'Tambora': '11210'},
    '3174': {'Cilandak': '12410', 'Jagakarsa': '12610', 'Kebayoran Baru': '12110',
             'Kebayoran Lama': '12210', 'Mampang Prapatan': '12710', 'Pancoran': '12710',
             'Pasar Minggu': '12510', 'Pesanggrahan': '12310', 'Setia Budi': '12910',
             'Tebet': '12810'},
    '3175': {'Cakung': '13910', 'Cipayung': '13810', 'Ciracas': '13710',
             'Duren Sawit': '13410', 'Jatinegara': '13310', 'Kramat Jati': '13510',
             'Makasar': '13610', 'Matraman': '13110', 'Pasar Rebo': '13710',
             'Pulo Gadung': '13210'},
    '3302': {'Purwokerto Barat': '53133', 'Purwokerto Selatan': '53141',
             'Purwokerto Timur': '53114', 'Purwokerto Utara': '53121',
             'Ajibarang': '53163', 'Banyumas': '53192', 'Baturaden': '53151',
             'Cilongok': '53162', 'Gumelar': '53165', 'Jatilawang': '53174',
             'Kalibagor': '53191', 'Karanglewas': '53133', 'Kebasen': '53172',
             'Kedung Banteng': '53152', 'Kembaran': '53182', 'Kemranjen': '53194',
             'Lumbir': '53177', 'Patikraja': '53171', 'Pekuncen': '53164',
             'Purwojati': '53175', 'Rawalo': '53173', 'Sokaraja': '53181',
             'Somagede': '53193', 'Sumbang': '53183', 'Sumpiuh': '53195',
             'Tambak': '53196', 'Wangon': '53176'},
    '3372': {'Banjarsari': '57131', 'Jebres': '57126', 'Laweyan': '57141',
             'Pasar Kliwon': '57111', 'Serengan': '57151'},
    '3374': {'Banyumanik': '50261', 'Candisari': '50271', 'Gajahmungkur': '50231',
             'Gayamsari': '50161', 'Genuk': '50111', 'Gunungpati': '50221',
             'Mijen': '50211', 'Ngaliyan': '50181', 'Pedurungan': '50191',
             'Semarang Barat': '50141', 'Semarang Selatan': '50241',
             'Semarang Tengah': '50131', 'Semarang Timur': '50121',
             'Semarang Utara': '50171', 'Tembalang': '50271', 'Tugu': '50151'},
    '3515': {'Sidoarjo': '61211', 'Buduran': '61252', 'Candi': '61271',
             'Gedangan': '61254', 'Porong': '61274', 'Krian': '61262',
             'Taman': '61257', 'Waru': '61256', 'Tanggulangin': '61272'},
    '3578': {'Asemrowo': '60182', 'Benowo': '60191', 'Bubutan': '60171',
             'Bulak': '60124', 'Dukuh Pakis': '60125', 'Gayungan': '60231',
             'Genteng': '60241', 'Gubeng': '60281', 'Gunung Anyar': '60294',
             'Jambangan': '60231', 'Karangpilang': '60221', 'Kenjeran': '60121',
             'Krembangan': '60175', 'Lakarsantri': '60211', 'Mulyorejo': '60115',
             'Pabean Cantian': '60161', 'Pakal': '60192', 'Rungkut': '60291',
             'Sambikerep': '60212', 'Sawahan': '60251', 'Semampir': '60151',
             'Simokerto': '60111', 'Sukolilo': '60119', 'Sukomanunggal': '60261',
             'Tambaksari': '60131', 'Tandes': '60181', 'Tegalsari': '60261',
             'Tenggilis Mejoyo': '60291', 'Wiyung': '60228', 'Wonocolo': '60231',
             'Wonokromo': '60241'},
    '3271': {'Bogor Barat': '16114', 'Bogor Selatan': '16132', 'Bogor Tengah': '16121',
             'Bogor Timur': '16141', 'Bogor Utara': '16151', 'Tanah Sereal': '16161'},
    '3273': {'Andir': '40181', 'Antapani': '40291', 'Arcamanik': '40291',
             'Babakan Ciparay': '40222', 'Bandung Kidul': '40261', 'Bandung Kulon': '40212',
             'Bandung Wetan': '40114', 'Batununggal': '40271', 'Bojongloa Kaler': '40231',
             'Bojongloa Kidul': '40238', 'Buahbatu': '40286', 'Cibeunying Kaler': '40122',
             'Cibeunying Kidul': '40126', 'Cicendo': '40172', 'Cidadap': '40143',
             'Coblong': '40131', 'Kiaracondong': '40281', 'Lengkong': '40262',
             'Regol': '40251', 'Sukajadi': '40161', 'Sukasari': '40153',
             'Sumur Bandung': '40111', 'Ujungberung': '40619'},
    '3275': {'Bekasi Barat': '17133', 'Bekasi Selatan': '17141', 'Bekasi Timur': '17111',
             'Bekasi Utara': '17121', 'Jatiasih': '17421', 'Mustikajaya': '17161',
             'Pondokgede': '17411', 'Rawalumbu': '17117'},
    '3276': {'Beji': '16421', 'Cilodong': '16414', 'Cimanggis': '16451',
             'Cinere': '16514', 'Limo': '16511', 'Pancoran Mas': '16431',
             'Sawangan': '16511', 'Sukmajaya': '16412', 'Tapos': '16451'},
    '3674': {'Ciputat': '15411', 'Ciputat Timur': '15412', 'Pamulang': '15417',
             'Pondok Aren': '15221', 'Serpong': '15311', 'Serpong Utara': '15321',
             'Setu': '15315'},
    '5103': {'Kuta': '80361', 'Kuta Selatan': '80361', 'Kuta Utara': '80361'},
    '5171': {'Denpasar Barat': '80119', 'Denpasar Selatan': '80221', 'Denpasar Timur': '80231',
             'Denpasar Utara': '80111'},
    '5271': {'Ampenan': '83111', 'Cakranegara': '83231', 'Mataram': '83121',
             'Selaparang': '83121', 'Sandubaya': '83231', 'Sekarbela': '83127'},
    '5201': {'Gerung': '83363'},
    '6371': {'Banjarmasin Barat': '70114', 'Banjarmasin Selatan': '70241',
             'Banjarmasin Tengah': '70231', 'Banjarmasin Timur': '70231',
             'Banjarmasin Utara': '70121'},
    '6471': {'Balikpapan Barat': '76131', 'Balikpapan Kota': '76111',
             'Balikpapan Selatan': '76114', 'Balikpapan Tengah': '76122',
             'Balikpapan Timur': '76117', 'Balikpapan Utara': '76126'},
    '6472': {'Samarinda Ilir': '75114', 'Samarinda Kota': '75111',
             'Samarinda Seberang': '75241', 'Samarinda Ulu': '75125',
             'Samarinda Utara': '75131', 'Sungai Kunjang': '75126'},
    '6571': {'Tarakan Barat': '77111', 'Tarakan Tengah': '77111',
             'Tarakan Timur': '77113', 'Tarakan Utara': '77111'},
    '7171': {'Wenang': '95111', 'Malalayang': '95161', 'Sario': '95114'},
    '7371': {'Biringkanaya': '90241', 'Makassar': '90111', 'Manggala': '90231',
             'Mariso': '90126', 'Panakkukang': '90231', 'Rappocini': '90231',
             'Tallo': '90211', 'Tamalanrea': '90241', 'Tamalate': '90221',
             'Ujung Pandang': '90111', 'Wajo': '90171'},
    '7471': {'Kendari': '93111', 'Mandonga': '93111', 'Poasia': '93111'},
    '7571': {'Kota Barat': '96131', 'Kota Selatan': '96132',
             'Kota Tengah': '96111', 'Kota Timur': '96111', 'Kota Utara': '96121'},
    '7602': {'Wonomulyo': '91353', 'Polewali': '91311'},
    '8171': {'Sirimau': '97121', 'Nusaniwe': '97111', 'Teluk Ambon': '97231'},
    '9171': {'Sorong': '98411', 'Sorong Barat': '98411', 'Sorong Timur': '98411'},
    '9371': {'Jayapura Selatan': '99111', 'Jayapura Utara': '99111', 'Abepura': '99111'},
    '9307': {'Mimika Baru': '99910'},
}


class Command(BaseCommand):
    help = 'Seed postal codes from static POSTAL_CODES dictionary'

    @transaction.atomic
    def handle(self, *args, **options):
        count = 0
        not_found = 0
        for city_code, districts in POSTAL_CODES.items():
            for district_name, code in districts.items():
                try:
                    district = District.objects.get(
                        city__code=city_code, name=district_name,
                    )
                    PostalCode.objects.update_or_create(
                        district=district, code=code,
                        defaults={'district': district},
                    )
                    count += 1
                except District.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f'  ! District "{district_name}" in {city_code} not found'
                    ))
                    not_found += 1

        self.stdout.write(self.style.SUCCESS(
            f'{count} postal codes seeded, {not_found} district names not matched'
        ))
