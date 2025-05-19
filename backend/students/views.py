# from rest_framework import generics, status
# from rest_framework.response import Response
# from students.serializers import StudentRegistrationSerializer

# class StudentRegistrationView(generics.CreateAPIView):
#     serializer_class = StudentRegistrationSerializer
    
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
        
#         # Store in Redis instead of DB
#         user_data = serializer.validated_data
#         verification_token = store_unverified_user(user_data)
        
#         # Send verification email via Celery
#         send_verification_email.delay(
#             verification_token=verification_token,
#             user_data={
#                 'username': user_data['username'],
#                 'email': user_data['email'],
#                 'first_name': user_data.get('first_name', ''),
#                 'last_name': user_data.get('last_name', '')
#             }
#         )
        
#         return Response({
#             'status': 'pending_verification',
#             'message': 'Verification email sent',
#             'email': user_data['email']
#         }, status=status.HTTP_202_ACCEPTED)

