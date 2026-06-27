from django.contrib import admin
from django.utils.html import format_html
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.urls import reverse

from apps.core.admin_utils import format_rupiah

from .models import Category, Product, FragranceFamily, FragranceNote, ProductVariant, Brand, ProductImage, Review, ProductSlugRedirect


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count', 'description']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']

    def product_count(self, obj):
        count = obj.products.count()
        url = reverse('admin:products_product_changelist') + '?' + urlencode({'category__id__exact': obj.id})
        return format_html('<a href="{}">{}</a>', url, count)
    product_count.short_description = 'Jumlah Produk'


@admin.register(FragranceNote)
class FragranceNoteAdmin(admin.ModelAdmin):
    list_display = ['name', 'note_type', 'product_count', 'created_at']
    list_filter = ['note_type']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['note_type', 'name']

    def product_count(self, obj):
        count = obj.products.count()
        url = reverse('admin:products_product_changelist') + '?' + urlencode({'fragrance_notes__id__exact': obj.id})
        return format_html('<a href="{}">{}</a>', url, count)
    product_count.short_description = 'Jumlah Produk'


@admin.register(FragranceFamily)
class FragranceFamilyAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count', 'description']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Jumlah Produk'


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Jumlah Produk'


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ['size_ml', 'price', 'stock', 'sku', 'is_available']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'sort_order']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_info', 'category_badge', 'brand_badge', 'formatted_price', 'stock_badge', 'status_display', 'created_at']
    list_display_links = ['product_info']
    list_filter = ['brand', 'category', 'fragrance_families', 'fragrance_notes', 'gender_target', 'occasion', 'season', 'is_available', 'created_at']
    search_fields = ['name', 'description', 'brand__name']
    autocomplete_fields = ['category', 'brand']
    prepopulated_fields = {'slug': ('name',)}
    list_select_related = ['category', 'brand']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['thumbnail_preview_detail']
    filter_horizontal = ['fragrance_notes', 'fragrance_families']
    inlines = [ProductImageInline, ProductVariantInline]
    actions = ['mark_as_available', 'mark_as_unavailable']

    fieldsets = (
        ('Informasi Dasar', {
            'fields': ('category', 'brand', 'name', 'slug', 'description')
        }),
        ('Fragrance Notes', {
            'fields': ('fragrance_notes',),
            'description': 'Pilih aroma untuk parfum ini. Tahan Ctrl untuk memilih banyak.',
        }),
        ('Keluarga Aroma', {
            'fields': ('fragrance_families',),
            'description': 'Pilih karakter aroma parfum (contoh: Citrus, Floral, Woody).',
        }),
        ('Target & Karakter', {
            'fields': ('gender_target', 'occasion', 'season'),
        }),
        ('Kinerja', {
            'fields': ('sillage', 'longevity'),
        }),
        ('Harga & Stok', {
            'fields': ('price', 'stock', 'is_available')
        }),
        ('Gambar', {
            'fields': ('image', 'thumbnail_preview_detail')
        }),
    )

    def product_info(self, obj):
        if obj.image:
            img = format_html(
                '<img src="{}" style="width:40px;height:40px;object-fit:cover;border-radius:4px;" />',
                obj.image.url
            )
        else:
            img = mark_safe(
                '<span style="display:inline-block;width:40px;height:40px;border-radius:4px;'
                'background:#e9ecef;text-align:center;line-height:40px;font-size:10px;color:#6c757d;">'
                'No img</span>'
            )
        return format_html(
            '<div style="display:flex;align-items:center;gap:8px;">'
            '<div>{}</div>'
            '<div><strong>{}</strong></div>'
            '</div>',
            img, obj.name
        )
    product_info.short_description = 'Produk'

    def category_badge(self, obj):
        if obj.category:
            return format_html('<span class="badge badge-info">{}</span>', obj.category.name)
        return '-'
    category_badge.short_description = 'Kategori'
    category_badge.admin_order_field = 'category'

    def brand_badge(self, obj):
        if obj.brand:
            return format_html('<span class="badge badge-secondary">{}</span>', obj.brand.name)
        return '-'
    brand_badge.short_description = 'Brand'
    brand_badge.admin_order_field = 'brand'

    def stock_badge(self, obj):
        stock = obj.stock
        if stock == 0:
            cls = 'badge badge-danger'
            label = 'Habis'
        elif stock <= 5:
            cls = 'badge badge-warning'
            label = f'{stock} tersisa'
        else:
            cls = 'badge badge-success'
            label = str(stock)
        return format_html('<span class="{}">{}</span>', cls, label)
    stock_badge.short_description = 'Stok'
    stock_badge.admin_order_field = 'stock'

    def status_display(self, obj):
        if obj.is_available:
            return mark_safe('<span class="badge badge-success">Aktif</span>')
        return mark_safe('<span class="badge badge-danger">Nonaktif</span>')
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'is_available'

    def thumbnail_preview_detail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:300px;max-height:300px;border-radius:8px;" />',
                obj.image.url
            )
        return mark_safe('<span style="color:#999;font-size:13px;">Tidak ada gambar</span>')
    thumbnail_preview_detail.short_description = 'Pratinjau Gambar'

    def formatted_price(self, obj):
        return format_rupiah(obj.price)
    formatted_price.short_description = 'Harga'
    formatted_price.admin_order_field = 'price'

    def mark_as_available(self, request, queryset):
        updated = queryset.update(is_available=True)
        self.message_user(request, f'{updated} produk ditandai tersedia.')
    mark_as_available.short_description = 'Tandai tersedia'

    def mark_as_unavailable(self, request, queryset):
        updated = queryset.update(is_available=False)
        self.message_user(request, f'{updated} produk ditandai tidak tersedia.')
    mark_as_unavailable.short_description = 'Tandai tidak tersedia'


@admin.register(ProductSlugRedirect)
class ProductSlugRedirectAdmin(admin.ModelAdmin):
    list_display = ['old_slug', 'product', 'created_at']
    search_fields = ['old_slug', 'product__name']
    autocomplete_fields = ['product']
    readonly_fields = ['old_slug', 'product', 'created_at']
    ordering = ['-created_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating_stars', 'created_at']
    list_select_related = ['product', 'user']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'user__username', 'comment']
    autocomplete_fields = ['product', 'user']
    readonly_fields = ['user', 'product', 'rating', 'comment', 'created_at', 'updated_at']

    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color:#f59e0b;">{}</span>', stars)
    rating_stars.short_description = 'Rating'
