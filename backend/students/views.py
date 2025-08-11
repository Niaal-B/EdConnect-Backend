from auth.authentication import CookieJWTAuthentication
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView, RetrieveUpdateAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from students.models import StudentDetails
from students.serializers import (StudentDetailsSerializer,
                                  StudentLoginSerializer)
from users.serializers import UserSerializer
from users.utils import set_jwt_cookies


class StudentLoginView(GenericAPIView):
    serializer_class = StudentLoginSerializer

    def post(self,request):
        serialzer = StudentLoginSerializer(data=request.data)
        serialzer.is_valid(raise_exception=True)
        user = serialzer._validated_data

        response = Response({"message" : "login successfull",
        "user": {
              "id": user.id,
                "username":user.username,
                "email": user.email,
                "role": "student",
        }
        },status=status.HTTP_200_OK)
        return set_jwt_cookies(response,user)


class StudentProfileView(RetrieveUpdateAPIView):
    queryset = StudentDetails.objects.select_related('user')  
    serializer_class = StudentDetailsSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  

    def get_object(self):
        try:
            return StudentDetails.objects.select_related('user').get(user=self.request.user)
        except StudentDetails.DoesNotExist:
            raise PermissionDenied("Student profile not found")

    def update(self, request, *args, **kwargs):
        if 'user' in request.data:
            raise PermissionDenied("Cannot modify user relationship")
        
        return super().update(request, *args, **kwargs)