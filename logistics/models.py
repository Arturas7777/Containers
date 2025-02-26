from django.db import models
from django.utils import timezone


class Client(models.Model):
    name = models.CharField(max_length=100)  # Имя клиента
    email = models.EmailField()  # Электронная почта клиента
    phone = models.CharField(max_length=15)  # Телефон клиента
    address = models.TextField()  # Адрес клиента

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    location = models.TextField()
    capacity = models.IntegerField()

    def __str__(self):
        return self.name


class Container(models.Model):
    STATUS_CHOICES = [
        ('arrived', 'Прибыл'),
        ('unloaded', 'Разгружен'),
        ('stored', 'На складе'),
        ('delivered', 'Передан клиенту'),
        ('sailing', 'Плывет'),  # Новый статус
    ]

    number = models.CharField(max_length=50, unique=True)
    arrival_date = models.DateField()
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Сохраняем контейнер
        if self.status == 'sailing':  # Если контейнер "Плывет", обновляем машины
            self.cars.update(storage_status='sailing')
        elif self.status != 'sailing':  # Если контейнер больше не "Плывет", снимаем статус с машин
            self.cars.exclude(storage_status='delivered').update(storage_status=self.status)


class Car(models.Model):
    STATUS_CHOICES = [
        ('in_port', 'В порту'),
        ('in_warehouse', 'На складе'),
        ('delivered', 'Передан клиенту'),
        ('sailing', 'Плывет'),  # Новый статус
    ]
    PROCEDURE_CHOICES = [
        ('transit', 'Транзит'),
        ('reexport', 'Реекспорт'),
        ('import', 'Импорт'),
        ('export', 'Экспорт'),
    ]
    TITLE_CHOICES = [
        ('ours', 'У нас'),
        ('warehouse', 'У склада'),
        ('delivered', 'Передан клиенту'),
        ('waiting_from_usa', 'Ждем из USA'),
    ]
    vin = models.CharField(max_length=17, unique=True)
    make = models.CharField(max_length=50)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="cars", null=True)
    title = models.CharField(max_length=20, choices=TITLE_CHOICES, default='ours')
    container = models.ForeignKey(Container, on_delete=models.SET_NULL, null=True, blank=True, related_name="cars")
    storage_status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    # Новое поле для даты выгрузки автомобиля на склад
    date_stored = models.DateField(null=True, blank=True)

    procedure = models.CharField(
        max_length=10,
        choices=PROCEDURE_CHOICES,
        default='transit',
    )

    def __str__(self):
        client_name = self.client.name if self.client else "Без клиента"
        return f"{self.make} {client_name} ({self.vin})"

    @property
    def days_on_warehouse(self):
        """Возвращает количество дней, которое автомобиль находится на складе."""
        if self.storage_status == 'in_warehouse' and self.date_stored:
            return (timezone.now().date() - self.date_stored).days
        return 0  # Если статус не 'На складе' или нет даты, то 0 дней

    def save(self, *args, **kwargs):
        """Автоматически устанавливаем дату выгрузки, когда статус 'На складе'."""
        if self.storage_status == 'in_warehouse' and not self.date_stored:
            self.date_stored = timezone.now().date()  # Устанавливаем текущую дату
        super().save(*args, **kwargs)


class Payment(models.Model):
    car = models.ForeignKey('Car', on_delete=models.CASCADE, null=True, blank=True)  # Привязка к автомобилю
    container = models.ForeignKey('Container', on_delete=models.CASCADE, null=True, blank=True)  # Привязка к контейнеру
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)  # Сумма долга
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Сумма уже оплачена
    payment_date = models.DateField(auto_now_add=True)  # Дата платежа
    status = models.CharField(max_length=20, choices=[  # Статус платежа
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачен'),
        ('overdue', 'Просрочен'),
    ])
    is_partial = models.BooleanField(default=False)  # Отметка о частичной оплате

    def save(self, *args, **kwargs):
        if self.amount_paid < self.amount_due:
            self.is_partial = True
        else:
            self.is_partial = False
        super().save(*args, **kwargs)  # Сохраняем объект

    def get_balance(self):
        """Вычисляем сумму долга"""
        return self.amount_due - self.amount_paid

    def __str__(self):
        return f"Payment for {self.car if self.car else 'Container'} - {self.amount_paid} / {self.amount_due} USD ({self.status})"


class Invoice(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="invoices")
    issue_date = models.DateField(default=timezone.now)  # Дата выставления счета
    due_date = models.DateField()  # Срок оплаты
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Сумма счета
    status = models.CharField(max_length=20, choices=[  # Статус счета
        ('unpaid', 'Не оплачен'),
        ('paid', 'Оплачен'),
        ('overdue', 'Просрочен'),
    ], default='unpaid')

    def mark_as_paid(self):
        self.status = 'paid'
        self.save()

    def check_overdue(self):
        if self.status == 'unpaid' and self.due_date < timezone.now().date():
            self.status = 'overdue'
            self.save()

    def __str__(self):
        return f"Invoice #{self.id} - {self.client.name} - {self.amount} USD ({self.status})"