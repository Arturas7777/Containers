# logistics/views.py
from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    return HttpResponse("Hello, this is the logistics app!")


from django.shortcuts import render
from django.http import JsonResponse
from logistics.tasks import send_payment_reminder

def send_reminder_view(request):
    send_payment_reminder.delay()  # Запуск задачи Celery
    return JsonResponse({"status": "success", "message": "Reminder sent!"})

def car_list(request):
    cars = Car.objects.all()  # Получаем все автомобили
    return render(request, 'logistics/cars_list.html', {'cars': cars})

def home(request):
    return render(request, 'logistics/home.html')
# Create your views here.
