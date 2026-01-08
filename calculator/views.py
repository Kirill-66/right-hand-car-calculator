from django.shortcuts import render
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from .models import RightHandCar, OwnershipCalculation
from .forms import CalculationForm

# Функции
def home(request):
    """Главная страница"""
    return render(request, 'calculator/home.html')

def calculation_result(request):
    """Результат расчета (заглушка)"""
    context = {
        'total_cost': 370000,
        'breakdown': {
            'customs': 90000,
            'adaptation': 80000,
            'insurance': 75000,
            'fuel': 60000,
            'maintenance': 50000,
            'tax': 15000,
        },
        'per_year': 123333,
        'price_rub': 300000,
        'car': {
            'brand': 'Toyota',
            'model': 'Mark II',
            'generation': 'JZX100',
        },
        'years': 3,
        'mileage': 15000,
        'region': 'Москва',
    }
    return render(request, 'calculator/result.html', context)

# Классы
class CarListView(ListView):
    """Список автомобилей"""
    model = RightHandCar
    template_name = 'calculator/car_list.html'
    context_object_name = 'cars'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cars = context['cars']
        
        # Группируем по маркам
        cars_by_brand = {}
        for car in cars:
            brand_name = car.get_brand_display()
            if brand_name not in cars_by_brand:
                cars_by_brand[brand_name] = []
            cars_by_brand[brand_name].append(car)
        
        context['cars_by_brand'] = cars_by_brand
        context['total_cars'] = cars.count()
        return context

class CalculationCreateView(CreateView):
    """Форма расчета"""
    model = OwnershipCalculation
    form_class = CalculationForm
    template_name = 'calculator/calculation_form.html'
    success_url = reverse_lazy('calculation_result')