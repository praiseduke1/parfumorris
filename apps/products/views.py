import logging

from django.db.models import Q, Count, Avg
from django.http import HttpResponsePermanentRedirect, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, DetailView, TemplateView

from apps.orders.models import OrderItem
from .models import Product, Category, FragranceNote, FragranceFamily, Review, ProductSlugRedirect

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = 'products/home.html'

    def get_context_data(self, **kwargs):
        logger.debug(
            f"HomeView — user={self.request.user.id} "
            f"username={self.request.user.username} "
            f"superuser={self.request.user.is_superuser}"
        )
        context = super().get_context_data(**kwargs)
        context['featured_products'] = Product.objects.filter(
            is_available=True
        ).select_related('category').prefetch_related('fragrance_notes', 'fragrance_families')[:8]
        context['new_products'] = Product.objects.filter(
            is_available=True
        ).select_related('category').prefetch_related('fragrance_notes', 'fragrance_families').order_by('-created_at')[:4]
        context['fragrance_notes'] = FragranceNote.objects.annotate(
            product_count=Count('products', filter=Q(products__is_available=True))
        )
        context['fragrance_families'] = FragranceFamily.objects.annotate(
            product_count=Count('products', filter=Q(products__is_available=True))
        )

        from apps.promotions.models import Voucher, UserVoucher
        vouchers = Voucher.objects.active()
        user = self.request.user
        user_claimed_ids = set()
        if user.is_authenticated and not user.is_superuser:
            user_claimed_ids = set(
                UserVoucher.objects.filter(user=user)
                .values_list('voucher_id', flat=True)
            )
        elif user.is_superuser:
            vouchers = vouchers.none()
        context['vouchers'] = vouchers
        context['user_claimed_voucher_ids'] = user_claimed_ids

        return context


class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        logger.debug(
            f"ProductListView — user={self.request.user.id} "
            f"username={self.request.user.username} "
            f"superuser={self.request.user.is_superuser}"
        )
        queryset = Product.objects.filter(
            is_available=True
        ).select_related('category').prefetch_related('fragrance_notes', 'fragrance_families')
        query = self.request.GET.get('q', '').strip()
        category_slug = self.request.GET.get('category', '')
        gender = self.request.GET.get('gender', '')

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        if gender in ('men', 'women', 'unisex'):
            queryset = queryset.filter(gender_target=gender)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.annotate(
            product_count=Count('products', filter=Q(products__is_available=True))
        )
        context['query'] = self.request.GET.get('q', '')
        context['selected_category'] = self.request.GET.get('category', '')
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            redirect_entry = get_object_or_404(
                ProductSlugRedirect, old_slug=self.kwargs.get(self.slug_url_kwarg)
            )
            return HttpResponsePermanentRedirect(
                reverse('products:detail', args=[redirect_entry.product.slug])
            )

    def get_queryset(self):
        logger.debug(
            f"ProductDetailView — user={self.request.user.id} "
            f"username={self.request.user.username} "
            f"superuser={self.request.user.is_superuser}"
        )
        return Product.objects.filter(
            is_available=True
        ).select_related('category').prefetch_related(
            'fragrance_notes', 'fragrance_families', 'variants',
            'reviews__user',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_products'] = Product.objects.filter(
            category=self.object.category, is_available=True
        ).exclude(id=self.object.id).prefetch_related('fragrance_notes', 'fragrance_families')[:4]

        notes = self.object.fragrance_notes.all()
        context['top_notes'] = notes.filter(note_type='TOP')
        context['middle_notes'] = notes.filter(note_type='MIDDLE')
        context['base_notes'] = notes.filter(note_type='BASE')

        context['variants'] = self.object.variants.filter(is_available=True)
        context['fragrance_families'] = self.object.fragrance_families.all()

        reviews = self.object.reviews.all()
        context['reviews'] = reviews
        context['avg_rating'] = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        context['review_count'] = reviews.count()

        user = self.request.user
        context['user_review'] = None
        context['can_review'] = False
        if user.is_authenticated and not user.is_superuser:
            try:
                context['user_review'] = reviews.get(user=user)
            except Review.DoesNotExist:
                pass
            context['can_review'] = OrderItem.objects.filter(
                product=self.object,
                order__user=user,
                order__status__in=['delivered', 'paid'],
            ).exists()

        return context


class AboutView(TemplateView):
    template_name = 'products/about.html'


class FragranceGuideView(TemplateView):
    template_name = 'products/fragrance_guide.html'


class ProductByNoteView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        logger.debug(
            f"ProductByNoteView — user={self.request.user.id} "
            f"username={self.request.user.username} "
            f"superuser={self.request.user.is_superuser}"
        )
        return Product.objects.filter(
            is_available=True, fragrance_notes__slug=self.kwargs['slug']
        ).select_related('category').prefetch_related('fragrance_notes', 'fragrance_families').distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.annotate(
            product_count=Count('products', filter=Q(products__is_available=True))
        )
        return context


class ProductByFamilyView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        return Product.objects.filter(
            is_available=True, fragrance_families__slug=self.kwargs['slug']
        ).select_related('category').prefetch_related('fragrance_notes', 'fragrance_families').distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.annotate(
            product_count=Count('products', filter=Q(products__is_available=True))
        )
        return context
