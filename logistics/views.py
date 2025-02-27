# logistics/views.py
from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, this is the logistics app!")


from django.shortcuts import render
from django.http import JsonResponse
from logistics.tasks import send_payment_reminder

def send_reminder_view(request):
    send_payment_reminder.delay()  # Запуск задачи Celery
    return JsonResponse({"status": "success", "message": "Reminder sent!"})
# Create your views here.
def home(request):
    return render(request, 'logistics/home.html')