from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User

from apps.regions.models import City, District, PostalCode, Province
from apps.products.models import Product


POINTS_PER_THOUSAND = Decimal('1000')
LEVEL_THRESHOLDS = {
    'PLATINUM': Decimal('5000000'),
    'GOLD': Decimal('1000000'),
    'SILVER': Decimal('0'),
}
LEVEL_BENEFITS = {
    'SILVER': {
        'label': 'Silver',
        'color': 'text-stone-700 bg-stone-100 border-stone-300',
        'badge': 'bg-stone-400 text-white',
        'icon_bg': 'bg-stone-100',
        'icon_color': 'text-stone-500',
        'benefits': [
            'Akses ke semua produk',
            'Welcome voucher 10%',
            '1 poin per Rp 1.000 belanja',
        ],
        'next_threshold': 'Rp 1.000.000 untuk naik ke Gold',
    },
    'GOLD': {
        'label': 'Gold',
        'color': 'text-amber-700 bg-amber-50 border-amber-300',
        'badge': 'bg-amber-500 text-white',
        'icon_bg': 'bg-amber-100',
        'icon_color': 'text-amber-600',
        'benefits': [
            'Semua benefit Silver',
            '1,5x poin per Rp 1.000 belanja',
            'Voucher ulang tahun spesial',
            'Prioritas layanan pelanggan',
        ],
        'next_threshold': 'Rp 5.000.000 untuk naik ke Platinum',
    },
    'PLATINUM': {
        'label': 'Platinum',
        'color': 'text-indigo-700 bg-indigo-50 border-indigo-300',
        'badge': 'bg-indigo-500 text-white',
        'icon_bg': 'bg-indigo-100',
        'icon_color': 'text-indigo-600',
        'benefits': [
            'Semua benefit Gold',
            '2x poin per Rp 1.000 belanja',
            'Gratis ongkos kirim',
            'Early access produk baru',
            'Voucher diskon eksklusif',
        ],
        'next_threshold': None,
    },
}


def get_level(total_spending):
    for level, threshold in sorted(LEVEL_THRESHOLDS.items(), key=lambda x: -x[1]):
        if total_spending >= threshold:
            return level
    return 'SILVER'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField('Nomor Telepon', max_length=20, blank=True)
    address = models.TextField('Alamat', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profil'
        verbose_name_plural = 'Profil'

    def __str__(self):
        return f'Profil {self.user.username}'


class MemberProfile(models.Model):
    class Level(models.TextChoices):
        SILVER = 'SILVER', 'Silver'
        GOLD = 'GOLD', 'Gold'
        PLATINUM = 'PLATINUM', 'Platinum'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member_profile')
    level = models.CharField(
        'Level', max_length=20, choices=Level.choices,
        default=Level.SILVER,
    )
    total_points = models.PositiveIntegerField('Total Poin', default=0)
    total_spending = models.DecimalField(
        'Total Belanja', max_digits=14, decimal_places=0, default=0,
    )
    birth_date = models.DateField('Tanggal Lahir', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Member Profile'
        verbose_name_plural = 'Member Profile'
        indexes = [models.Index(fields=['level'])]

    def __str__(self):
        return f'{self.user.username} ({self.get_level_display()})'

    def upgrade_level(self):
        new_level = get_level(self.total_spending)
        if new_level != self.level:
            self.level = new_level
            self.save(update_fields=['level'])
            PointTransaction.objects.create(
                user=self.user,
                points=0,
                type=PointTransaction.Type.UPGRADE,
                description=f'Level naik ke {dict(self.Level.choices)[new_level]}',
            )

    def earn_points(self, amount):
        multiplier = {'SILVER': 10, 'GOLD': 15, 'PLATINUM': 20}
        points = int(amount / POINTS_PER_THOUSAND * multiplier[self.level] / 10)
        if points > 0:
            self.total_points += points
            self.save(update_fields=['total_points'])
            PointTransaction.objects.create(
                user=self.user,
                points=points,
                type=PointTransaction.Type.EARN,
                description=f'Poin dari pembelian Rp {amount:,.0f}',
            )


class PointTransaction(models.Model):
    class Type(models.TextChoices):
        EARN = 'EARN', 'Earned'
        REDEEM = 'REDEEM', 'Redeemed'
        UPGRADE = 'UPGRADE', 'Level Upgrade'

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='point_transactions',
        verbose_name='Pengguna',
    )
    points = models.IntegerField('Poin')
    type = models.CharField(
        'Tipe', max_length=10, choices=Type.choices,
    )
    description = models.CharField('Deskripsi', max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Transaksi Poin'
        verbose_name_plural = 'Transaksi Poin'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', '-created_at'])]

    def __str__(self):
        prefix = '+' if self.type in (self.Type.EARN, self.Type.UPGRADE) else '-'
        return f'{prefix}{self.points} — {self.user.username}'


class CustomerAddress(models.Model):
    LABEL_CHOICES = [
        ('Rumah', 'Rumah'),
        ('Kantor', 'Kantor'),
        ('Kos', 'Kos'),
        ('Rumah Orang Tua', 'Rumah Orang Tua'),
        ('Gudang', 'Gudang'),
        ('Lainnya', 'Lainnya'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='addresses',
        verbose_name='Pengguna'
    )
    label = models.CharField('Label', max_length=50, blank=True, choices=LABEL_CHOICES)
    recipient_name = models.CharField('Nama Penerima', max_length=100)
    phone = models.CharField('Nomor Telepon', max_length=20)
    address_line = models.TextField('Alamat Lengkap')
    rt = models.CharField('RT', max_length=4, blank=True)
    rw = models.CharField('RW', max_length=4, blank=True)
    province = models.ForeignKey(
        Province, on_delete=models.PROTECT, related_name='addresses',
        verbose_name='Provinsi', null=True, blank=True,
    )
    city = models.ForeignKey(
        City, on_delete=models.PROTECT, related_name='addresses',
        verbose_name='Kota/Kabupaten', null=True, blank=True,
    )
    district = models.ForeignKey(
        District, on_delete=models.PROTECT, related_name='addresses',
        verbose_name='Kecamatan', null=True, blank=True,
    )
    postal_code = models.ForeignKey(
        PostalCode, on_delete=models.PROTECT, related_name='addresses',
        verbose_name='Kode Pos', null=True, blank=True,
    )
    latitude = models.FloatField('Latitude', null=True, blank=True)
    longitude = models.FloatField('Longitude', null=True, blank=True)
    is_default = models.BooleanField('Alamat Utama', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Alamat Pelanggan'
        verbose_name_plural = 'Alamat Pelanggan'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        label = self.label or 'Alamat'
        return f'{label} - {self.recipient_name}'

    def save(self, *args, **kwargs):
        if self.is_default:
            CustomerAddress.objects.filter(
                user=self.user, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class Wishlist(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='wishlist_items',
        verbose_name='Pengguna'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='wishlist_items',
        verbose_name='Produk'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Wishlist'
        verbose_name_plural = 'Wishlist'
        unique_together = ['user', 'product']
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.product.name}'
