"""
Stripe webhook handler for Airport API
Automatically confirms orders when payment succeeds
"""
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
from django.db import transaction
import stripe

from airport.models import Order, Ticket


@csrf_exempt
def stripe_webhook(request):
    """
    Stripe webhook endpoint to handle payment events.
    Automatically confirms orders when payment succeeds.
    
    Events handled:
    - payment_intent.succeeded: Auto-confirm order and create ticket
    - payment_intent.payment_failed: Mark payment as failed
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponse('Webhook secret not configured', status=500)
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(f'Invalid payload: {e}', status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(f'Invalid signature: {e}', status=400)
    
    # Handle payment_intent.succeeded
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        order_id = payment_intent['metadata'].get('order_id')
        
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                
                # Check if already confirmed (idempotency)
                if order.status == 'confirmed':
                    print(f"ℹ️ Order {order_id} already confirmed, skipping")
                    return HttpResponse(status=200)
                
                # Auto-confirm order
                with transaction.atomic():
                    order.status = 'confirmed'
                    order.payment_status = 'succeeded'
                    order.save()
                    
                    # Create ticket if not exists
                    if not hasattr(order, 'ticket'):
                        Ticket.objects.create(
                            order=order,
                            flight=order.flight,
                            user=order.user,
                            seat_number=order.seat_number,
                            status='active'
                        )
                        print(f"✅ Order {order_id} auto-confirmed via webhook + ticket created")
                    else:
                        print(f"✅ Order {order_id} auto-confirmed via webhook (ticket exists)")
                
            except Order.DoesNotExist:
                print(f"❌ Order {order_id} not found in webhook")
                return HttpResponse(f'Order {order_id} not found', status=404)
            except Exception as e:
                print(f"❌ Error processing webhook for order {order_id}: {e}")
                return HttpResponse(f'Error: {e}', status=500)
    
    # Handle payment_intent.payment_failed
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        order_id = payment_intent['metadata'].get('order_id')
        
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                order.payment_status = 'failed'
                order.save()
                print(f"⚠️ Payment failed for Order {order_id}")
            except Order.DoesNotExist:
                print(f"❌ Order {order_id} not found in webhook")
    
    # Handle payment_intent.canceled
    elif event['type'] == 'payment_intent.canceled':
        payment_intent = event['data']['object']
        order_id = payment_intent['metadata'].get('order_id')
        
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                if order.status == 'pending':
                    order.status = 'cancelled'
                    order.payment_status = 'canceled'
                    order.save()
                    print(f"ℹ️ Order {order_id} cancelled via webhook")
            except Order.DoesNotExist:
                pass
    
    return HttpResponse(status=200)
