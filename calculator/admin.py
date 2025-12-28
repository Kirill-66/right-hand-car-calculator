from django.contrib import admin
from .models import RightHandCar

@admin.register(RightHandCar)
class RightHandCarAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'generation', 'year_from', 'year_to')
    search_fields = ('model', 'generation')
    list_filter = ('brand', 'fuel_type')