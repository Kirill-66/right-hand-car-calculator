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
]