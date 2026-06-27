import hashlib
import time

import requests
import midtransclient
from django.conf import settings


MIDTRANS_TIMEOUT = 15


class _TimeoutRequests:
    """Wrapper that injects a default timeout into requests made by midtransclient."""

    def request(self, method, url, **kwargs):
        kwargs.setdefault('timeout', MIDTRANS_TIMEOUT)
        return requests.request(method, url, **kwargs)


def get_snap():
    snap = midtransclient.Snap(
        is_production=settings.MIDTRANS_IS_PRODUCTION,
        server_key=settings.MIDTRANS_SERVER_KEY,
    )
    snap.http_client.http_client = _TimeoutRequests()
    return snap


MIDTRANS_RETRIES = 3
MIDTRANS_RETRY_DELAY = 1


def _retry_request(fn, *args, **kwargs):
    for attempt in range(MIDTRANS_RETRIES):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if attempt < MIDTRANS_RETRIES - 1:
                time.sleep(MIDTRANS_RETRY_DELAY * (2 ** attempt))
                continue
            raise


def create_transaction(order):
    snap = get_snap()

    item_details = []
    for item in order.items.select_related('product').all():
        item_details.append({
            'id': str(item.product_id),
            'price': int(item.price),
            'quantity': item.quantity,
            'name': item.product_name[:50],
        })

    discount_amount = int(order.discount_amount)
    if discount_amount > 0:
        item_details.append({
            'id': 'DISCOUNT',
            'price': -discount_amount,
            'quantity': 1,
            'name': 'Diskon Voucher',
        })

    shipping_cost = int(order.shipping_cost)
    if shipping_cost > 0:
        item_details.append({
            'id': 'SHIPPING',
            'price': shipping_cost,
            'quantity': 1,
            'name': 'Ongkos Kirim',
        })

    param = {
        'transaction_details': {
            'order_id': f'ORDER-{order.midtrans_order_id}',
            'gross_amount': int(order.total_price),
        },
        'item_details': item_details,
        'customer_details': {
            'first_name': order.recipient_name[:20],
            'phone': order.phone,
            'email': order.user.email or '',
            'shipping_address': {
                'first_name': order.recipient_name[:20],
                'phone': order.phone,
                'address': order.shipping_address,
                'city': order.city,
                'postal_code': order.postal_code,
            },
        },
        'callbacks': {
            'finish': f'{settings.BASE_URL}/payment/finish/{order.id}/',
            'unfinish': f'{settings.BASE_URL}/payment/unfinish/{order.id}/',
            'error': f'{settings.BASE_URL}/payment/error/{order.id}/',
        },
    }

    transaction = _retry_request(snap.create_transaction, param)
    return transaction


def get_transaction_status(order):
    snap = get_snap()
    status = _retry_request(snap.transactions.status, f'ORDER-{order.midtrans_order_id}')
    return status


def verify_signature(order_id, status_code, gross_amount, signature_key):
    data = f'{order_id}{status_code}{gross_amount}{settings.MIDTRANS_SERVER_KEY}'
    computed = hashlib.sha512(data.encode()).hexdigest()
    return computed == signature_key
