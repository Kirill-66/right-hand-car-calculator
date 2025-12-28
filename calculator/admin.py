from django.contrib import admin
from .models import RightHandCar, OwnershipCalculation, CostItem

@admin.register(RightHandCar)
class RightHandCarAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'generation', 'year_from', 'year_to')
    search_fields = ('model', 'generation')
    list_filter = ('brand', 'fuel_type')

@admin.register(OwnershipCalculation)
class OwnershipCalculationAdmin(admin.ModelAdmin):
    list_display = ('id', 'car', 'purchase_price_jpy', 'ownership_years', 'region', 'created_at')
    list_filter = ('region', 'ownership_years', 'created_at')
    search_fields = ('car__model', 'car__brand')

@admin.register(CostItem)
class CostItemAdmin(admin.ModelAdmin):
    list_display = ('calculation', 'category', 'year', 'amount')
    list_filter = ('category', 'year')
    search_fields = ('calculation__car__model', 'description')