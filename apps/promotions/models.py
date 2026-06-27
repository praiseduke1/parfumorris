from datetime import timedelta

from django.db import models
from django.db.models import F, Q
from django.contrib.auth.models import User
from django.utils.timezone import now


class VoucherQuerySet(models.QuerySet):
    def active(self):
        today = now().date()
        return self.filter(
            is_active=True,
        ).filter(
            Q(start_date__lte=today) | Q(start_date__isnull=True),
        ).filter(
            Q(expired_date__gte=today) | Q(expired_date__isnull=True),
        ).filter(
            Q(quota=0) | Q(claimed_count__lt=F('quota'))
        )

    def public(self):
        return self.filter(voucher_type=Voucher.Type.PUBLIC)

    def auto_assignable(self):
        return self.filter(auto_assign=True, is_active=True)


class Voucher(models.Model):
    class Category(models.TextChoices):
        PRODUCT = 'product', 'Voucher Produk'
        SHIPPING = 'shipping', 'Voucher Ongkir'

    class Type(models.TextChoices):
        PUBLIC = 'public', 'Publik'
        WELCOME = 'welcome', 'Member Baru'
        MIN_PURCHASE = 'min_purchase', 'Minimum Pembelian'
        BIRTHDAY = 'birthday', 'Ulang Tahun'
        LOYALTY = 'loyalty', 'Loyalitas'

    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', 'Persen (%)'
        FIXED = 'fixed', 'Nominal (Rp)'

    code = models.CharField('Kode Voucher', max_length=50, unique=True)
    category = models.CharField(
        'Jenis Voucher', max_length=20,
        choices=Category.choices, default=Category.PRODUCT,
        help_text='Voucher Produk (diskon belanja) atau Voucher Ongkir (diskon pengiriman)'
    )
    description = models.TextField('Deskripsi', blank=True)
    discount_type = models.CharField(
        'Tipe Diskon', max_length=20,
        choices=DiscountType.choices, default=DiscountType.PERCENTAGE
    )
    discount_amount = models.DecimalField('Nilai Diskon', max_digits=12, decimal_places=0)
    min_purchase = models.DecimalField(
        'Min. Belanja', max_digits=12, decimal_places=0, default=0,
        help_text='Total belanja minimum sebelum diskon'
    )
    max_discount = models.DecimalField(
        'Maks. Diskon', max_digits=12, decimal_places=0,
        null=True, blank=True,
        help_text='Maksimal nominal diskon (khusus persen)'
    )
    voucher_type = models.CharField(
        'Tipe Voucher', max_length=20,
        choices=Type.choices, default=Type.PUBLIC,
        help_text='Menentukan cara voucher didistribusikan'
    )
    auto_assign = models.BooleanField(
        'Otomatis', default=False,
        help_text='Voucher otomatis diberikan ke customer yang memenuhi syarat'
    )
    min_transactions = models.PositiveIntegerField(
        'Min. Transaksi', default=0,
        help_text='Jumlah transaksi minimum (khusus tipe loyalitas)'
    )
    quota = models.PositiveIntegerField(
        'Kuota', default=0,
        help_text='Maksimum jumlah klaim (0 = tidak terbatas)'
    )
    claimed_count = models.PositiveIntegerField('Sudah Diklaim', default=0)
    used_count = models.PositiveIntegerField('Sudah Digunakan', default=0)
    start_date = models.DateField(
        'Tanggal Mulai', default=now,
        help_text='Tanggal mulai berlaku voucher'
    )
    expired_date = models.DateField(
        'Tanggal Kedaluwarsa', null=True, blank=True,
        help_text='Kosongkan jika tidak ada batas waktu'
    )
    is_active = models.BooleanField('Aktif', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = VoucherQuerySet.as_manager()

    class Meta:
        verbose_name = 'Voucher Promosi'
        verbose_name_plural = 'Voucher Promosi'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} ({self.get_category_display()})'

    def is_claimable(self):
        today = now().date()
        if not self.is_active:
            return False
        if self.start_date and self.start_date > today:
            return False
        if self.expired_date and self.expired_date < today:
            return False
        if self.quota > 0 and self.claimed_count >= self.quota:
            return False
        return True

    def remaining_quota(self):
        if self.quota == 0:
            return -1
        return max(0, self.quota - self.claimed_count)

    def can_use(self, subtotal=0):
        if not self.is_active:
            return False
        today = now().date()
        if self.start_date and self.start_date > today:
            return False
        if self.expired_date and self.expired_date < today:
            return False
        if subtotal and subtotal < self.min_purchase:
            return False
        return True

    def calculate_discount(self, subtotal):
        if self.discount_type == self.DiscountType.FIXED:
            return min(self.discount_amount, subtotal)
        amount = subtotal * self.discount_amount / 100
        if self.max_discount:
            amount = min(amount, self.max_discount)
        return min(int(amount), subtotal)

    def get_type_icon(self):
        icons = {
            self.Type.PUBLIC: 'globe',
            self.Type.WELCOME: 'star',
            self.Type.MIN_PURCHASE: 'shopping-cart',
            self.Type.BIRTHDAY: 'gift',
            self.Type.LOYALTY: 'award',
        }
        return icons.get(self.voucher_type, 'tag')


class UserVoucher(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Tersedia'
        USED = 'used', 'Terpakai'
        EXPIRED = 'expired', 'Kedaluwarsa'

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='user_vouchers',
        verbose_name='Pengguna'
    )
    voucher = models.ForeignKey(
        Voucher, on_delete=models.CASCADE, related_name='user_vouchers',
        verbose_name='Voucher'
    )
    status = models.CharField(
        'Status', max_length=20, choices=Status.choices, default=Status.AVAILABLE,
        db_index=True
    )
    assigned_at = models.DateTimeField('Diperoleh Pada', auto_now_add=True)
    used_at = models.DateTimeField('Digunakan Pada', null=True, blank=True)
    expires_at = models.DateTimeField('Kedaluwarsa Pada')

    class Meta:
        verbose_name = 'Voucher Pengguna'
        verbose_name_plural = 'Voucher Pengguna'
        ordering = ['-assigned_at']
        unique_together = ['user', 'voucher']

    def __str__(self):
        return f'{self.user.username} - {self.voucher.code}'
