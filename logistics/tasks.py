from datetime import datetime# logistics/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from .models import Client, Payment

@shared_task
def send_payment_reminder():
    # Получаем всех клиентов, у которых есть неоплаченные счета
    clients_with_due_payments = Client.objects.filter(
        payments__status='unpaid',
        payments__due_date__lte=datetime.now()
    ).distinct()

    for client in clients_with_due_payments:
        unpaid_payments = Payment.objects.filter(client=client, status='unpaid')

        # Отправляем напоминание клиенту
        send_mail(
            'Напоминание о неоплаченных счетах',
            f'У вас есть неоплаченные счета на сумму: {sum([payment.amount for payment in unpaid_payments])}. Пожалуйста, оплатите их как можно скорее.',
            'no-reply@yourapp.com',
            [client.email],
            fail_silently=False,
        )