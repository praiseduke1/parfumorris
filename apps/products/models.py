from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth.models import User


class FragranceFamily(models.Model):
    name = models.CharField('Nama Keluarga Aroma', max_length=100)
    slug = models.SlugField('Slug', unique=True, blank=True)
    description = models.TextField('Deskripsi', blank=True)

    class Meta:
        verbose_name = 'Keluarga Aroma'
        verbose_name_plural = 'Keluarga Aroma'
        ordering = ['name']
        indexes = [models.Index(fields=['name'])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Category(models.Model):
    name = models.CharField('Nama Kategori', max_length=100)
    slug = models.SlugField('Slug', unique=True, blank=True)
    description = models.TextField('Deskripsi', blank=True)

    class Meta:
        verbose_name = 'Kategori'
        verbose_name_plural = 'Kategori'
        ordering = ['name']
        indexes = [models.Index(fields=['name'])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class FragranceNote(models.Model):
    class NoteType(models.TextChoices):
        TOP = 'TOP', 'Top Notes'
        MIDDLE = 'MIDDLE', 'Middle Notes'
        BASE = 'BASE', 'Base Notes'

    name = models.CharField('Nama Aroma', max_length=100)
    note_type = models.CharField(
        'Tipe Note', max_length=10, choices=NoteType.choices
    )
    slug = models.SlugField('Slug', unique=True, blank=True)
    description = models.TextField('Deskripsi', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fragrance Note'
        verbose_name_plural = 'Fragrance Notes'
        ordering = ['note_type', 'name']
        indexes = [models.Index(fields=['note_type', 'name'])]

    def __str__(self):
        return f'{self.name} ({self.get_note_type_display()})'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Brand(models.Model):
    name = models.CharField('Nama Brand', max_length=100)
    slug = models.SlugField('Slug', unique=True, blank=True)
    description = models.TextField('Deskripsi', blank=True)
    logo = models.ImageField('Logo', upload_to='brands/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Brand'
        verbose_name_plural = 'Brand'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductVariant(models.Model):
    product = models.ForeignKey(
        'Product', on_delete=models.CASCADE, related_name='variants',
        verbose_name='Produk'
    )
    size_ml = models.PositiveIntegerField('Ukuran (ml)')
    price = models.DecimalField('Harga', max_digits=12, decimal_places=0)
    weight = models.PositiveIntegerField('Berat (gram)', default=0, blank=True)
    stock = models.PositiveIntegerField('Stok', default=0)
    sku = models.CharField('SKU', max_length=50, unique=True, blank=True)
    is_available = models.BooleanField('Tersedia', default=True)

    class Meta:
        verbose_name = 'Varian Produk'
        verbose_name_plural = 'Varian Produk'
        ordering = ['size_ml']
        unique_together = ['product', 'size_ml']

    def __str__(self):
        return f'{self.product.name} ({self.size_ml}ml)'


class Product(models.Model):
    class Gender(models.TextChoices):
        MEN = 'men', 'For Men'
        WOMEN = 'women', 'For Women'
        UNISEX = 'unisex', 'Unisex'

    class Occasion(models.TextChoices):
        DAILY = 'daily', 'Daily'
        OFFICE = 'office', 'Office'
        CASUAL = 'casual', 'Casual'
        FORMAL = 'formal', 'Formal'
        EVENING = 'evening', 'Evening'

    class Sillage(models.TextChoices):
        INTIMATE = 'intimate', 'Intimate'
        MODERATE = 'moderate', 'Moderate'
        HEAVY = 'heavy', 'Heavy'

    class Longevity(models.TextChoices):
        SHORT = 'short', '1–3 hours'
        MODERATE = 'moderate', '3–6 hours'
        LONG = 'long', '6–9 hours'
        VERY_LONG = 'very_long', '9+ hours'

    class Season(models.TextChoices):
        SPRING = 'spring', 'Spring'
        SUMMER = 'summer', 'Summer'
        FALL = 'fall', 'Fall'
        WINTER = 'winter', 'Winter'
        ALL = 'all', 'All Season'

    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='products',
        verbose_name='Kategori'
    )
    brand = models.ForeignKey(
        Brand, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products', verbose_name='Brand'
    )
    fragrance_notes = models.ManyToManyField(
        FragranceNote, related_name='products', blank=True,
        verbose_name='Fragrance Notes'
    )
    fragrance_families = models.ManyToManyField(
        FragranceFamily, related_name='products', blank=True,
        verbose_name='Keluarga Aroma'
    )
    name = models.CharField('Nama Produk', max_length=200)
    slug = models.SlugField('Slug', unique=True, blank=True)
    description = models.TextField('Deskripsi', blank=True)
    price = models.DecimalField('Harga', max_digits=12, decimal_places=0)
    weight = models.PositiveIntegerField('Berat (gram)', default=500)
    stock = models.PositiveIntegerField('Stok', default=0)
    image = models.ImageField('Gambar', upload_to='products/', blank=True, null=True)
    is_available = models.BooleanField('Tersedia', default=True)
    gender_target = models.CharField(
        'Target Gender', max_length=10, choices=Gender.choices,
        default=Gender.UNISEX,
    )
    occasion = models.CharField(
        'Kesempatan', max_length=10, choices=Occasion.choices,
        default=Occasion.DAILY,
    )
    sillage = models.CharField(
        'Sillage', max_length=10, choices=Sillage.choices,
        default=Sillage.MODERATE,
    )
    longevity = models.CharField(
        'Daya Tahan', max_length=10, choices=Longevity.choices,
        default=Longevity.MODERATE,
    )
    season = models.CharField(
        'Musim', max_length=10, choices=Season.choices,
        default=Season.ALL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Produk'
        verbose_name_plural = 'Produk'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_available', '-created_at']),
            models.Index(fields=['category', 'is_available']),
            models.Index(fields=['gender_target']),
            models.Index(fields=['occasion']),
            models.Index(fields=['season']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('products:detail', args=[self.slug])

    def save(self, *args, **kwargs):
        old_slug = None
        if self.pk:
            old_slug = Product.objects.filter(pk=self.pk).values_list('slug', flat=True).first()
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        if self.slug and old_slug and old_slug != self.slug:
            ProductSlugRedirect.objects.update_or_create(
                old_slug=old_slug,
                defaults={'product': self}
            )

    def has_variants(self):
        return self.variants.exists()

    def min_price(self):
        return self.variants.aggregate(models.Min('price'))['price__min'] or self.price

    def total_stock(self):
        if self.has_variants():
            return self.variants.aggregate(models.Sum('stock'))['stock__sum'] or 0
        return self.stock


class ProductSlugRedirect(models.Model):
    old_slug = models.SlugField('Slug Lama', unique=True, max_length=200)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='slug_redirects',
        verbose_name='Produk'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Redirect Slug'
        verbose_name_plural = 'Redirect Slug'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.old_slug} → {self.product.slug}'


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='images',
        verbose_name='Produk'
    )
    image = models.ImageField('Gambar', upload_to='products/')
    alt_text = models.CharField('Teks Alternatif', max_length=200, blank=True)
    is_primary = models.BooleanField('Utama', default=False)
    sort_order = models.PositiveIntegerField('Urutan', default=0)

    class Meta:
        verbose_name = 'Gambar Produk'
        verbose_name_plural = 'Gambar Produk'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'Gambar {self.product.name} ({self.sort_order})'


class Review(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reviews',
        verbose_name='Pengguna'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='reviews',
        verbose_name='Produk'
    )
    rating = models.PositiveSmallIntegerField(
        'Rating', choices=[(i, str(i)) for i in range(1, 6)]
    )
    comment = models.TextField('Komentar', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ulasan'
        verbose_name_plural = 'Ulasan'
        unique_together = ['user', 'product']
        ordering = ['-created_at']
        indexes = [models.Index(fields=['-created_at'])]

    def __str__(self):
        return f'{self.user.username} - {self.product.name} ({self.rating}/5)'

    def has_purchased_product(self):
        if not hasattr(self, '_purchased_cache'):
            from apps.orders.models import Order, OrderItem
            self._purchased_cache = OrderItem.objects.filter(
                product=self.product,
                order__user=self.user,
                order__status__in=['completed', 'paid'],
            ).exists()
        return self._purchased_cache
