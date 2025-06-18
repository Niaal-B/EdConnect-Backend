from rest_framework.views import APIView
from .serializers import (MentorLoginSerializer,MentorProfileSerializer,ProfilePictureSerializer,
VerificationDocumentSerializer,MentorProfileUpdateSerializer,PublicMentorSerializer)
from rest_framework.response import Response
from rest_framework import status,permissions
from users.utils import set_jwt_cookies
from rest_framework.generics import GenericAPIView,RetrieveUpdateAPIView,ListAPIView
from mentors.models import MentorDetails
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
            name='page',
            type=int,
            location=OpenApiParameter.QUERY,
            description='Page number'
        ),
    ]
)
class PublicMentorListView(ListAPIView):
    """
    Simple public API to list verified mentors with:
    - Pagination (10 per page)
    - Basic expertise filtering
    - Error handling
    
    Example requests:
    GET /api/mentors/                          # All mentors (page 1)
    GET /api/mentors/?page=2                   # Page 2
    GET /api/mentors/?expertise=python         # Filter by expertise
    GET /api/mentors/?experience_min=5         # 5+ years experience
    """
    
    serializer_class = PublicMentorSerializer
    
    def get_queryset(self):
        try:
            queryset = MentorDetails.objects.filter(is_verified=True)
            
            # 1. Filter by expertise (case-insensitive partial match)
            expertise = self.request.query_params.get('expertise')
            if expertise:
                queryset = queryset.filter(expertise__icontains=expertise)
            
            # 2. Filter by minimum experience
            exp_min = self.request.query_params.get('experience_min')
            if exp_min:
                queryset = queryset.filter(experience_years__gte=int(exp_min))
            
            # 3. Filter by maximum experience
            exp_max = self.request.query_params.get('experience_max')
            if exp_max:
                queryset = queryset.filter(experience_years__lte=int(exp_max))
            
            return queryset.order_by('-experience_years')  # Sort by most experienced first
            
        except ValueError:
            # Handles invalid number inputs (e.g. experience_min=abc)
            return MentorDetails.objects.none()
    
    def list(self, request, *args, **kwargs):
        try:
            # Get the base response from DRF's ListAPIView
            response = super().list(request, *args, **kwargs)
            
            # Add custom response format if needed
            response.data = {
                'success': True,
                'mentors': response.data['results'],  # Paginated results
                'total': response.data['count'],       # Total mentors count
                'page': int(request.query_params.get('page', 1))
            }
            return response
            
        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


