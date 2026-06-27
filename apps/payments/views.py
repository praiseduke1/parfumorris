import json
import uuid
from datetime import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import Http404, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.timezone import make_aware
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.core.decorators import customer_required
from .models import Payment
from .midtrans import create_transaction, get_transaction_status, verify_signature
from apps.accounts.models import MemberProfile
from apps.orders.models import Order, OrderItem
from apps.products.models import Product, ProductVariant


ORDER_ID_PREFIX = 'ORDER-'


def _parse_order_id(raw_order_id):
    if raw_order_id and raw_order_id.startswith(ORDER_ID_PREFIX):
        return raw_order_id.removeprefix(ORDER_ID_PREFIX)
    return raw_order_id


@login_required
@customer_required
def checkout(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status not in (Order.Status.PENDING_PAYMENT,):
        return render(request, 'payments/error.html', {
            'error': 'Pesanan ini sudah dibayar atau dibatalkan.',
            'order': order,
        })

    payment, created = Payment.objects.get_or_create(order=order)

    if not payment.snap_token:
        try:
            result = create_transaction(order)
            payment.snap_token = result['token']
            payment.snap_redirect_url = result['redirect_url']
            payment.amount = order.total_price
            payment.save()
        except Exception as e:
            return render(request, 'payments/error.html', {
                'error': f'Gagal terhubung ke Midtrans: {e}',
                'order': order,
            })

    context = {
        'order': order,
        'payment': payment,
        'client_key': settings.MIDTRANS_CLIENT_KEY,
    }
    return render(request, 'payments/checkout.html', context)


def _ensure_order_owner(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if not request.user.is_authenticated:
        return redirect(f'{reverse(settings.LOGIN_URL)}?next={reverse("orders:detail", args=[order_id])}')
    if request.user != order.user:
        raise Http404
    return order


def _process_successful_payment(payment, order, status_data):
    with transaction.atomic():
        was_paid_before = (payment.status == Payment.PaymentStatus.SUCCESS)
        payment.transaction_id = status_data.get('transaction_id', payment.transaction_id)
        payment.payment_method = status_data.get('payment_type', payment.payment_method)
        payment.fraud_status = status_data.get('fraud_status', payment.fraud_status)
        payment.raw_response = status_data
        transaction_time = status_data.get('transaction_time', '')
        if transaction_time:
            try:
                payment.payment_time = make_aware(
                    datetime.strptime(transaction_time, '%Y-%m-%d %H:%M:%S')
                )
            except (ValueError, TypeError):
                pass
        payment.status = Payment.PaymentStatus.SUCCESS
        order.status = Order.Status.PAID
        payment.save()
        order.save()

        if not was_paid_before:
            for item in OrderItem.objects.filter(order=order).select_related('variant'):
                Product.objects.filter(id=item.product_id).update(
                    stock=F('stock') - item.quantity
                )
                if item.variant:
                    ProductVariant.objects.filter(id=item.variant_id).update(
                        stock=F('stock') - item.quantity
                    )
            try:
                member = MemberProfile.objects.get(user=order.user)
                member.total_spending += order.total_price
                member.save(update_fields=['total_spending'])
                member.earn_points(order.total_price)
                member.upgrade_level()
            except MemberProfile.DoesNotExist:
                pass


@login_required
@customer_required
def payment_finish(request, order_id):
    result = _ensure_order_owner(request, order_id)
    if not isinstance(result, Order):
        return result
    order = result
    payment = get_object_or_404(Payment, order=order)

    verified = False
    try:
        status_data = get_transaction_status(order)
        tx_status = status_data.get('transaction_status')
        if tx_status in ('capture', 'settlement'):
            _process_successful_payment(payment, order, status_data)
            verified = True
        elif tx_status in ('deny', 'cancel', 'expire'):
            payment.status = Payment.PaymentStatus.FAILED
            payment.raw_response = status_data
            order.status = Order.Status.CANCELLED
            payment.save()
            order.save()
        return render(request, 'payments/success.html' if verified else 'payments/error.html', {
            'order': order,
            'payment': payment,
        })
    except Exception:
        pass

    context = {
        'order': order,
        'payment': payment,
        'verified': verified,
    }
    return render(request, 'payments/success.html', context)


@login_required
@customer_required
def payment_unfinish(request, order_id):
    result = _ensure_order_owner(request, order_id)
    if not isinstance(result, Order):
        return result
    order = result
    return render(request, 'payments/unfinish.html', {'order': order})


@login_required
@customer_required
def payment_error(request, order_id):
    result = _ensure_order_owner(request, order_id)
    if not isinstance(result, Order):
        return result
    order = result
    return render(request, 'payments/error.html', {'order': order})


@csrf_exempt
@require_POST
def payment_notification(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse('Invalid JSON', status=400)

    raw_order_id = body.get('order_id', '')
    parsed_order_id = _parse_order_id(raw_order_id)
    transaction_status = body.get('transaction_status', '')
    transaction_id = body.get('transaction_id', '')
    payment_type = body.get('payment_type', '')
    fraud_status = body.get('fraud_status', '')
    transaction_time = body.get('transaction_time', '')
    status_code = body.get('status_code', '')
    gross_amount = body.get('gross_amount', '')
    signature_key = body.get('signature_key', '')

    if not parsed_order_id or not transaction_status:
        return HttpResponse('Missing required fields', status=400)

    try:
        uuid.UUID(parsed_order_id)
    except (ValueError, AttributeError):
        return HttpResponse('Not Found', status=404)

    if not verify_signature(raw_order_id, status_code, gross_amount, signature_key):
        return HttpResponse('Invalid signature', status=403)

    try:
        order = Order.objects.get(midtrans_order_id=parsed_order_id)
        payment = Payment.objects.get(order=order)
    except (Order.DoesNotExist, Payment.DoesNotExist):
        return HttpResponse('Not Found', status=404)

    if str(int(order.total_price)) != str(gross_amount):
        return HttpResponse('Amount mismatch', status=400)

    payment.transaction_id = transaction_id
    payment.payment_method = payment_type
    payment.fraud_status = fraud_status
    payment.raw_response = body

    if transaction_time:
        try:
            payment.payment_time = make_aware(
                datetime.strptime(transaction_time, '%Y-%m-%d %H:%M:%S')
            )
        except (ValueError, TypeError):
            pass

    if transaction_status == 'capture' and fraud_status == 'accept':
        _process_successful_payment(payment, order, body)
    elif transaction_status == 'settlement':
        _process_successful_payment(payment, order, body)
    elif transaction_status in ('deny', 'cancel', 'expire'):
        payment.status = Payment.PaymentStatus.FAILED
        payment.save()
        order.status = Order.Status.CANCELLED
        order.save()
    elif transaction_status == 'pending':
        payment.status = Payment.PaymentStatus.PENDING
        payment.save()

    return HttpResponse('OK')
