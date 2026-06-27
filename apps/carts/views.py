from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme

from apps.core.decorators import customer_required
from .models import Cart, CartItem
from apps.products.models import Product, ProductVariant



def get_cart_item_stock(cart_item):
    return cart_item.variant.stock if cart_item.variant else cart_item.product.stock


def get_or_create_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return cart


@login_required
@customer_required
def cart_detail(request):
    cart = get_or_create_cart(request)
    items = cart.items.select_related('product__category', 'variant').all()

    subtotal = cart.total_price()
    total_items = cart.total_items()

    voucher_code = request.session.get('voucher_code', '')
    voucher_discount = 0
    final_total = subtotal

    if voucher_code:
        from apps.promotions.services import validate_voucher
        is_valid, voucher, discount, error = validate_voucher(voucher_code, request.user, subtotal)
        if is_valid:
            voucher_discount = discount
            final_total = subtotal - discount
            if voucher.category == voucher.Category.PRODUCT:
                request.session['product_voucher_id'] = voucher.id
        else:
            if 'voucher_code' in request.session:
                del request.session['voucher_code']
            if 'product_voucher_id' in request.session:
                del request.session['product_voucher_id']
            voucher_code = ''

    context = {
        'cart': cart,
        'cart_items': items,
        'subtotal': subtotal,
        'total_items': total_items,
        'voucher_code': voucher_code,
        'voucher_discount': voucher_discount,
        'final_total': final_total,
    }
    return render(request, 'carts/cart_detail.html', context)


@login_required
@customer_required
@require_POST
def apply_voucher(request):
    code = request.POST.get('code', '').strip()
    if not code:
        if 'voucher_code' in request.session:
            del request.session['voucher_code']
        if 'product_voucher_id' in request.session:
            del request.session['product_voucher_id']
        messages.error(request, 'Kode voucher tidak boleh kosong.')
        return redirect('carts:detail')

    cart = get_or_create_cart(request)
    subtotal = cart.total_price()

    from apps.promotions.services import validate_voucher
    is_valid, voucher, discount, error = validate_voucher(code, request.user, subtotal)
    if is_valid:
        request.session['voucher_code'] = voucher.code
        if voucher.category == voucher.Category.PRODUCT:
            request.session['product_voucher_id'] = voucher.id
        elif voucher.category == voucher.Category.SHIPPING:
            request.session['shipping_voucher_id'] = voucher.id
        messages.success(request, f'Voucher {voucher.code} berhasil diterapkan.')
    else:
        if 'voucher_code' in request.session:
            del request.session['voucher_code']
        if 'product_voucher_id' in request.session:
            del request.session['product_voucher_id']
        messages.error(request, error or 'Voucher tidak valid.')

    return redirect('carts:detail')


@login_required
@customer_required
@require_POST
def remove_voucher(request):
    if 'voucher_code' in request.session:
        del request.session['voucher_code']
    if 'product_voucher_id' in request.session:
        del request.session['product_voucher_id']
    if 'shipping_voucher_id' in request.session:
        del request.session['shipping_voucher_id']
    messages.success(request, 'Voucher berhasil dihapus.')
    return redirect('carts:detail')


@login_required
@customer_required
@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_available=True)
    variant_id = request.POST.get('variant_id')
    variant = None
    if variant_id:
        variant = get_object_or_404(ProductVariant, id=variant_id, product=product, is_available=True)

    max_stock = variant.stock if variant else product.stock

    cart = get_or_create_cart(request)
    qty = request.POST.get('quantity', 1)
    try:
        qty = int(qty)
        if qty < 1:
            qty = 1
    except (ValueError, TypeError):
        qty = 1

    if qty > max_stock:
        label = f'{product.name} ({variant.size_ml}ml)' if variant else product.name
        messages.error(request, f'Stok {label} tidak mencukupi. Stok tersedia: {max_stock}')
        next_url = request.POST.get('next') or request.GET.get('next') or 'carts:detail'
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
            return redirect(next_url)
        return redirect('carts:detail')

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, variant=variant,
        defaults={'quantity': qty}
    )
    if not created:
        new_qty = min(cart_item.quantity + qty, max_stock)
        cart_item.quantity = new_qty
        cart_item.save()
        label = f'{product.name} ({variant.size_ml}ml)' if variant else product.name
        messages.info(request, f'Jumlah {label} di keranjang: {new_qty}')
    else:
        label = f'{product.name} ({variant.size_ml}ml)' if variant else product.name
        messages.success(request, f'{label} ditambahkan ke keranjang')

    next_url = request.POST.get('next') or request.GET.get('next') or 'carts:detail'
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
        return redirect(next_url)
    return redirect('carts:detail')


@login_required
@customer_required
@require_POST
def cart_update(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    action = request.POST.get('action', 'set')
    max_stock = get_cart_item_stock(cart_item)

    if action == 'increase':
        new_qty = min(cart_item.quantity + 1, max_stock)
    elif action == 'decrease':
        new_qty = cart_item.quantity - 1
    else:
        raw = request.POST.get('quantity', cart_item.quantity)
        try:
            new_qty = int(raw)
        except (ValueError, TypeError):
            new_qty = cart_item.quantity

    new_qty = max(new_qty, 0)

    if new_qty == 0:
        name = str(cart_item)
        cart_item.delete()
        messages.success(request, f'{name} dihapus dari keranjang')
    else:
        cart_item.quantity = min(new_qty, max_stock)
        cart_item.save()
        messages.info(request, f'Jumlah {cart_item} diperbarui')

    return redirect('carts:detail')


@login_required
@customer_required
@require_POST
def cart_remove(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = str(cart_item)
    cart_item.delete()
    messages.success(request, f'{product_name} dihapus dari keranjang')
    return redirect('carts:detail')



