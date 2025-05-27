from rest_framework.generics import GenericAPIView
from students.serializers import StudentLoginSerializer

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