"""
Stripe webhook handler for Airport API
Automatically confirms orders when payment succeeds

Events handled:
- payment_intent.succeeded        → confirm order + create ticket
- payment_intent.payment_failed   → mark payment failed
- payment_intent.canceled         → cancel or expire order
- payment_intent.requires_action  → expire if reservation passed
- checkout.session.completed      → confirm order + create ticket (Checkout flow)
- checkout.session.expired        → mark order as expired (Checkout flow)
"""
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
from django.db import transaction
import stripe

from airport.models import Order, Ticket


def _confirm_order(order, order_id):
    """Shared helper: confirm order and create ticket if not exists."""
    if order.status == 'confirmed':
        print(f"ℹ️ Order {order_id} already confirmed, skipping")
        return

    with transaction.atomic():
        order.status = 'confirmed'
        order.payment_status = 'succeeded'
        order.save()

        if not hasattr(order, 'ticket'):
            Ticket.objects.create(
                order=order,
                flight=order.flight,
                user=order.user,
                seat_number=order.seat_number,
                status='active'
            )
            print(f"✅ Order {order_id} confirmed + ticket created")
        else:
            print(f"✅ Order {order_id} confirmed (ticket already exists)")


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponse('Webhook secret not configured', status=500)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(f'Invalid payload: {e}', status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(f'Invalid signature: {e}', status=400)

    event_type = event['type']

    # ── payment_intent.succeeded ──────────────────────────────────────────────
    if event_type == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        order_id = payment_intent['metadata'].get('order_id')

        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                _confirm_order(order, order_id)
            except Order.DoesNotExist:
                print(f"❌ Order {order_id} not found")
                return HttpResponse(f'Order {order_id} not found', status=404)
            except Exception as e:
                print(f"❌ Error processing order {order_id}: {e}")
                return HttpResponse(f'Error: {e}', status=500)

    # ── payment_intent.payment_failed ─────────────────────────────────────────
    elif event_type == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        order_id = payment_intent['metadata'].get('order_id')

        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                order.payment_status = 'failed'
                order.save()
                print(f"⚠️ Payment failed for Order {order_id}")
            except Order.DoesNotExist:
                print(f"❌ Order {order_id} not found")

    # ── payment_intent.canceled ───────────────────────────────────────────────
    elif event_type == 'payment_intent.canceled':
        payment_intent = event['data']['object']
        order_id = payment_intent['metadata'].get('order_id')
        cancellation_reason = payment_intent.get('cancellation_reason')

        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                if order.status == 'pending':
                    if cancellation_reason == 'automatic':
                        order.status = 'expired'
                        order.payment_status = 'canceled'
                        order.save()
                        print(f"⏰ Order {order_id} expired (Stripe auto-canceled)")
                    else:
                        order.status = 'cancelled'
                        order.payment_status = 'canceled'
                        order.save()
                        print(f"ℹ️ Order {order_id} cancelled (reason: {cancellation_reason})")
            except Order.DoesNotExist:
                pass

    # ── payment_intent.requires_action ───────────────────────────────────────
    elif event_type == 'payment_intent.requires_action':
        payment_intent = event['data']['object']
        order_id = payment_intent['metadata'].get('order_id')

        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                if order.status == 'pending' and order.is_expired():
                    order.status = 'expired'
                    order.save()
                    print(f"⏰ Order {order_id} expired (reservation passed during 3DS)")
            except Order.DoesNotExist:
                pass

    # ── checkout.session.completed ────────────────────────────────────────────
    elif event_type == 'checkout.session.completed':
        session = event['data']['object']
        order_id = session['metadata'].get('order_id')

        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                # Update payment_intent_id from session if not already set
                if session.get('payment_intent') and not order.payment_intent_id:
                    order.payment_intent_id = session['payment_intent']
                _confirm_order(order, order_id)
            except Order.DoesNotExist:
                print(f"❌ Order {order_id} not found in checkout.session.completed")
                return HttpResponse(f'Order {order_id} not found', status=404)
            except Exception as e:
                print(f"❌ Error processing checkout session for order {order_id}: {e}")
                return HttpResponse(f'Error: {e}', status=500)

    # ── checkout.session.expired ──────────────────────────────────────────────
    elif event_type == 'checkout.session.expired':
        session = event['data']['object']
        order_id = session['metadata'].get('order_id')

        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                if order.status == 'pending':
                    order.status = 'expired'
                    order.payment_status = 'expired'
                    order.save()
                    print(f"⏰ Order {order_id} expired (Stripe Checkout Session expired)")
            except Order.DoesNotExist:
                print(f"❌ Order {order_id} not found in checkout.session.expired")

    return HttpResponse(status=200)
