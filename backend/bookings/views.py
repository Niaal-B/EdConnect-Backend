import logging

import stripe
from auth.authentication import CookieJWTAuthentication
from bookings.models import Booking
from bookings.serializers import BookingSerializer, MentorBookingsSerializer
from django.conf import settings
from django.db import transaction
from django.db.models import Q,Case,When,Value,IntegerField
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from mentors.models import MentorDetails, Slot
from notifications.tasks import send_realtime_notification_task
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import User
from .zegoserverassistant import generate_token04
from notifications.tasks import send_realtime_notification_task

logger = logging.getLogger(__name__)


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
                stripe_account_id = MentorDetails.objects.get(user=mentor).stripe_account_id
                print(stripe_account_id)
                if not stripe_account_id:
                    return Response({"detail": "Mentor's Stripe account is not connected. They cannot receive payments."},
                                    status=status.HTTP_400_BAD_REQUEST)

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

                total_amount_cents = int(slot.fee * 100)
                platform_fee_cents = int(total_amount_cents * settings.PLATFORM_FEE_PERCENTAGE)

                if platform_fee_cents >= total_amount_cents:
                    return Response({"detail": "Calculated platform fee is greater than or equal to total amount."},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)



                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'], 
                    line_items=[
                        {
                            'price_data': {
                                'currency': 'usd', 
                                'unit_amount': total_amount_cents, 
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

                    payment_intent_data={
                        'application_fee_amount': platform_fee_cents,
                        'transfer_data': {
                            'destination': stripe_account_id, 
                        },
                    },

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
                logger.error(e)
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
        return (
            Booking.objects.filter(student=user)
            .exclude(status="PENDING_PAYMENT")
            .select_related("slot__mentor")
            .order_by(
                Case(
                    When(status="CONFIRMED", booked_start_time__gte=timezone.now(), then=Value(1)),
                    When(status="CONFIRMED", booked_start_time__lt=timezone.now(), then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField(),
                ),
                Case(
                    When(booked_start_time__gte=timezone.now(), then="booked_start_time"),
                    default=Value(None),
                ),
                "-booked_start_time",
            )
        )


    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset) 
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
        

class MentorBookingsAPIView(generics.ListAPIView):
    serializer_class = MentorBookingsSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Booking.objects.filter(
            mentor=user
        ).exclude(
            status__in=['PENDING', 'PENDING_PAYMENT']
        ).select_related('student').order_by(
            Case(
                When(status='CONFIRMED', booked_start_time__gte=timezone.now(), then=Value(1)),
                When(status='CONFIRMED', booked_start_time__lt=timezone.now(), then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            ),
            Case(
                When(booked_start_time__gte=timezone.now(), then='booked_start_time'),
                default=Value(None),
            ),
            '-booked_start_time'
        )

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
                            pass
                        else:
                             # Handle other unexpected slot statuses if needed
                            logger.error(f"Webhook: Slot {slot_id} has unexpected status {slot.status}. Booking {booking_id} confirmed.")


                    logger.debug(f"Booking {booking_id} and Slot {slot_id} updated to CONFIRMED/booked via webhook.")
                except Booking.DoesNotExist:
                    logger.error(f"Webhook: Booking with ID {booking_id} not found.")
                    return HttpResponse(status=404)
                except Slot.DoesNotExist:
                    logger.error(f"Webhook: Slot with ID {slot_id} not found for booking {booking_id}.")
                    return HttpResponse(status=404)
                except Exception as e:
                    logger.error(f"Webhook processing error for booking {booking_id}: {e}")
                    return HttpResponse(status=500)
        else:
            logger.error("Webhook received without booking_id in metadata. Session ID:", session.id)

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
                    
                    slot.status = 'available' 
                    slot.save()

                elif cancelling_user == booking.mentor:
                    refund_amount_cents = int(booking.booked_fee * 100)
                    booking_new_status = 'CANCELED_BY_MENTOR'
                    slot.status = 'unavailable' 
                    slot.save()

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
                logger.error(f"ValueError during cancellation for booking {booking.id}: {e}")
                return Response({"detail": f"Cancellation error: {e}"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            except Exception as e:
                import traceback
                traceback.print_exc()
                return Response({"detail": "An unexpected error occurred during cancellation."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class GenerateZegoTokenView(APIView):
    def post(self, request, format=None):
        try:
            booking_id = request.data.get('booking_id')
            user_id = request.data.get('user_id')
            
            if not booking_id or not user_id:
                return Response({'error': 'booking_id and user_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                booking = Booking.objects.get(id=booking_id)
            except Booking.DoesNotExist:
                return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

            if str(booking.student.id) != str(user_id) and str(booking.mentor.id) != str(user_id):
                return Response({'error': 'You do not have permission to join this session.'}, status=status.HTTP_403_FORBIDDEN)
            
            app_id = settings.ZEGO_APP_ID
            server_secret = settings.ZEGO_SERVER_SECRET
            effective_time_in_seconds = 3600
            print(type(app_id))
 
            token_info = generate_token04(
                int(app_id), 
                user_id, 
                server_secret, 
                effective_time_in_seconds, 
                payload=''
            )

            if token_info.error_code == 0:
                return Response({'token': token_info.token}, status=status.HTTP_200_OK)
            else:
                return Response({'error': token_info.error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
