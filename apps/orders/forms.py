import logging
import re

from django import forms

from apps.regions.models import City, District, PostalCode, Province
from .models import Order

logger = logging.getLogger(__name__)

INPUT_CLASS = 'w-full px-4 py-2.5 bg-stone-50 border border-stone-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-600/20 focus:border-amber-600 text-sm text-stone-700 placeholder:text-stone-400 transition-all'


class CheckoutForm(forms.ModelForm):
    province = forms.ModelChoiceField(
        queryset=Province.objects.all(),
        widget=forms.Select(attrs={
            'class': INPUT_CLASS,
            'data-url': '/api/locations/cities/',
            'data-placeholder': 'Pilih Provinsi',
            'aria-label': 'Provinsi',
        }),
        error_messages={'required': 'Provinsi wajib dipilih.'},
    )
    city = forms.ModelChoiceField(
        queryset=City.objects.none(),
        widget=forms.Select(attrs={
            'class': INPUT_CLASS,
            'data-url': '/api/locations/districts/',
            'data-placeholder': 'Pilih Kota/Kabupaten',
            'aria-label': 'Kota/Kabupaten',
        }),
        error_messages={'required': 'Kota/Kabupaten wajib dipilih.'},
    )
    district = forms.ModelChoiceField(
        queryset=District.objects.none(),
        widget=forms.Select(attrs={
            'class': INPUT_CLASS,
            'data-url': '/api/locations/postal-code/',
            'data-placeholder': 'Pilih Kecamatan',
            'aria-label': 'Kecamatan',
        }),
        error_messages={'required': 'Kecamatan wajib dipilih.'},
    )
    postal_code = forms.ModelChoiceField(
        queryset=PostalCode.objects.none(),
        widget=forms.Select(attrs={
            'class': INPUT_CLASS,
            'data-placeholder': 'Pilih Kode Pos',
            'aria-label': 'Kode Pos',
        }),
        error_messages={'required': 'Kode Pos wajib dipilih.'},
    )

    class Meta:
        model = Order
        fields = [
            'recipient_name', 'phone', 'shipping_address', 'notes',
        ]
        widgets = {
            'recipient_name': forms.TextInput(attrs={
                'class': INPUT_CLASS, 'placeholder': 'Nama lengkap penerima',
            }),
            'phone': forms.TextInput(attrs={
                'class': INPUT_CLASS, 'placeholder': '08xxxxxxxxxx',
            }),
            'shipping_address': forms.Textarea(attrs={
                'class': INPUT_CLASS, 'placeholder': 'Nama jalan, gedung, nomor rumah, RT/RW', 'rows': 3,
            }),
            'notes': forms.Textarea(attrs={
                'class': INPUT_CLASS, 'placeholder': 'Catatan untuk pengiriman (opsional)', 'rows': 2,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def parent_val(name):
            raw = self.data.get(name) if self.is_bound else self.initial.get(name)
            if raw is None or raw == '':
                return None
            try:
                return int(raw)
            except (ValueError, TypeError):
                return None

        province_id = parent_val('province')
        city_id = parent_val('city')
        district_id = parent_val('district')

        logger.debug('CheckoutForm: province=%s city=%s district=%s', province_id, city_id, district_id)

        if province_id:
            self.fields['city'].queryset = City.objects.filter(province_id=province_id)
        if city_id:
            self.fields['district'].queryset = District.objects.filter(city_id=city_id)
        if district_id:
            self.fields['postal_code'].queryset = PostalCode.objects.filter(district_id=district_id)

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        digits = re.sub(r'\D', '', phone)
        if not digits.startswith('08'):
            raise forms.ValidationError('Nomor telepon harus diawali 08.')
        if len(digits) < 10:
            raise forms.ValidationError('Nomor telepon minimal 10 digit.')
        return phone

    def clean(self):
        cleaned = super().clean()
        province = cleaned.get('province')
        city = cleaned.get('city')
        district = cleaned.get('district')
        postal_code = cleaned.get('postal_code')

        logger.debug(
            'CheckoutForm.clean: province=%s city=%s district=%s postal_code=%s',
            province.pk if province else None,
            city.pk if city else None,
            district.pk if district else None,
            postal_code.pk if postal_code else None,
        )

        if city and province and city.province_id != province.id:
            self.add_error('city', 'Kota/kabupaten tidak sesuai dengan provinsi yang dipilih.')
        if district and city and district.city_id != city.id:
            self.add_error('district', 'Kecamatan tidak sesuai dengan kota/kabupaten yang dipilih.')
        if postal_code and district and postal_code.district_id != district.id:
            self.add_error('postal_code', 'Kode pos tidak sesuai dengan kecamatan yang dipilih.')

        return cleaned

    def clean_shipping_address(self):
        addr = self.cleaned_data['shipping_address']
        if len(addr.strip()) < 10:
            raise forms.ValidationError('Alamat minimal 10 karakter.')
        return addr

    def save(self, commit=True):
        order = super().save(commit=False)
        province = self.cleaned_data.get('province')
        city = self.cleaned_data.get('city')
        district = self.cleaned_data.get('district')
        postal_code = self.cleaned_data.get('postal_code')
        order.province = province.name if province else ''
        order.city = city.name if city else ''
        order.district = district.name if district else ''
        order.postal_code = postal_code.code if postal_code else ''
        if commit:
            order.save()
        return order
