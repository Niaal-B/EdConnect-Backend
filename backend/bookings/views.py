from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from auth.authentication import CookieJWTAuthentication
import stripe
from django.conf import settings
from django.db import transaction 
from django.shortcuts import get_object_or_404 
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST   
from django.http import JsonResponse, HttpResponse


from bookings.models import Booking
from bookings.serializers import BookingSerializer
from mentors.models import Slot
from users.models import User
from rest_framework.views import APIView

stripe.api_key = settings.STRIPE_SECRET_KEY

class BookingCreateAPIView(generics.CreateAPIView):
    serializer_class = BookingSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        slot_id = request.data.get('slot_id')

        if not slot_id:
            return Response({"detail": "slot_id is required."},
                            status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            try:
                slot = Slot.objects.select_for_update().get(id=slot_id, status='available')

                mentor = slot.mentor
                if request.user == mentor:
                    return Response({"detail": "Mentors cannot book their own slots."},
                                    status=status.HTTP_400_BAD_REQUEST)

                booking = Booking.objects.create(
                    student=request.user, 
                    mentor=mentor,  
                    slot=slot,         
                    booked_start_time=slot.start_time,
                    booked_end_time=slot.end_time,
                    booked_fee=slot.fee,
                    booked_timezone=slot.timezone,
                    status='PENDING_PAYMENT', 
                    payment_status='PENDING'  
                )

                product_name = f'Mentorship Session with {mentor.id}'
                product_description = (
                    f'{slot.start_time.strftime("%Y-%m-%d %H:%M")} - '
                    f'{slot.end_time.strftime("%H:%M")} ({slot.timezone})'
                )

                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'], 
                    line_items=[
                        {
                            'price_data': {
                                'currency': 'usd', 
                                'unit_amount': int(slot.fee * 100), 
                                'product_data': {
                                    'name': product_name,
                                    'description': product_description,
                                },
                            },
                            'quantity': 1,
                        },
                    ],
                    mode='payment', 
                    success_url=f'http://localhost:3000/booking/success?session_id={{CHECKOUT_SESSION_ID}}',
                    cancel_url='http://localhost:3000/booking/cancel',

                    client_reference_id=str(booking.id),
                    metadata={
                        'booking_id': str(booking.id),
                        'mentor_id': str(mentor.id),
                        'student_id': str(request.user.id),
                        'slot_id': str(slot.id),
                    },
                    customer_email=request.user.email,
                )
                booking.stripe_checkout_session_id = checkout_session.id
                booking.save()

                return Response({
                    "message": "Booking initiated, redirecting to payment.",
                    "stripe_checkout_url": checkout_session.url,
                    "booking_id": str(booking.id)
                }, status=status.HTTP_201_CREATED)

            except Slot.DoesNotExist:
                return Response({"detail": "Selected slot is not available or does not exist."},
                                status=status.HTTP_404_NOT_FOUND)
            except User.DoesNotExist:
                return Response({"detail": "Mentor not found for the selected slot."},
                                status=status.HTTP_404_NOT_FOUND)
            except stripe.error.StripeError as e:
                return Response({"detail": f"Payment initiation failed: {e.user_message or 'Stripe API error'}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                print(e)
                return Response({"detail": "An unexpected error occurred during booking."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class BookingStatusAPIView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id, *args, **kwargs):
        booking = get_object_or_404(Booking, stripe_checkout_session_id=session_id)

        if request.user != booking.student and request.user != booking.mentor:
            return Response({"detail": "You do not have permission to view this booking."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)



@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object'] 

        booking_id = session.get('metadata', {}).get('booking_id')
        slot_id = session.get('metadata', {}).get('slot_id')
        payment_intent_id = session.get('payment_intent') 

        if booking_id:
            with transaction.atomic():
                try:
                    booking = Booking.objects.select_for_update().get(id=booking_id)
                    slot = Slot.objects.select_for_update().get(id=slot_id)

                    # Update Booking status
                    if booking.status == 'PENDING_PAYMENT' and booking.payment_status == 'PENDING':
                        booking.status = 'CONFIRMED'
                        booking.payment_status = 'PAID'
                        booking.stripe_payment_intent_id = payment_intent_id 
                        booking.save()

                        # Update Slot status
                        if slot.status == 'available': 
                            slot.status = 'booked'
                            slot.save()
                        elif slot.status == 'booked':
                            # Slot might have been booked by another means or already updated.
                            # Log this as an informational message rather than an error.
                            print(f"Webhook: Slot {slot_id} already marked booked. Booking {booking_id} confirmed.")
                        else:
                             # Handle other unexpected slot statuses if needed
                            print(f"Webhook: Slot {slot_id} has unexpected status {slot.status}. Booking {booking_id} confirmed.")


                    print(f"Booking {booking_id} and Slot {slot_id} updated to CONFIRMED/booked via webhook.")
                except Booking.DoesNotExist:
                    print(f"Webhook: Booking with ID {booking_id} not found.")
                    return HttpResponse(status=404)
                except Slot.DoesNotExist:
                    print(f"Webhook: Slot with ID {slot_id} not found for booking {booking_id}.")
                    return HttpResponse(status=404)
                except Exception as e:
                    print(f"Webhook processing error for booking {booking_id}: {e}")
                    return HttpResponse(status=500)
        else:
            print("Webhook received without booking_id in metadata. Session ID:", session.id)

    elif event['type'] == 'payment_intent.succeeded':

        pass

    return HttpResponse(status=200)
