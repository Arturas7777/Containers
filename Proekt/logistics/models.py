from django.db import models

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
    title = models.CharField(max_length=20, choices=TITLE_CHOICES, default='ours')  # Заменили year на title
    container = models.ForeignKey(Container, on_delete=models.SET_NULL, null=True, blank=True, related_name="cars")
    storage_status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    # Новое поле procedure
    procedure = models.CharField(
        max_length=10,
        choices=PROCEDURE_CHOICES,
        default='transit',  # Можно установить по умолчанию
    )

    def __str__(self):
        # Проверяем, есть ли клиент, и выводим его имя, если есть
        client_name = self.client.name if self.client else "Без клиента"
        return f"{self.make} {client_name} ({self.vin})"  # В выводе отображаем имя клиента

class Payment(models.Model):
    car = models.ForeignKey('Car', on_delete=models.CASCADE, null=True, blank=True)  # Привязка к автомобилю
    container = models.ForeignKey('Container', on_delete=models.CASCADE, null=True, blank=True)  # Привязка к контейнеру
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Сумма платежа
    payment_date = models.DateField(auto_now_add=True)  # Дата платежа
    status = models.CharField(max_length=20, choices=[  # Статус платежа
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачен'),
        ('overdue', 'Просрочен'),
    ])

    def save(self, *args, **kwargs):
        # Если платеж связан с контейнером, делим сумму на количество машин в контейнере
        if self.container:
            cars_in_container = self.container.car_set.count()  # Получаем количество машин в контейнере
            self.amount = self.amount / cars_in_container  # Разделяем сумму на количество машин
        super().save(*args, **kwargs)  # Сохраняем объект

    def __str__(self):
        return f"Payment for {self.car if self.car else 'Container'} - {self.amount} USD ({self.status})"


from django.db import models

# Create your models here.
