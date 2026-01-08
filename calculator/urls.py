from django.urls import path
from . import views

urlpatterns = [
    # Основные страницы
    path('', views.home, name='home'),
    path('cars/', views.car_list, name='car_list'),
    
    # Расчет стоимости
    path('calculate/', views.calculation_create, name='calculation_create'),
    path('calculate/<int:calculation_id>/', views.calculation_result, name='calculation_result'),
    
    # Пользовательские
    path('my-calculations/', views.my_calculations, name='my_calculations'),
    path('calculation/<int:calculation_id>/delete/', views.calculation_delete, name='calculation_delete'),

    path('api/currency/', views.api_currency_rate, name='api_currency'),
    path('api/currency/all/', views.api_all_rates, name='api_all_rates'),
    path('api/calculate-customs/', views.api_calculate, name='api_calculate'),
    path('api/fuel-price/', views.api_fuel_price, name='api_fuel_price'),
]