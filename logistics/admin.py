from django.contrib import admin
from django.utils import timezone
from .models import Car, Payment, Warehouse, Container, Client, Invoice


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('car', 'container', 'amount_due', 'amount_paid', 'get_balance', 'payment_date', 'status', 'is_partial')
    list_filter = ('status', 'is_partial')
    search_fields = ('car__vin', 'container__number', 'status')

    def get_balance(self, obj):
        return obj.get_balance()
    get_balance.short_description = 'долг'


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'capacity')


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('vin', 'make', 'days_on_warehouse_display', 'client', 'status', 'title', 'container', 'container_arrival_date')  # Замени 'storage_status' на 'status'
    list_filter = ('storage_status', 'container')
    search_fields = ('vin', 'make', 'client__name')

    def status(self, obj):  # Переименовали метод
        return obj.storage_status
    status.short_description = "STATUS"

    def days_on_warehouse_display(self, obj):
        if obj.storage_status == 'in_warehouse' and obj.date_stored:
            return (timezone.now().date() - obj.date_stored).days
        return 0
    days_on_warehouse_display.short_description = "DAYS"

    def container_arrival_date(self, obj):
        return obj.container.arrival_date if obj.container else None
    container_arrival_date.short_description = 'ETA'


class CarInline(admin.TabularInline):
    model = Car
    extra = 1


@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    list_display = ('number', 'arrival_date', 'status', 'warehouse')
    list_filter = ('status', 'warehouse')
    inlines = [CarInline]


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'address')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('client', 'issue_date', 'due_date', 'amount', 'status')
    list_filter = ('status',)
    search_fields = ('client__name', 'status')
