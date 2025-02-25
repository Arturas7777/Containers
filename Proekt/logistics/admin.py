from django.contrib import admin
from .models import Car, Payment, Warehouse, Container, Client


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('car', 'container', 'amount', 'payment_date', 'status')


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'capacity')


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('vin', 'make', 'client', 'storage_status', 'title', 'container', 'container_arrival_date')
    list_filter = ('storage_status', 'container')
    search_fields = ('vin', 'make', 'client__name')  # Поиск по VIN, марке и имени клиента

    def container_arrival_date(self, obj):
        return obj.container.arrival_date if obj.container else None

    container_arrival_date.short_description = 'Дата прибытия контейнера'

    def get_warehouse(self, obj):
        return obj.container.warehouse if obj.container else None

    get_warehouse.short_description = 'Склад'


class CarInline(admin.TabularInline):  # или admin.StackedInline для другого вида
    model = Car
    extra = 1  # Количество пустых форм для добавления машин


@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    list_display = ('number', 'arrival_date', 'status', 'warehouse')
    list_filter = ('status', 'warehouse')
    inlines = [CarInline]  # Вставляем возможность добавлять машины


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'address')


from django.contrib import admin

# Register your models here.
