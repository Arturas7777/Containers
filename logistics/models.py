from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

class Client(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()

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
        ('sailing', 'Плывет'),
    ]

    number = models.CharField(max_length=50, unique=True)
    arrival_date = models.DateField()
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    ths = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="THS")

    def __str__(self):
        return self.number

    def clean(self):
        if self.status == 'arrived' and (self.ths is None or self.ths <= 0):
            raise ValidationError("Поле THS обязательно для заполнения и должно быть больше 0 при статусе 'Прибыл'.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        if self.status == 'sailing':
            self.cars.update(storage_status='sailing')
        elif self.status != 'sailing':
            self.cars.exclude(storage_status='delivered').update(storage_status=self.status)
        if self.status == 'arrived' and self.ths is not None:
            cars = self.cars.all()
            if cars.exists():
                ths_per_car = self.ths / cars.count()
                for car in cars:
                    car.ths = ths_per_car
                    car.save()

class Car(models.Model):
    STATUS_CHOICES = [
        ('in_port', 'В порту'),
        ('in_warehouse', 'На складе'),
        ('delivered', 'Передан клиенту'),
        ('sailing', 'Плывет'),
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
    date_stored = models.DateField(null=True, blank=True)
    procedure = models.CharField(max_length=10, choices=PROCEDURE_CHOICES, default='transit')
    ths = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="THS")
    sklad = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="SKLAD")
    days_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="DAYS")
    prof = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="PROF")
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False, verbose_name="TOTAL")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Склад")

    def __str__(self):
        client_name = self.client.name if self.client else "Без клиента"
        return f"{self.make} {client_name} ({self.vin})"

    def days_on_warehouse_display(self):
        if self.storage_status == 'in_warehouse' and self.date_stored:
            return (timezone.now().date() - self.date_stored).days
        return 0
    days_on_warehouse_display.short_description = "Дней на складе"

    def save(self, *args, **kwargs):
        if self.storage_status == 'in_warehouse' and not self.date_stored:
            self.date_stored = timezone.now().date()
        if self.container and not self.warehouse:
            self.warehouse = self.container.warehouse
        self.total = self.ths + self.sklad + self.days_cost + self.prof
        super().save(*args, **kwargs)

class Payment(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('cash', 'Наличные'),
        ('transfer', 'Перевод'),
        ('mutual_settlement', 'Взаимозачёт'),
    ]

    car = models.ForeignKey('Car', on_delete=models.CASCADE, null=True, blank=True)
    container = models.ForeignKey('Container', on_delete=models.CASCADE, null=True, blank=True)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Ожидает оплаты'), ('paid', 'Оплачен'), ('overdue', 'Просрочен')])
    is_partial = models.BooleanField(default=False)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='cash')  # Новое поле

    def save(self, *args, **kwargs):
        if self.amount_paid < self.amount_due:
            self.is_partial = True
        else:
            self.is_partial = False
        super().save(*args, **kwargs)

    def get_balance(self):
        return self.amount_due - self.amount_paid

    def __str__(self):
        return f"Payment for {self.car if self.car else 'Container'} - {self.amount_paid} / {self.amount_due} USD ({self.status}) - {self.get_payment_type_display()}"

class Invoice(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="invoices")
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=[('unpaid', 'Не оплачен'), ('paid', 'Оплачен'), ('overdue', 'Просрочен')], default='unpaid')
    cars = models.ManyToManyField(Car, related_name="invoices", blank=True)

    def update_amount(self):
        self.amount = sum(car.total for car in self.cars.all())
        self.save(update_fields=['amount'])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def mark_as_paid(self):
        self.status = 'paid'
        self.save()

    def check_overdue(self):
        if self.status == 'unpaid' and self.due_date < timezone.now().date():
            self.status = 'overdue'
            self.save()

    def __str__(self):
        return f"Invoice #{self.id} - {self.client.name} - {self.amount} USD ({self.status})"