from rest_framework.views import APIView
from .serializers import (MentorLoginSerializer,MentorProfileSerializer,ProfilePictureSerializer,
VerificationDocumentSerializer,MentorProfileUpdateSerializer,PublicMentorSerializer,
SlotSerializer)
from rest_framework.response import Response
from rest_framework import status,permissions
from users.utils import set_jwt_cookies
from rest_framework.generics import GenericAPIView,RetrieveUpdateAPIView,ListAPIView,ListCreateAPIView,UpdateAPIView
from mentors.models import MentorDetails,Slot
from auth.authentication import CookieJWTAuthentication
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser,FormParser,JSONParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiTypes, OpenApiParameter, OpenApiExample
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from django.db import models
from django.db.models import Q



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
    """
    Enhanced public API to list verified mentors with:
    - Pagination (10 per page)
    - Search functionality (name, bio, expertise)
    - Expertise filtering
    - Experience range filtering
    - Error handling
    
    Example requests:
    GET /api/mentors/                                    # All mentors (page 1)
    GET /api/mentors/?page=2                             # Page 2
    GET /api/mentors/?expertise=python                   # Filter by expertise
    GET /api/mentors/?experience_min=5                   # 5+ years experience
    GET /api/mentors/?search=machine learning            # Search functionality
    GET /api/mentors/?search=john&expertise=python       # Combined search and filter
    """
    
    serializer_class = PublicMentorSerializer
    
    def get_queryset(self):
        try:
            queryset = MentorDetails.objects.filter(is_verified=True).select_related('user')
            
            # 1. Search functionality - searches across username, bio, and expertise
            search_query = self.request.query_params.get('search', '').strip()
            if search_query:
                search_terms = search_query.split()
                search_q = Q()
                
                for term in search_terms:
                    # Search in username (from related User model)
                    search_q |= Q(user__username__icontains=term)
                    # Search in bio
                    search_q |= Q(bio__icontains=term)
                    # Search in expertise (assuming it's a text field or JSON field)
                    search_q |= Q(expertise__icontains=term)
                
                queryset = queryset.filter(search_q)
            
            # 2. Filter by expertise (case-insensitive partial match)
            expertise = self.request.query_params.get('expertise', '').strip()
            if expertise:
                queryset = queryset.filter(expertise__icontains=expertise)
            
            # 3. Filter by minimum experience
            exp_min = self.request.query_params.get('experience_min')
            if exp_min:
                try:
                    exp_min_int = int(exp_min)
                    queryset = queryset.filter(experience_years__gte=exp_min_int)
                except ValueError:
                    pass  # Ignore invalid values
            
            # 4. Filter by maximum experience
            exp_max = self.request.query_params.get('experience_max')
            if exp_max:
                try:
                    exp_max_int = int(exp_max)
                    queryset = queryset.filter(experience_years__lte=exp_max_int)
                except ValueError:
                    pass  # Ignore invalid values
            
            # Order by experience (most experienced first) and then by username
            return queryset.order_by('-experience_years', 'user__username').distinct()
            
        except Exception as e:
            # Log the error in production
            print(f"Error in queryset: {str(e)}")
            return MentorDetails.objects.none()
    
    def list(self, request, *args, **kwargs):
        try:
            # Get the base response from DRF's ListAPIView
            response = super().list(request, *args, **kwargs)
            
            # Get current page number
            page_number = int(request.query_params.get('page', 1))
            
            # Custom response format to match frontend expectations
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
            
            # Add search/filter info if present
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

    def get_queryset(self):
        return Slot.objects.filter(mentor=self.request.user).order_by('-start_time')

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