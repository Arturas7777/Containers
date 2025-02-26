from django.contrib import admin
from .models import Car, Payment, Warehouse, Container, Client


from django.contrib import admin
from .models import Payment, Warehouse, Car, Container, Client, Invoice

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('car', 'container', 'amount_due', 'amount_paid', 'get_balance', 'payment_date', 'status', 'is_partial')
    list_filter = ('status', 'is_partial')
    search_fields = ('car__vin', 'container__number', 'status')

    def get_balance(self, obj):
        return obj.get_balance()
    get_balance.short_description = 'Оставшийся долг'

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'capacity')

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('vin', 'make', 'days_on_warehouse', 'client', 'storage_status', 'title', 'container', 'container_arrival_date')
    list_filter = ('storage_status', 'container')
    search_fields = ('vin', 'make', 'client__name')  # Поиск по VIN, марке и имени клиента

    def container_arrival_date(self, obj):
        return obj.container.arrival_date if obj.container else None

    container_arrival_date.short_description = 'ETA'

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

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('client', 'issue_date', 'due_date', 'amount', 'status')
    list_filter = ('status',)
    search_fields = ('client__name', 'status')


