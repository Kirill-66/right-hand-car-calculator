from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.car_list, name='car_list'),
    path('calculator/', views.calculation_create, name='calculation_create'),
    path('calculator/<int:calculation_id>/', views.calculation_result, name='calculation_result'),
    path('my-calculations/', views.my_calculations, name='my_calculations'),
    path('my-calculations/<int:calculation_id>/delete/', views.calculation_delete, name='calculation_delete'),
    
    path('car/add/', views.car_create, name='car_create'),
    path('car/import/', views.car_import, name='car_import'),
    path('car/<int:car_id>/edit/', views.car_update, name='car_update'),
    path('car/<int:car_id>/delete/', views.car_delete, name='car_delete'),
    path('car/<int:car_id>/', views.car_detail, name='car_detail'),
    
    # API endpoints
    path('api/currency-rate/', views.api_currency_rate, name='api_currency_rate'),
    path('api/all-rates/', views.api_all_rates, name='api_all_rates'),
    path('api/car/<int:car_id>/details/', views.api_car_details, name='api_car_details'),
    path('api/quick-calculate/', views.quick_calculate, name='quick_calculate'),
    path('api/save-calculation/', views.api_save_calculation, name='api_save_calculation'),
]