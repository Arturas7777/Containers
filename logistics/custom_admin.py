from django.contrib import admin
from django.utils import timezone
from django import forms
from .models import Car, Payment, Warehouse, Container, Client, Invoice


class LogisticsAdminSite(admin.AdminSite):
    site_header = "Логистическая система"
    site_title = "Админка логистики"
    index_title = "Управление модулями"

    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        logistics_app = None
        for i, app in enumerate(app_list):
            if app['app_label'] == 'logistics':
                logistics_app = app_list.pop(i)
                break
        if logistics_app:
            app_list.insert(0, logistics_app)
        return app_list


admin_site = LogisticsAdminSite(name='logistics_admin')


class CarInline(admin.TabularInline):
    model = Car
    extra = 0
    fields = ('vin', 'make', 'storage_status', 'client')


class InvoiceCarInlineForm(forms.ModelForm):
    ths = forms.DecimalField(label="THS")
    sklad_combined = forms.DecimalField(label="SKLAD + Наценка")
    days_cost = forms.DecimalField(label="DAYS")

    class Meta:
        model = Invoice.cars.through
        fields = ('car',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'car') and self.instance.car:
            car = self.instance.car
            self.fields['ths'].initial = car.ths
            self.fields['sklad_combined'].initial = car.sklad + car.prof
            self.fields['days_cost'].initial = car.days_cost

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit and instance.car:
            car = instance.car
            car.ths = self.cleaned_data['ths']
            car.days_cost = self.cleaned_data['days_cost']
            new_sklad_combined = self.cleaned_data['sklad_combined']
            car.prof = new_sklad_combined - car.sklad
            car.save()
        if commit:
            instance.save()
        return instance


class InvoiceCarInline(admin.TabularInline):
    model = Invoice.cars.through
    form = InvoiceCarInlineForm
    extra = 1
    verbose_name = "Автомобиль"
    verbose_name_plural = "Автомобили"
    fields = ('car', 'ths', 'sklad_combined', 'days_cost')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'car':
            invoice_id = request.resolver_match.kwargs.get('object_id')
            if invoice_id:
                invoice = Invoice.objects.get(id=invoice_id)
                if invoice.client:
                    kwargs['queryset'] = Car.objects.filter(
                        client=invoice.client,
                        storage_status='in_warehouse'
                    )
            else:
                kwargs['queryset'] = Car.objects.filter(storage_status='in_warehouse')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class CarAdmin(admin.ModelAdmin):
    list_display = ('vin', 'make', 'days_on_warehouse_display', 'client', 'storage_status', 'title', 'container',
                    'container_arrival_date')
    list_filter = ('storage_status', 'container')
    search_fields = ('vin', 'make', 'client__name')

    fieldsets = (
        (None, {
            'fields': ('vin', 'make', 'client', 'storage_status', 'title', 'container', 'date_stored', 'warehouse')
        }),
        ('Расходы и итоговая цена', {
            'fields': ('ths', 'sklad', 'days_cost', 'prof', 'total')
        }),
    )
    readonly_fields = ('total',)

    def days_on_warehouse_display(self, obj):
        if obj.storage_status == 'in_warehouse' and obj.date_stored:
            return (timezone.now().date() - obj.date_stored).days
        return 0

    days_on_warehouse_display.short_description = "DAYS"

    def container_arrival_date(self, obj):
        return obj.container.arrival_date if obj.container else None

    container_arrival_date.short_description = 'ETA'

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields


class ContainerAdmin(admin.ModelAdmin):
    list_display = ('number', 'arrival_date', 'status', 'warehouse')
    list_filter = ('status', 'warehouse')
    inlines = [CarInline]

    fieldsets = (
        (None, {
            'fields': (
                'number',
                'arrival_date',
                'warehouse',
                'status',
                'ths',
            )
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.save()


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'car', 'container', 'amount_due', 'amount_paid', 'payment_date', 'status', 'payment_type')
    list_filter = ('status', 'payment_type')
    search_fields = ('car__vin', 'container__number')

    fieldsets = (
        (None, {
            'fields': ('car', 'container', 'amount_due', 'amount_paid', 'status', 'payment_type')
        }),
    )
    readonly_fields = ('payment_date',)  # Перенесли payment_date сюда


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'issue_date', 'due_date', 'amount', 'status')
    list_filter = ('status',)
    search_fields = ('client__name', 'status')
    inlines = [InvoiceCarInline]
    readonly_fields = ('amount',)
    exclude = ('cars',)

    actions = ['mark_as_paid']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.update_amount()

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.update_amount()

    def mark_as_paid(self, request, queryset):
        queryset.update(status='paid')

    mark_as_paid.short_description = "Пометить выбранные счета как оплаченные"


admin_site.register(Car, CarAdmin)
admin_site.register(Payment, PaymentAdmin)
admin_site.register(Warehouse)
admin_site.register(Container, ContainerAdmin)
admin_site.register(Client)
admin_site.register(Invoice, InvoiceAdmin)