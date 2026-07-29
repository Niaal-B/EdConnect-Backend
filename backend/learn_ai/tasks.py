"""Reserved for asynchronous LearnAI jobs when generation moves to Celery."""

# The synchronous MVP uses LearnAIService directly. A future Celery task should
# call that orchestration service rather than duplicate provider logic here.
