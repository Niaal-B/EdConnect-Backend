import datetime

import pytz
import stripe
from auth.authentication import CookieJWTAuthentication
from bookings.models import Booking
from django.conf import settings
from django.db import models
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   OpenApiTypes, extend_schema)
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from mentors.models import MentorDetails, Slot
from rest_framework import permissions, status
from rest_framework.generics import (GenericAPIView, ListAPIView,
                                     ListCreateAPIView, RetrieveUpdateAPIView,
                                     UpdateAPIView)
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.utils import set_jwt_cookies

from .serializers import (MentorLoginSerializer, MentorProfileSerializer,
                          MentorProfileUpdateSerializer,
                          ProfilePictureSerializer, PublicMentorSerializer,
                          SlotSerializer, VerificationDocumentSerializer,UpcomingBookingSerializer)

from connections.models import Connection
from bookings.models import Booking,Feedback
from bookings.serializers import FeedbackSerializer

class MentorLoginView(GenericAPIView):
    serializer_class = MentorLoginSerializer
    def post(self,request):
        serializer = MentorLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

        response = Response({"message" : "login succesfull",
        "user": {
              "id": user.id,
                "username":user.username,
                "email": user.email,
                "role": "mentor",
                
        }
        },status=status.HTTP_200_OK)

        return set_jwt_cookies(response,user)
      
class MentorProfileView(RetrieveUpdateAPIView):
    """
    Retrieve or update mentor profile (excluding profile picture)
    """
    queryset = MentorDetails.objects.all()
    serializer_class = MentorProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]
    authentication_classes = [CookieJWTAuthentication]  


    def get_object(self):
        return get_object_or_404(MentorDetails, user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return MentorProfileUpdateSerializer
        return MentorProfileSerializer


class ProfilePictureView(APIView):
    """
    Handle profile picture uploads
    """
    authentication_classes = [CookieJWTAuthentication]  
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]


    
    @extend_schema(
        request=ProfilePictureSerializer,
        responses={200: ProfilePictureSerializer},
        methods=["PATCH"],
        description="Upload or update mentor profile picture",
        tags=["Mentor Profile"],
    )


    def patch(self, request):
        mentor = get_object_or_404(MentorDetails, user=request.user)
        serializer = ProfilePictureSerializer(mentor, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

class DocumentUploadView(APIView):
    """
    Handle verification document uploads
    """
    authentication_classes = [CookieJWTAuthentication]  
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]


    @extend_schema(
        request=VerificationDocumentSerializer,
        responses={200: VerificationDocumentSerializer},
        methods=["POST"],
        description="Upload documents",
        tags=["Mentor Profile"],
    )

      

    def post(self, request):
        mentor = get_object_or_404(MentorDetails, user=request.user) 
        serializer = VerificationDocumentSerializer(data=request.data)  
        serializer.is_valid(raise_exception=True)
        serializer.save(mentor=request.user) 
        

        return Response({
            'status': 'success',
            'document': serializer.data
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='expertise',
            type=str,
            location=OpenApiParameter.QUERY,
            description='Filter by expertise (case-insensitive)'
        ),
        OpenApiParameter(
            name='experience_min',
            type=int,
            location=OpenApiParameter.QUERY,
            description='Minimum years of experience'
        ),
        OpenApiParameter(
            name='experience_max',
            type=int,
            location=OpenApiParameter.QUERY,
            description='Maximum years of experience'
        ),
        OpenApiParameter(
            name='search',
            type=str,
            location=OpenApiParameter.QUERY,
            description='Search by name, bio, or expertise'
        ),
        OpenApiParameter(
            name='page',
            type=int,
            location=OpenApiParameter.QUERY,
            description='Page number'
        ),
    ]
)

class PublicMentorListView(ListAPIView):
    
    serializer_class = PublicMentorSerializer
    
    def get_queryset(self):
        try:
            queryset = MentorDetails.objects.filter(is_verified=True).select_related('user')
            
            search_query = self.request.query_params.get('search', '').strip()
            if search_query:
                search_terms = search_query.split()
                search_q = Q()
                
                for term in search_terms:
                    search_q |= Q(user__username__icontains=term)
                    search_q |= Q(bio__icontains=term)
                    search_q |= Q(expertise__icontains=term)
                
                queryset = queryset.filter(search_q)
            
            expertise = self.request.query_params.get('expertise', '').strip()
            if expertise:
                queryset = queryset.filter(expertise__icontains=expertise)
            
            exp_min = self.request.query_params.get('experience_min')
            if exp_min:
                try:
                    exp_min_int = int(exp_min)
                    queryset = queryset.filter(experience_years__gte=exp_min_int)
                except ValueError:
                    pass  
            
            exp_max = self.request.query_params.get('experience_max')
            if exp_max:
                try:
                    exp_max_int = int(exp_max)
                    queryset = queryset.filter(experience_years__lte=exp_max_int)
                except ValueError:
                    pass  
            
            return queryset.order_by('-experience_years', 'user__username').distinct()
            
        except Exception as e:
            return MentorDetails.objects.none()
    
    def list(self, request, *args, **kwargs):
        try:
            response = super().list(request, *args, **kwargs)
            
            page_number = int(request.query_params.get('page', 1))
            
            custom_response = {
                'success': True,
                'mentors': response.data['results'],
                'total': response.data['count'],
                'page': page_number,
                'has_next': response.data['next'] is not None,
                'has_previous': response.data['previous'] is not None,
                'next_page': page_number + 1 if response.data['next'] else None,
                'previous_page': page_number - 1 if response.data['previous'] else None,
            }
            
            search_query = request.query_params.get('search', '').strip()
            expertise = request.query_params.get('expertise', '').strip()
            exp_min = request.query_params.get('experience_min')
            exp_max = request.query_params.get('experience_max')
            
            filters_applied = []
            if search_query:
                filters_applied.append(f"search: '{search_query}'")
            if expertise:
                filters_applied.append(f"expertise: '{expertise}'")
            if exp_min:
                filters_applied.append(f"min_experience: {exp_min}")
            if exp_max:
                filters_applied.append(f"max_experience: {exp_max}")
            
            if filters_applied:
                custom_response['filters_applied'] = filters_applied
                custom_response['message'] = f"Found {response.data['count']} mentors matching your criteria"
            else:
                custom_response['message'] = f"Found {response.data['count']} verified mentors"
            
            return Response(custom_response, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {
                    'success': False, 
                    'error': 'Invalid page number provided',
                    'mentors': [],
                    'total': 0
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    'success': False, 
                    'error': str(e),
                    'mentors': [],
                    'total': 0
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MentorSlotListCreateView(ListCreateAPIView):
    serializer_class = SlotSerializer
    authentication_classes = [CookieJWTAuthentication]  
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Slot.objects.filter(mentor=self.request.user).order_by('start_time')

    def perform_create(self, serializer):
        serializer.save(mentor=self.request.user)


class MentorSlotCancelView(UpdateAPIView):
    serializer_class = SlotSerializer
    authentication_classes = [CookieJWTAuthentication]  
    permission_classes = [IsAuthenticated]
    queryset = Slot.objects.all()

    def patch(self, request, *args, **kwargs):
        slot = self.get_object()

        if slot.mentor != request.user:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        if slot.status == "booked":
            return Response({"error": "Cannot cancel a booked slot"}, status=status.HTTP_400_BAD_REQUEST)

        slot.status = "cancelled"
        slot.save()
        return Response({"success": "Slot cancelled successfully"}, status=status.HTTP_200_OK)


class MentorStripeOnboardingView(APIView):
    authentication_classes = [CookieJWTAuthentication]  
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        try:
            mentor_profile = MentorDetails.objects.get(user=user)
        except MentorDetails.DoesNotExist:
            return Response(
                {"detail": "Mentor profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        account_id = mentor_profile.stripe_account_id

        try:
            if not account_id:
                account = stripe.Account.create(
                    type='express',
                    country='US', 
                    email=user.email,
                    capabilities={
                        'card_payments': {'requested': True},
                        'transfers': {'requested': True},
                    },
                    business_type='individual', 

                    metadata={
                        'edconnect_user_id': str(user.id),
                        'edconnect_mentor_profile_id': str(mentor_profile.id),
                    }
                )
                account_id = account.id
                mentor_profile.stripe_account_id = account_id
                mentor_profile.save()
            else:
                account = stripe.Account.retrieve(account_id)

            account_link = stripe.AccountLink.create(
                account=account_id,
                refresh_url=f"{settings.PLATFORM_BASE_URL}/mentor/earnings?refresh=true",
                return_url=f"{settings.PLATFORM_BASE_URL}/mentor/earnings?onboarding_success=true", 
                type='account_onboarding',
            )
            return Response({"url": account_link.url})

        except stripe.error.StripeError as e:
            return Response(
                {"detail": f"Stripe error: {e.user_message}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {"detail": "An unexpected error occurred during Stripe onboarding initiation."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request):
        user = request.user
        try:
            mentor_profile = MentorDetails.objects.get(user=user)
        except MentorDetails.DoesNotExist:
            return Response(
                {"detail": "Mentor profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        account_id = mentor_profile.stripe_account_id
        if not account_id:
            return Response(
                {"status": "not_onboarded", "detail": "Stripe account not linked."},
                status=status.HTTP_200_OK
            )

        try:
            account = stripe.Account.retrieve(account_id)
            return Response({
                "status": "onboarded",
                "details_submitted": account.details_submitted,
                "payouts_enabled": account.payouts_enabled,
                "charges_enabled": account.charges_enabled, 
                "requirements_due": account.requirements.past_due or account.requirements.eventually_due or account.requirements.currently_due,
                "detail": "Stripe account linked."
            })
        except stripe.error.StripeError as e:
            return Response(
                {"detail": f"Stripe error: {e.user_message}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {"detail": "An unexpected error occurred retrieving Stripe account status."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MentorEarningsAPIView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


    def get(self,request,*args,**kwargs):
        mentor = request.user 
        Mentordetails = MentorDetails.objects.get(user=mentor)

        if not hasattr(Mentordetails, 'stripe_account_id') or not Mentordetails.stripe_account_id:
             return Response(
                {"detail": "Stripe account not connected for this mentor."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            stripe_account_status = stripe.Account.retrieve(
                Mentordetails.stripe_account_id
            )
            payouts_enabled = stripe_account_status.payouts_enabled
            charges_enabled = stripe_account_status.charges_enabled
            requirements_due = stripe_account_status.requirements.eventually_due    

        except stripe.error.StripeError as e:
            return Response(
                {"detail": f"Error fetching Stripe account status: {e.user_message}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        total_balance_available = 0
        total_balance_pending = 0
  
        try:
            balance = stripe.Balance.retrieve(stripe_account=Mentordetails.stripe_account_id)
            for b in balance['available']:
                total_balance_available += b['amount']
            for b in balance['pending']:
                total_balance_pending += b['amount']

        except stripe.error.StripeError as e:
            pass 

        total_earnings_cents = 0
        monthly_earnings_cents = 0
        
        now = timezone.now()
        start_of_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


        try:
            transfers = stripe.Transfer.list(
                destination=Mentordetails.stripe_account_id,
                limit=100,
            )

            for transfer in transfers.auto_paging_iter(): 

                transfer_created_dt = datetime.datetime.fromtimestamp(transfer.created, tz=pytz.utc)
                total_earnings_cents += transfer.amount

                if transfer_created_dt >= start_of_current_month:
                    monthly_earnings_cents += transfer.amount

        except stripe.error.StripeError as e:
            pass

        completed_sessions_count = Booking.objects.filter(
            mentor=mentor,
            status='CONFIRMED',
            payment_status='PAID',
            booked_end_time__lt=now
        ).count()

        average_session_fee = 0
        total_fee_from_completed_sessions = Booking.objects.filter(
            mentor=mentor,
            status='CONFIRMED',
            payment_status='PAID',
            booked_end_time__lt=now
        ).aggregate(Sum('booked_fee'))['booked_fee__sum']

        if completed_sessions_count > 0 and total_fee_from_completed_sessions is not None:
            average_session_fee = total_fee_from_completed_sessions / completed_sessions_count


        response_data = {
            'stripe_status': {
                'status': 'onboarded', 
                'details_submitted': True, 
                'payouts_enabled': payouts_enabled,
                'charges_enabled': charges_enabled,
                'requirements_due': requirements_due, 
                'detail': 'Stripe account status fetched.'
            },

            'totalEarnings': total_earnings_cents / 100.0,
            'monthlyEarnings': monthly_earnings_cents / 100.0,
            'pendingPayouts': total_balance_pending / 100.0,
            'availableForPayout': total_balance_available / 100.0, 

            'completedSessions': completed_sessions_count,
            'averageSessionFee': average_session_fee,

            'payoutSchedule': 'Weekly (every Friday)', 
            'platformFee': settings.PLATFORM_FEE_PERCENTAGE * 100, 
            'processingTime': '1-2 business days',
        }

        return Response(response_data, status=status.HTTP_200_OK)


        

class MentorDashboardStatsView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        mentor = self.request.user
        
        if mentor.role !='mentor':
            return


        pending_requests_count = Connection.objects.filter(
            status='pending',mentor=mentor
        ).count()


        confirmed_sessions_count = Booking.objects.filter(
            status='CONFIRMED',mentor=mentor
        ).count()

        data = {
            "pending_requests_count": pending_requests_count,
            "confirmed_sessions_count": confirmed_sessions_count,
        }
        
        return Response(data)



class UpcomingSessionsView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        mentor = request.user
        if mentor.role != "mentor":
            return Response({"detail": "Only students can access this."}, status=403)

        upcoming_sessions = Booking.objects.filter(
            mentor=mentor,
            status="CONFIRMED",
        )[:5]

        serializer = UpcomingBookingSerializer(upcoming_sessions, many=True)
        return Response(serializer.data)




class MentorFeedbackView(ListAPIView):
    """
    API view to list all feedback for the authenticated mentor.
    """
    authentication_classes = [CookieJWTAuthentication]
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Feedback.objects.filter(booking__mentor=self.request.user).order_by('-submitted_at')
