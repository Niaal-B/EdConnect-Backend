from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # disable CSRF for simplicity, better to configure CSRF token in production
def hello_api(request):
    return JsonResponse({"message": "Hello from Django API!"})
