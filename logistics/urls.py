# logistics/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('send-reminder/', views.send_reminder_view, name='send_reminder'),
]

urlpatterns = [
    path('cars/', views.car_list, name='cars_list'),
]