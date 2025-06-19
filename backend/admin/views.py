from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView,generics
from admin.serializers import AdminLoginSerializer
from rest_framework import status
from users.utils import set_jwt_cookies
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from users.serializers import UserSerializer
from users.models import User
from auth.authentication import CookieJWTAuthentication
from admin.serializers import MentorApprovalSerializer,MentorVerificationSerializer
from mentors.models import MentorDetails
from django.shortcuts import get_object_or_404

# Create your views here.

class AdminLoginView(generics.GenericAPIView):
    serializer_class = AdminLoginSerializer

    def post(self,request):
        print("Hey i reached here")
        serializer = AdminLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

        response = Response({"message" : "login successfull",
        "user": {
              "id": user.id,
                "username":user.username,
                "email": user.email,
        }
        },status=status.HTTP_200_OK)

        return set_jwt_cookies(response,user)


class UserListView(generics.GenericAPIView):
  authentication_classes = [CookieJWTAuthentication] 
  permission_classes = [IsAdminUser]

  def get(self,request,*args,**kwargs):
    users = User.objects.exclude(is_superuser=True)
    serialized_data = UserSerializer(users,many=True)

    return Response({"users":serialized_data.data},status=status.HTTP_200_OK)


class UserStatusUpdateView(generics.GenericAPIView):
    authentication_classes = [CookieJWTAuthentication] 
    permission_classes = [IsAdminUser]

    def patch(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            
            user.is_active = not user.is_active
            user.save()
            
            return Response({
                "message": "User status updated",
                "user": UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class MentorVerificationDetailView(generics.RetrieveAPIView):
    """
    Endpoint to get mentor verification details by USER ID.
    Note: Uses the user's ID (not MentorDetails ID) in the URL.
    Example: /api/mentors/123/ (where 123 is the user ID)
    """

    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAdminUser]
    serializer_class = MentorVerificationSerializer
    
    
    def get_queryset(self):
        return MentorDetails.objects.select_related('user').prefetch_related('user__documents')
    
    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, user__id=self.kwargs['id'])
        return obj


class PendingMentorVerificationsView(generics.ListAPIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAdminUser]
    serializer_class = MentorVerificationSerializer
    
    def get_queryset(self):
        return MentorDetails.objects.filter(
            is_verified=False
        ).select_related('user').prefetch_related('user__documents')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        }, status=status.HTTP_200_OK)


class ApproveRejectMentorView(generics.GenericAPIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAdminUser]
    serializer_class = MentorApprovalSerializer
    
    def patch(self, request, mentor_id):
        mentor = get_object_or_404(MentorDetails, id=mentor_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action = serializer.validated_data['action']
        reason = serializer.validated_data.get('reason', '')
        
        if action == 'approve':
            mentor.is_verified = True
            mentor.verification_status = 'approved'
            mentor.rejection_reason = ''
            mentor.save()
            
          #need to implement the notification
            
            return Response(
                {
                    'status': 'approved',
                    'verification_status': 'approved',
                    'message': 'Mentor successfully approved'
                },
                status=status.HTTP_200_OK
            )
        else:
            mentor.is_verified = False
            mentor.verification_status = 'rejected'
            mentor.rejection_reason = reason
            mentor.save()
            
           #need to implement the notification

            return Response(
                {
                    'status': 'rejected',
                    'verification_status': 'rejected',
                    'rejection_reason': reason,
                    'message': 'Mentor application rejected'
                },
                status=status.HTTP_200_OK
            )

class UpdateVerificationStatusView(generics.GenericAPIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAdminUser]
    
    def patch(self, request, mentor_id):
        mentor = get_object_or_404(MentorDetails, id=mentor_id)
        new_status = request.data.get('status')
        
        if new_status not in dict(MentorDetails.VERIFICATION_STATUS).keys():
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        mentor.verification_status = new_status
        mentor.save()
        
        return Response(
            {
                'status': 'success',
                'verification_status': mentor.verification_status,
                'last_status_update': mentor.last_status_update
            },
            status=status.HTTP_200_OK
        )