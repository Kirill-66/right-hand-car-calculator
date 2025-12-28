from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cars/', views.CarListView.as_view(), name='car_list'),
    path('calculate/', views.CalculationCreateView.as_view(), name='calculation_create'),
    path('result/', views.calculation_result, name='calculation_result'),
]