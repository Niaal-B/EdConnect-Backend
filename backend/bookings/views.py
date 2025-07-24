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
from django.db.models import Q
from django.utils import timezone 



from bookings.models import Booking
from bookings.serializers import BookingSerializer,MentorBookingsSerializer
from mentors.models import Slot
from users.models import User
from rest_framework.views import APIView
from notifications.tasks import send_realtime_notification_task

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


class StudentBookingsAPIView(generics.ListAPIView):
    serializer_class = BookingSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Booking.objects.filter(
            Q(student=user) &
            Q(status__in=['CONFIRMED']) & 
            Q(payment_status__in=['PAID'])
        ).select_related('slot__mentor').order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({"message": "No confirmed bookings found for this student."}, status=status.HTTP_200_OK)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)        

class MentorBookingsAPIView(generics.ListAPIView):
    serializer_class = MentorBookingsSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Booking.objects.filter(
            mentor=user,status__in=['CONFIRMED'],payment_status__in=['PAID']).select_related('student').order_by('-created_at')





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


class BookingCancelAPIView(generics.UpdateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ['patch']

    def patch(self, request, *args, **kwargs):
        booking = self.get_object()

        if booking.status != 'CONFIRMED' or booking.payment_status != 'PAID':
            return Response({"detail": "Only confirmed and paid bookings can be cancelled."},
                            status=status.HTTP_400_BAD_REQUEST)

        cancelling_user = request.user
        if not (cancelling_user == booking.student or cancelling_user == booking.mentor):
            return Response({"detail": "You do not have permission to cancel this booking."},
                            status=status.HTTP_403_FORBIDDEN)

        now = timezone.now()
        if now >= booking.booked_end_time:
            return Response({"detail": "Cannot cancel a session that has already ended or passed."},
                            status=status.HTTP_400_BAD_REQUEST)

        refund_amount_cents = 0
        booking_new_status = ''
        cancellation_reason = request.data.get('reason', 'N/A')

        with transaction.atomic():
            try:
                slot = Slot.objects.select_for_update().get(id=booking.slot.id)

                if cancelling_user == booking.student:
                    time_until_session = booking.booked_start_time - now
                    hours_until_session = time_until_session.total_seconds() / 3600

                    if hours_until_session >= 24:
                        refund_amount_cents = int(booking.booked_fee * 100)
                        booking_new_status = 'CANCELED_BY_STUDENT_FULL_REFUND'
                    else:
                        refund_amount_cents = 0
                        booking_new_status = 'CANCELED_BY_STUDENT_NO_REFUND'

                elif cancelling_user == booking.mentor:
                    refund_amount_cents = int(booking.booked_fee * 100)
                    booking_new_status = 'CANCELED_BY_MENTOR'

                if refund_amount_cents > 0:
                    if not booking.stripe_payment_intent_id:
                        raise ValueError("Booking has no payment intent ID for refund.")
                    
                    refund = stripe.Refund.create(
                        payment_intent=booking.stripe_payment_intent_id,
                        amount=refund_amount_cents,
                        reason='requested_by_customer',
                        metadata={
                            'booking_id': str(booking.id),
                            'cancelled_by_user_id': str(cancelling_user.id),
                            'cancellation_reason': cancellation_reason,
                            'refund_type': booking_new_status
                        }
                    )
                    booking.stripe_refund_id = refund.id 
                    booking.payment_status = 'REFUNDED' if refund.status == 'succeeded' else 'REFUND_FAILED' 
                else:
                    booking.payment_status = 'NO_REFUND'

                booking.status = booking_new_status
                booking.cancellation_reason = cancellation_reason 
                booking.cancelled_by = cancelling_user 
                booking.cancelled_at = now
                booking.save()

                slot.status = 'unavailable' 
                slot.save()

                #need to create task to remove the event from calendar
                #need to create task to send notification


                return Response({
                    "message": "Booking cancelled successfully.",
                    "booking_status": booking.status,
                    "refund_amount": refund_amount_cents / 100.0,
                    "stripe_refund_id": getattr(booking, 'stripe_refund_id', None)
                }, status=status.HTTP_200_OK)

            except Booking.DoesNotExist:
                return Response({"detail": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)

            except Slot.DoesNotExist:
                return Response({"detail": "Associated slot not found."}, status=status.HTTP_404_NOT_FOUND)

            except stripe.error.StripeError as e:
                return Response({"detail": f"Cancellation failed due to payment processing error: {e.user_message}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            except ValueError as e:
                print(f"ValueError during cancellation for booking {booking.id}: {e}")
                return Response({"detail": f"Cancellation error: {e}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            except Exception as e:
                import traceback
                traceback.print_exc()
                return Response({"detail": "An unexpected error occurred during cancellation."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
