from rest_framework.views import APIView
from .serializers import MentorLoginSerializer
from rest_framework.response import Response
from rest_framework import status
from users.utils import set_jwt_cookies
from rest_framework.generics import GenericAPIView
class MentorLoginView(GenericAPIView):
    serializer_class = MentorLoginSerializer
    def post(self,request):
        serializer = MentorLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

        response = Response({"role" : "mentor"},status=status.HTTP_200_OK)
        return set_jwt_cookies(response,user)
