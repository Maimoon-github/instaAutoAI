from django.urls import path
from django.http import JsonResponse

def pipeline_health(request):
    return JsonResponse({"status": "ok", "service": "pipeline"})

urlpatterns = [
    path("pipeline/health/", pipeline_health, name="pipeline-health"),
]