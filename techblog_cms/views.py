from django.shortcuts import render
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok"})

def index(request):
    return render(request, 'index.html')

# Create your views here.
