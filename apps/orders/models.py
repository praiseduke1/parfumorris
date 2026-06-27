import uuid

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

from apps.products.models import Product, ProductVariant
from apps.promotions.models import Voucher as PromoVoucher


class Voucher(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', 'Persen (%)'
        FIXED = 'fixed', 'Nominal (Rp)'

    code = models.CharField('Kode Voucher', max_length=50, unique=True)
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
    max_uses = models.PositiveIntegerField('Maks. Penggunaan', default=0)
    used_count = models.PositiveIntegerField('Sudah Digunakan', default=0)
    is_active = models.BooleanField('Aktif', default=True)
    valid_from = models.DateTimeField('Berlaku Dari')
    valid_until = models.DateTimeField('Berlaku Sampai')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Voucher'
        verbose_name_plural = 'Voucher'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['is_active', '-created_at'])]

    def __str__(self):
        return self.code

    def is_valid(self, subtotal=0):
        if not self.is_active:
            return False
        if self.valid_from and self.valid_from > now():
            return False
        if self.valid_until and self.valid_until < now():
            return False
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False
        if subtotal > 0 and subtotal < self.min_purchase:
            return False
        return True

    def calculate_discount(self, subtotal):
        if self.discount_type == self.DiscountType.FIXED:
            return min(self.discount_amount, subtotal)
        amount = subtotal * self.discount_amount / 100
        if self.max_discount:
            amount = min(amount, self.max_discount)
        return min(int(amount), subtotal)


def generate_order_number():
    date_part = now().strftime('%Y%m%d')
    unique_part = uuid.uuid4().hex[:6].upper()
    return f'ORD-{date_part}-{unique_part}'


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = 'pending_payment', 'Pending Payment'
        PAID = 'paid', 'Paid'
        PROCESSING = 'processing', 'Processing'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='orders',
        verbose_name='Pengguna'
    )
    order_number = models.CharField(
        'Nomor Pesanan', max_length=30, unique=True,
        default=generate_order_number, editable=False
    )
    status = models.CharField(
        'Status', max_length=20, choices=Status.choices,
        default=Status.PENDING_PAYMENT
    )
    subtotal = models.DecimalField('Subtotal', max_digits=12, decimal_places=0, default=0)
    discount_amount = models.DecimalField('Diskon', max_digits=12, decimal_places=0, default=0)
    shipping_cost = models.DecimalField('Ongkos Kirim', max_digits=12, decimal_places=0, default=0)
    shipping_courier = models.CharField('Kurir', max_length=20, blank=True)
    shipping_service = models.CharField('Layanan', max_length=50, blank=True)
    shipping_estimation = models.CharField('Estimasi', max_length=50, blank=True)
    shipping_weight = models.PositiveIntegerField('Berat (gram)', default=0)
    shipping_origin = models.CharField('Asal Pengiriman', max_length=200, blank=True)
    shipping_destination = models.CharField('Tujuan Pengiriman', max_length=200, blank=True)
    tracking_number = models.CharField('Nomor Resi', max_length=100, blank=True)
    total_price = models.DecimalField('Total Harga', max_digits=12, decimal_places=0)

    paid_at = models.DateTimeField('Tanggal Pembayaran', null=True, blank=True)
    processing_at = models.DateTimeField('Tanggal Diproses', null=True, blank=True)
    shipped_at = models.DateTimeField('Tanggal Dikirim', null=True, blank=True)
    delivered_at = models.DateTimeField('Tanggal Diterima', null=True, blank=True)
    completed_at = models.DateTimeField('Tanggal Selesai', null=True, blank=True)

    voucher = models.ForeignKey(
        Voucher, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders', verbose_name='Voucher'
    )
    product_voucher = models.ForeignKey(
        PromoVoucher, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='product_orders', verbose_name='Voucher Produk'
    )
    shipping_voucher = models.ForeignKey(
        PromoVoucher, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='shipping_orders', verbose_name='Voucher Ongkir'
    )
    product_discount = models.DecimalField('Diskon Produk', max_digits=12, decimal_places=0, default=0)
    shipping_discount = models.DecimalField('Diskon Ongkir', max_digits=12, decimal_places=0, default=0)

    midtrans_order_id = models.UUIDField(
        'ID Midtrans', default=uuid.uuid4, unique=True, editable=False
    )
    recipient_name = models.CharField('Nama Penerima', max_length=100)
    phone = models.CharField('Nomor Telepon', max_length=20)
    shipping_address = models.TextField('Alamat Lengkap')
    city = models.CharField('Kota', max_length=100)
    province = models.CharField('Provinsi', max_length=100, blank=True)
    district = models.CharField('Kecamatan', max_length=100, blank=True)
    postal_code = models.CharField('Kode Pos', max_length=10)
    notes = models.TextField('Catatan Pesanan', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pesanan'
        verbose_name_plural = 'Pesanan'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.order_number} - {self.user.username}'

    STATUS_TIMESTAMP_FIELDS = {
        Status.PAID: 'paid_at',
        Status.PROCESSING: 'processing_at',
        Status.SHIPPED: 'shipped_at',
        Status.DELIVERED: 'delivered_at',
        Status.COMPLETED: 'completed_at',
    }

    def save(self, *args, **kwargs):
        if not self.midtrans_order_id:
            self.midtrans_order_id = uuid.uuid4()
        is_new = self._state.adding
        if is_new:
            super().save(*args, **kwargs)
        else:
            try:
                old = Order.objects.get(pk=self.pk)
                status_changed = old.status != self.status
            except Order.DoesNotExist:
                status_changed = False
            if status_changed:
                ts_field = self.STATUS_TIMESTAMP_FIELDS.get(self.status)
                if ts_field:
                    setattr(self, ts_field, now())
            super().save(*args, **kwargs)
            if status_changed:
                OrderStatusHistory.objects.create(
                    order=self,
                    status=self.status,
                )
        if is_new:
            OrderStatusHistory.objects.create(
                order=self,
                status=self.status,
            )


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(
        'Order', on_delete=models.CASCADE, related_name='status_history',
        verbose_name='Pesanan'
    )
    status = models.CharField(
        'Status', max_length=20,
        choices=Order.Status.choices,
    )
    notes = models.TextField('Catatan', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Riwayat Status Pesanan'
        verbose_name_plural = 'Riwayat Status Pesanan'
        ordering = ['created_at']
        indexes = [models.Index(fields=['order', 'created_at'])]

    def __str__(self):
        return f'{self.order.order_number}: {self.get_status_display()}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items',
        verbose_name='Pesanan'
    )
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='order_items', verbose_name='Produk'
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='order_items', verbose_name='Varian'
    )
    product_name = models.CharField('Nama Produk', max_length=200)
    variant_name = models.CharField('Nama Varian', max_length=50, blank=True)
    price = models.DecimalField('Harga', max_digits=12, decimal_places=0)
    quantity = models.PositiveIntegerField('Jumlah', default=1)

    class Meta:
        verbose_name = 'Item Pesanan'
        verbose_name_plural = 'Item Pesanan'

    def __str__(self):
        label = self.product_name
        if self.variant_name:
            label += f' ({self.variant_name})'
        return f'{self.quantity}x {label}'

    def total_price(self):
        return self.price * self.quantity
