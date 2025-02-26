# logistics/views.py
from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, this is the logistics app!")


from django.shortcuts import render

# Create your views here.
