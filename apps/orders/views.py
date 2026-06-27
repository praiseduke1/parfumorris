from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from django.views.decorators.http import require_POST

from apps.accounts.models import CustomerAddress
from apps.core.decorators import customer_required
from .forms import CheckoutForm
from .models import Order, OrderItem
from apps.carts.models import Cart
from apps.promotions.models import UserVoucher, Voucher as PromoVoucher
from apps.promotions.views import (
    calculate_subtotal, calculate_shipping_cost as calc_shipping_cost,
    calculate_product_discount, calculate_shipping_discount, calculate_total,
    _get_session_voucher_ids, _set_session_voucher_ids,
)
from apps.shipping.models import ShippingConfig


@customer_required
def order_create(request):
    if not request.user.is_authenticated:
        return redirect('accounts:member_benefits')

    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.items.exists():
        messages.warning(request, 'Keranjang belanja kosong')
        return redirect('carts:detail')

    cart_items = cart.items.select_related('product', 'variant').all()
    subtotal = calculate_subtotal(cart)
    total_items = cart.total_items()

    product_voucher_obj = None
    shipping_voucher_obj = None
    product_discount = 0
    shipping_discount = 0

    shipping_info = request.session.get('shipping', {})
    shipping_cost_val = calc_shipping_cost(shipping_info)

    pv_id, sv_id = _get_session_voucher_ids(request)

    if pv_id:
        product_discount, product_voucher_obj = calculate_product_discount(
            subtotal, pv_id, request.user
        )
    if sv_id:
        shipping_discount, shipping_voucher_obj = calculate_shipping_discount(
            shipping_cost_val, sv_id, subtotal, request.user
        )

    discount_amount = product_discount + shipping_discount

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            for cart_item in cart_items:
                max_stock = cart_item.variant.stock if cart_item.variant else cart_item.product.stock
                if cart_item.quantity > max_stock:
                    label = f'{cart_item.product.name} ({cart_item.variant.size_ml}ml)' if cart_item.variant else cart_item.product.name
                    messages.error(
                        request,
                        f'Stok {label} tidak mencukupi. '
                        f'Tersedia: {max_stock}'
                    )
                    return redirect('carts:detail')

            if not shipping_info or not shipping_info.get('courier_code'):
                messages.error(request, 'Pilih layanan pengiriman terlebih dahulu.')
                final_total = subtotal - discount_amount
                addresses = CustomerAddress.objects.filter(user=request.user)
                context = {
                    'form': form, 'cart': cart, 'cart_items': cart_items,
                    'subtotal': subtotal, 'total_items': total_items,
                    'discount_amount': discount_amount,
                    'product_discount': product_discount,
                    'shipping_discount': shipping_discount,
                    'product_voucher_id': pv_id,
                    'shipping_voucher_id': sv_id,
                    'final_total': final_total,
                    'addresses': addresses,
                    'shipping_info': shipping_info,
                }
                return render(request, 'orders/order_create.html', context)

            shipping_cost = int(shipping_info.get('cost', 0))

            # Recalculate discounts with current shipping cost
            if shipping_voucher_obj and shipping_cost > 0:
                shipping_discount = shipping_voucher_obj.calculate_discount(shipping_cost)
            elif shipping_voucher_obj and shipping_cost <= 0:
                shipping_discount = 0
            discount_amount = product_discount + shipping_discount

            grand_total = calculate_total(subtotal, shipping_cost, product_discount, shipping_discount)

            order = form.save(commit=False)
            order.user = request.user
            order.subtotal = subtotal
            order.discount_amount = discount_amount
            order.product_discount = product_discount
            order.shipping_discount = shipping_discount
            order.product_voucher = product_voucher_obj
            order.shipping_voucher = shipping_voucher_obj
            order.shipping_cost = shipping_cost
            order.shipping_courier = shipping_info.get('courier_code', '')
            order.shipping_service = shipping_info.get('service', '')
            order.shipping_estimation = shipping_info.get('etd', '')
            order.shipping_weight = 0
            order.shipping_origin = ''
            order.shipping_destination = ''
            order.total_price = grand_total
            order.save()

            cart_weight = sum(
                ((item.variant.weight if item.variant else None) or item.product.weight or 500) * item.quantity
                for item in cart_items
            )
            order.shipping_weight = cart_weight
            config = ShippingConfig.get_config()
            order.shipping_origin = f'{config.origin_district}, {config.origin_city}'
            dst_city = form.cleaned_data.get('city')
            dst_district = form.cleaned_data.get('district')
            if dst_city and dst_district:
                order.shipping_destination = f'{dst_district.name}, {dst_city.name}'
            order.save(update_fields=[
                'shipping_weight', 'shipping_origin', 'shipping_destination',
            ])

            for cart_item in cart_items:
                unit_price = cart_item.variant.price if cart_item.variant else cart_item.product.price
                variant_name = f'{cart_item.variant.size_ml}ml' if cart_item.variant else ''
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    variant=cart_item.variant,
                    product_name=cart_item.product.name,
                    variant_name=variant_name,
                    price=unit_price,
                    quantity=cart_item.quantity,
                )

            cart.items.all().delete()

            # Mark product voucher as used
            if product_voucher_obj:
                uv = UserVoucher.objects.filter(
                    user=request.user, voucher=product_voucher_obj,
                    status=UserVoucher.Status.AVAILABLE,
                ).first()
                if uv:
                    uv.status = UserVoucher.Status.USED
                    uv.used_at = now()
                    uv.save()
                else:
                    PromoVoucher.objects.filter(pk=product_voucher_obj.pk).update(
                        used_count=F('used_count') + 1
                    )

            # Mark shipping voucher as used
            if shipping_voucher_obj:
                uv = UserVoucher.objects.filter(
                    user=request.user, voucher=shipping_voucher_obj,
                    status=UserVoucher.Status.AVAILABLE,
                ).first()
                if uv:
                    uv.status = UserVoucher.Status.USED
                    uv.used_at = now()
                    uv.save()
                else:
                    PromoVoucher.objects.filter(pk=shipping_voucher_obj.pk).update(
                        used_count=F('used_count') + 1
                    )

            if 'product_voucher_id' in request.session:
                del request.session['product_voucher_id']
            if 'shipping_voucher_id' in request.session:
                del request.session['shipping_voucher_id']
            if 'shipping' in request.session:
                del request.session['shipping']

            return redirect('payments:checkout', order_id=order.id)

        final_total = subtotal - discount_amount
        if shipping_info:
            final_total += int(shipping_info.get('cost', 0))
    else:  # GET
        addresses = CustomerAddress.objects.filter(user=request.user)
        initial = {}
        default_addr = addresses.filter(is_default=True).first()
        if default_addr:
            initial = {
                'recipient_name': default_addr.recipient_name,
                'phone': default_addr.phone,
                'shipping_address': default_addr.address_line,
                'province': default_addr.province_id,
                'city': default_addr.city_id,
                'district': default_addr.district_id,
                'postal_code': default_addr.postal_code_id,
            }
        elif not default_addr:
            try:
                profile = request.user.profile
                initial = {
                    'recipient_name': request.user.get_full_name() or request.user.username,
                    'phone': profile.phone,
                }
            except AttributeError:
                initial = {
                    'recipient_name': request.user.get_full_name() or request.user.username,
                }
        form = CheckoutForm(initial=initial)

        final_total = subtotal - discount_amount
        if shipping_info:
            final_total += int(shipping_info.get('cost', 0))

    addresses = CustomerAddress.objects.filter(user=request.user)
    import json

    context = {
        'form': form,
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'total_items': total_items,
        'discount_amount': discount_amount,
        'product_discount': product_discount,
        'shipping_discount': shipping_discount,
        'product_voucher_id': pv_id,
        'shipping_voucher_id': sv_id,
        'product_voucher_id_json': json.dumps(pv_id) if pv_id else 'null',
        'shipping_voucher_id_json': json.dumps(sv_id) if sv_id else 'null',
        'final_total': final_total,
        'addresses': addresses,
        'shipping_info': shipping_info,
    }
    return render(request, 'orders/order_create.html', context)


@login_required
@customer_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {
        'order': order,
        'order_items': order.items.all(),
    }
    return render(request, 'orders/order_detail.html', context)


@login_required
@customer_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    context = {'orders': orders}
    return render(request, 'orders/order_list.html', context)


@login_required
@customer_required
@require_POST
def order_cancel(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status != Order.Status.PENDING_PAYMENT:
        messages.error(request, 'Pesanan tidak dapat dibatalkan karena sudah diproses.')
        return redirect('orders:detail', order_id=order.id)

    order.status = Order.Status.CANCELLED
    order.save()
    messages.success(request, f'Pesanan {order.order_number} berhasil dibatalkan.')
    return redirect('orders:detail', order_id=order.id)


@login_required
@customer_required
@require_POST
def order_confirm_received(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status != Order.Status.DELIVERED:
        messages.error(request, 'Pesanan hanya dapat dikonfirmasi saat status "Pesanan Sampai".')
        return redirect('orders:detail', order_id=order.id)

    order.status = Order.Status.COMPLETED
    order.save()
    messages.success(request, 'Pesanan berhasil diselesaikan. Terima kasih telah berbelanja di Morris Parfum.')
    return redirect('orders:detail', order_id=order.id)


@login_required
@customer_required
def order_track(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    history = {h.status: h for h in order.status_history.all()}

    ALL_STATUSES = ['pending_payment', 'paid', 'processing', 'shipped', 'delivered', 'completed']

    if order.status == Order.Status.CANCELLED:
        non_cancel = [h for h in order.status_history.all() if h.status != Order.Status.CANCELLED]
        if non_cancel:
            last_active = non_cancel[-1].status
            try:
                status_order = ALL_STATUSES[:ALL_STATUSES.index(last_active) + 1]
            except ValueError:
                status_order = ALL_STATUSES[:4]
        else:
            status_order = ['pending_payment']
    else:
        status_order = ALL_STATUSES[:]

    current_idx = None
    for i, s in enumerate(status_order):
        if s == order.status:
            current_idx = i
            break

    if order.status == Order.Status.CANCELLED and current_idx is None and status_order:
        current_idx = len(status_order) - 1

    timeline = []
    for i, s in enumerate(status_order):
        entry = history.get(s)
        is_current = s == order.status and order.status != 'cancelled'
        is_future = current_idx is not None and i > current_idx
        is_active = current_idx is not None and i <= current_idx
        timeline.append({
            'status': s,
            'entry': entry,
            'is_active': is_active,
            'is_current': is_current,
            'is_future': is_future,
        })

    context = {
        'order': order,
        'timeline': timeline,
    }
    return render(request, 'orders/order_track.html', context)
