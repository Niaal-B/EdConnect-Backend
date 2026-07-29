"""LearnAI API routes."""

from django.urls import path

from .views import GenerateNotesAPIView, LearnAIHistoryAPIView, LearnAISummaryDetailAPIView

urlpatterns = [
    path("generate/", GenerateNotesAPIView.as_view(), name="learn-ai-generate"),
    path("history/", LearnAIHistoryAPIView.as_view(), name="learn-ai-history"),
    path("<int:summary_id>/", LearnAISummaryDetailAPIView.as_view(), name="learn-ai-detail"),
]
