"""HTTP views for LearnAI."""

import logging

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth.authentication import CookieJWTAuthentication

from .models import LearnAISummary
from .serializers import GenerateNotesSerializer, LearnAISummarySerializer
from .services import (
    AIQuotaExceededError,
    AIResponseError,
    AIServiceUnavailableError,
    LearnAIError,
    LearnAIService,
    TranscriptNotAvailableError,
)

logger = logging.getLogger(__name__)


class IsStudent(BasePermission):
    """Allow LearnAI access to authenticated student accounts only."""

    message = "LearnAI is available for student accounts only."

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and getattr(request.user, "role", None) == "student")


class LearnAIAuthenticatedAPIView(APIView):
    """Base class for authenticated LearnAI API endpoints."""

    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated, IsStudent]


class GenerateNotesAPIView(LearnAIAuthenticatedAPIView):
    """Create study notes from a YouTube lecture transcript."""

    @extend_schema(request=GenerateNotesSerializer, responses={201: LearnAISummarySerializer})
    def post(self, request):
        serializer = GenerateNotesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            note = LearnAIService().generate_notes(
                student=request.user,
                youtube_url=serializer.validated_data["youtube_url"],
            )
        except TranscriptNotAvailableError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except AIQuotaExceededError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except (AIServiceUnavailableError, AIResponseError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except LearnAIError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception("Unexpected LearnAI generation failure")
            return Response(
                {"detail": "Unable to generate notes right now. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(LearnAISummarySerializer(note).data, status=status.HTTP_201_CREATED)


class LearnAIHistoryAPIView(generics.ListAPIView):
    """List notes owned by the currently authenticated student."""

    serializer_class = LearnAISummarySerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated, IsStudent]
    pagination_class = None

    def get_queryset(self):
        return LearnAISummary.objects.filter(student=self.request.user)


class LearnAISummaryDetailAPIView(LearnAIAuthenticatedAPIView):
    """Retrieve or delete one note set owned by the current student."""

    def get_object(self, summary_id: int) -> LearnAISummary:
        try:
            return LearnAISummary.objects.get(id=summary_id, student=self.request.user)
        except LearnAISummary.DoesNotExist as exc:
            raise NotFound("Study notes not found.") from exc

    @extend_schema(responses={200: LearnAISummarySerializer})
    def get(self, request, summary_id: int):
        return Response(LearnAISummarySerializer(self.get_object(summary_id)).data)

    @extend_schema(responses={204: None})
    def delete(self, request, summary_id: int):
        self.get_object(summary_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
