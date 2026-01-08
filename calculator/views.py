from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import RightHandCar, OwnershipCalculation, CostItem
from .forms import CalculationForm, CarFilterForm


def home(request):
    """Главная страница сайта"""
    # Получаем популярные автомобили для отображения
    popular_cars = RightHandCar.objects.all()[:6]
    
    # Получаем статистику
    total_calculations = OwnershipCalculation.objects.count()
    total_cars = RightHandCar.objects.count()
    
    context = {
        'popular_cars': popular_cars,
        'total_calculations': total_calculations,
        'total_cars': total_cars,
        'recent_calculations': OwnershipCalculation.objects.order_by('-created_at')[:3]
    }
    
    return render(request, 'calculator/home.html', context)


def car_list(request):
    """Страница с каталогом автомобилей"""
    form = CarFilterForm(request.GET or None)
    cars = RightHandCar.objects.all().order_by('brand', 'model')
    
    # Применяем фильтры, если форма валидна
    if form.is_valid():
        brand = form.cleaned_data.get('brand')
        fuel_type = form.cleaned_data.get('fuel_type')
        year_from = form.cleaned_data.get('year_from')
        year_to = form.cleaned_data.get('year_to')
        
        if brand:
            cars = cars.filter(brand=brand)
        if fuel_type:
            cars = cars.filter(fuel_type=fuel_type)
        if year_from:
            cars = cars.filter(year_to__gte=year_from)  
            cars = cars.filter(year_from__lte=year_to)  
    
    paginator = Paginator(cars, 12) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем доступные марки для фильтра
    available_brands = RightHandCar.objects.values_list('brand', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_cars': cars.count(),
        'available_brands': available_brands,
    }
    
    return render(request, 'calculator/car_list.html', context)


def calculation_create(request):
    """Создание нового расчета стоимости"""
    if request.method == 'POST':
        form = CalculationForm(request.POST)
        if form.is_valid():
            calculation = form.save(commit=False)
            
            # Привязываем к пользователю, если он авторизован
            if request.user.is_authenticated:
                calculation.user = request.user
            
            calculation.save()
            
            # Выполняем расчет стоимости
            calculation = calculate_ownership_cost(calculation)
            
            messages.success(request, 'Расчет успешно создан!')
            return redirect('calculation_result', calculation_id=calculation.id)
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        car_id = request.GET.get('car')
        initial_data = {}
        
        if car_id:
            try:
                car = RightHandCar.objects.get(id=car_id)
                initial_data['car'] = car
            except RightHandCar.DoesNotExist:
                pass
        
        form = CalculationForm(initial=initial_data)
    
    # Получаем автомобили для подсказок
    cars = RightHandCar.objects.all()[:10]
    
    context = {
        'form': form,
        'cars': cars,
    }
    
    return render(request, 'calculator/calculation_form.html', context)


def calculation_result(request, calculation_id):
    """Отображение результата расчета"""
    calculation = get_object_or_404(OwnershipCalculation, id=calculation_id)
    
    if not calculation.total_cost:
        calculation = calculate_ownership_cost(calculation)
    
    # Получаем детализацию расходов
    cost_items = calculation.cost_items.all()
    
    # Группируем расходы по категориям для отображения
    breakdown = {
        'customs': calculation.customs_cost or 0,
        'adaptation': calculation.adaptation_cost or 0,
        'insurance': calculation.insurance_cost or 0,
        'fuel': calculation.fuel_cost or 0,
        'maintenance': calculation.maintenance_cost or 0,
        'tax': calculation.tax_cost or 0,
    }
    
    # Рассчитываем проценты
    total_cost = calculation.total_cost or 0
    for key in breakdown:
        if total_cost > 0:
            breakdown[f'{key}_percent'] = round((breakdown[key] / total_cost) * 100, 1)
        else:
            breakdown[f'{key}_percent'] = 0
    
    # Данные для контекста
    context = {
        'calculation': calculation,
        'car': calculation.car,
        'total_cost': calculation.total_cost or 0,
        'per_year': (calculation.total_cost or 0) / calculation.ownership_years if calculation.total_cost else 0,
        'price_rub': calculation.purchase_price_jpy * 0.6,  # Примерный курс
        'price_jpy': calculation.purchase_price_jpy,
        'mileage': calculation.annual_mileage,
        'years': calculation.ownership_years,
        'region': calculation.get_region_display(),
        'breakdown': breakdown,
        'cost_items': cost_items,
        'exchange_rate': 0.6,  
        'fuel_price': 55.5,    
    }
    
    return render(request, 'calculator/result.html', context)


@login_required
def my_calculations(request):
    """Список расчетов текущего пользователя"""
    calculations = OwnershipCalculation.objects.filter(user=request.user).order_by('-created_at')
    
    paginator = Paginator(calculations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_calculations': calculations.count(),
    }
    
    return render(request, 'calculator/my_calculations.html', context)


@login_required
def calculation_delete(request, calculation_id):
    """Удаление расчета"""
    calculation = get_object_or_404(OwnershipCalculation, id=calculation_id, user=request.user)
    
    if request.method == 'POST':
        calculation.delete()
        messages.success(request, 'Расчет успешно удален.')
        return redirect('my_calculations')
    
    return render(request, 'calculator/calculation_confirm_delete.html', {'calculation': calculation})


def calculate_ownership_cost(calculation):
    """Функция расчета стоимости владения"""
    
    EXCHANGE_RATE = 0.6  
    CUSTOMS_DUTY_RATE = 0.48 
    RECYCLING_FEE = 20000  
    ADAPTATION_COST = 150000  
    
    # Расчет основных расходов
    price_rub = calculation.purchase_price_jpy * EXCHANGE_RATE
    
    # 1. Таможня и утильсбор
    customs_cost = price_rub * CUSTOMS_DUTY_RATE + RECYCLING_FEE
    
    # 2. Адаптация
    adaptation_cost = ADAPTATION_COST
    
    # 3. Страховка (примерная формула)
    insurance_cost = (price_rub * 0.05) * calculation.ownership_years  
    # 4. Топливо
    fuel_price_per_liter = 55.5  # руб/л
    total_km = calculation.annual_mileage * calculation.ownership_years
    fuel_cost = (total_km / 100) * calculation.car.fuel_consumption * fuel_price_per_liter
    
    # 5. ТО и ремонты
    maintenance_cost = 30000 * calculation.ownership_years
    
    # 6. Транспортный налог
    tax_rate = 50  # руб за л.с.
    car_power = 150
    tax_cost = car_power * tax_rate * calculation.ownership_years
    
    # Итоговая стоимость
    total_cost = (
        customs_cost +
        adaptation_cost +
        insurance_cost +
        fuel_cost +
        maintenance_cost +
        tax_cost
    )
    
    # Сохраняем результаты
    calculation.customs_cost = customs_cost
    calculation.adaptation_cost = adaptation_cost
    calculation.insurance_cost = insurance_cost
    calculation.fuel_cost = fuel_cost
    calculation.maintenance_cost = maintenance_cost
    calculation.tax_cost = tax_cost
    calculation.total_cost = total_cost
    
    calculation.save()
    
    # Создаем детализацию расходов по годам
    CostItem.objects.filter(calculation=calculation).delete()  # Удаляем старые
    
    # Таможня и адаптация - только в первый год
    CostItem.objects.create(
        calculation=calculation,
        category='calculation',
        year=1,
        amount=customs_cost,
        description='Таможенные пошлины и утильсбор'
    )
    
    CostItem.objects.create(
        calculation=calculation,
        category='adaptation',
        year=1,
        amount=adaptation_cost,
        description='Адаптация под российские условия'
    )
    
    # Ежегодные расходы
    for year in range(1, calculation.ownership_years + 1):
        CostItem.objects.create(
            calculation=calculation,
            category='insurance',
            year=year,
            amount=insurance_cost / calculation.ownership_years,
            description='Страховка'
        )
        
        CostItem.objects.create(
            calculation=calculation,
            category='fuel',
            year=year,
            amount=fuel_cost / calculation.ownership_years,
            description='Топливо'
        )
        
        CostItem.objects.create(
            calculation=calculation,
            category='maintenance',
            year=year,
            amount=maintenance_cost / calculation.ownership_years,
            description='Техническое обслуживание'
        )
        
        CostItem.objects.create(
            calculation=calculation,
            category='tax',
            year=year,
            amount=tax_cost / calculation.ownership_years,
            description='Транспортный налог'
        )
    
    return calculation


# Обработчики ошибок
def handler404(request, exception):
    """Обработка ошибки 404"""
    return render(request, 'calculator/404.html', status=404)


def handler500(request):
    """Обработка ошибки 500"""
    return render(request, 'calculator/500.html', status=500)