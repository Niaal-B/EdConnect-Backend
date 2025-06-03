from rest_framework.views import APIView
from .serializers import MentorLoginSerializer,MentorProfileSerializer,ProfilePictureSerializer,VerificationDocumentSerializer,MentorProfileUpdateSerializer
from rest_framework.response import Response
from rest_framework import status,permissions
from users.utils import set_jwt_cookies
from rest_framework.generics import GenericAPIView,RetrieveUpdateAPIView
from mentors.models import MentorDetails
from auth.authentication import CookieJWTAuthentication
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser,FormParser,JSONParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiTypes, OpenApiParameter, OpenApiExample



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


