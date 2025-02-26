from django.db import models
from django.utils import timezone


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

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.status == 'sailing':
            self.cars.update(storage_status='sailing')
        else:
            self.cars.exclude(storage_status='delivered').update(storage_status=self.status)


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

    vin = models.CharField(max_length=17, unique=True)
    make = models.CharField(max_length=50)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="cars", null=True)
    container = models.ForeignKey(Container, on_delete=models.SET_NULL, null=True, blank=True, related_name="cars")
    storage_status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    date_stored = models.DateField(null=True, blank=True)
    procedure = models.CharField(max_length=10, choices=PROCEDURE_CHOICES, default='transit')

    def __str__(self):
        return f"{self.make} ({self.vin})"

    def days_on_warehouse_display(self):
        if self.storage_status == 'in_warehouse' and self.date_stored:
            return (timezone.now().date() - self.date_stored).days
        return 0

    def save(self, *args, **kwargs):
        if self.storage_status == 'in_warehouse' and not self.date_stored:
            self.date_stored = timezone.now().date()
        super().save(*args, **kwargs)


class Payment(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, null=True, blank=True)
    container = models.ForeignKey(Container, on_delete=models.CASCADE, null=True, blank=True)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачен'),
        ('overdue', 'Просрочен'),
    ])

    def save(self, *args, **kwargs):
        self.is_partial = self.amount_paid < self.amount_due
        super().save(*args, **kwargs)

    def get_balance(self):
        return self.amount_due - self.amount_paid

    def __str__(self):
        return f"Payment: {self.amount_paid}/{self.amount_due} USD ({self.status})"


class Invoice(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="invoices")
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
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
