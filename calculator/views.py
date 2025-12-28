from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, DetailView
from django.urls import reverse_lazy
from .models import RightHandCar, OwnershipCalculation
from .forms import CalculationForm

def home(request):
    """Главная страница"""
    return render(request, 'calculator/home.html')

class CarListView(ListView):
    """Список доступных автомобилей"""
    model = RightHandCar
    template_name = 'calculator/car_list.html'
    context_object_name = 'cars'

class CalculationCreateView(CreateView):
    """Создание нового расчета"""
    model = OwnershipCalculation
    form_class = CalculationForm
    template_name = 'calculator/calculation_form.html'
    success_url = reverse_lazy('calculation_result')
    
    def form_valid(self, form):
        # Если пользователь авторизован, сохраняем его
        if self.request.user.is_authenticated:
            form.instance.user = self.request.user
        return super().form_valid(form)

def calculation_result(request, pk=None):
    """Результат расчета"""
    # Пока заглушка
    context = {
        'message': 'Здесь будет результат расчета',
        'total_cost': 150000,
        'years': 3,
    }
    return render(request, 'calculator/result.html', context)