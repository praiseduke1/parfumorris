import logging
import re

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from apps.regions.models import City, District, PostalCode
from .models import CustomerAddress, Profile

logger = logging.getLogger(__name__)


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'autocomplete': 'username',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'autocomplete': 'current-password',
    }))


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email ini sudah terdaftar.')
        return email


INPUT_CLASS = 'w-full px-4 py-2.5 bg-stone-50 border border-stone-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-600/20 focus:border-amber-600 text-sm text-stone-700 placeholder:text-stone-400 transition-all appearance-none'
TOM_SELECT_CLASS = 'w-full'


class ProfileUpdateForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': INPUT_CLASS})
    )

    class Meta:
        model = Profile
        fields = ['phone']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': '08xxxxxxxxxx',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email

    def clean_username(self):
        username = self.cleaned_data['username']
        if self.user and User.objects.exclude(pk=self.user.pk).filter(username=username).exists():
            raise forms.ValidationError('Username sudah digunakan.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if self.user and User.objects.exclude(pk=self.user.pk).filter(email=email).exists():
            raise forms.ValidationError('Email sudah terdaftar.')
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.username = self.cleaned_data['username']
            self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save()
                profile.save()
        return profile


class CustomerAddressForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['city'].queryset = City.objects.none()
        self.fields['district'].queryset = District.objects.none()
        self.fields['postal_code'].queryset = PostalCode.objects.none()

        def parent_val(name):
            raw = None
            if self.is_bound:
                raw = self.data.get(name)
            elif self.instance.pk:
                parent = getattr(self.instance, name, None)
                raw = parent.pk if parent else None
            else:
                raw = self.initial.get(name)
            if raw is None or raw == '':
                return None
            try:
                return int(raw)
            except (ValueError, TypeError):
                return None

        pid = parent_val('province')
        cid = parent_val('city')
        did = parent_val('district')
        logger.debug('CustomerAddressForm: province=%s city=%s district=%s', pid, cid, did)

        if pid:
            self.fields['city'].queryset = City.objects.filter(province_id=pid)
        if cid:
            self.fields['district'].queryset = District.objects.filter(city_id=cid)
        if did:
            self.fields['postal_code'].queryset = PostalCode.objects.filter(district_id=did)

    class Meta:
        model = CustomerAddress
        fields = [
            'recipient_name', 'phone', 'address_line',
            'province', 'city', 'district', 'postal_code',
            'is_default', 'label',
            'rt', 'rw', 'latitude', 'longitude',
        ]
        widgets = {
            'recipient_name': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Nama lengkap penerima',
                'autocomplete': 'name',
                'aria-label': 'Nama Penerima',
            }),
            'phone': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': '08xxxxxxxxxx',
                'autocomplete': 'tel',
                'aria-label': 'Nomor Telepon',
            }),
            'address_line': forms.Textarea(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Nama jalan, gedung, nomor rumah, RT/RW',
                'rows': 3,
                'autocomplete': 'street-address',
                'aria-label': 'Alamat Lengkap',
            }),
            'label': forms.Select(choices=CustomerAddress.LABEL_CHOICES, attrs={
                'class': TOM_SELECT_CLASS,
                'aria-label': 'Label Alamat',
            }),
            'province': forms.Select(attrs={
                'class': TOM_SELECT_CLASS,
                'data-url': '/api/locations/cities/',
                'data-placeholder': 'Pilih Provinsi',
                'aria-label': 'Provinsi',
            }),
            'city': forms.Select(attrs={
                'class': TOM_SELECT_CLASS,
                'data-url': '/api/locations/districts/',
                'data-placeholder': 'Pilih Kota/Kabupaten',
                'aria-label': 'Kota/Kabupaten',
            }),
            'district': forms.Select(attrs={
                'class': TOM_SELECT_CLASS,
                'data-url': '/api/locations/postal-code/',
                'data-placeholder': 'Pilih Kecamatan',
                'aria-label': 'Kecamatan',
            }),
            'postal_code': forms.Select(attrs={
                'class': TOM_SELECT_CLASS,
                'data-placeholder': 'Pilih Kode Pos',
                'aria-label': 'Kode Pos',
            }),
            'rt': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'RT',
                'aria-label': 'RT',
            }),
            'rw': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'RW',
                'aria-label': 'RW',
            }),
            'latitude': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': '-6.2088',
                'step': 'any',
                'aria-label': 'Latitude',
            }),
            'longitude': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': '106.8456',
                'step': 'any',
                'aria-label': 'Longitude',
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-amber-600 border-stone-300 rounded focus:ring-amber-500',
                'aria-label': 'Jadikan alamat utama',
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        digits = re.sub(r'\D', '', phone)
        if not digits.startswith('08'):
            raise forms.ValidationError('Nomor telepon harus diawali 08.')
        if len(digits) < 10:
            raise forms.ValidationError('Nomor telepon minimal 10 digit.')
        return phone

    def clean_address_line(self):
        addr = self.cleaned_data['address_line']
        if len(addr.strip()) < 15:
            raise forms.ValidationError('Alamat terlalu pendek. Minimal 15 karakter.')
        return addr

    def clean(self):
        cleaned = super().clean()
        province = cleaned.get('province')
        city = cleaned.get('city')
        district = cleaned.get('district')
        postal_code = cleaned.get('postal_code')

        logger.debug(
            'CustomerAddressForm.clean: province=%s city=%s district=%s postal_code=%s',
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
