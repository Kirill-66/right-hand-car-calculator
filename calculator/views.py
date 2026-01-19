from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Avg
import json
import base64
import io
from datetime import datetime
from decimal import Decimal

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None

from .models import RightHandCar, OwnershipCalculation, CostItem
from .forms import CalculationForm, CarFilterForm, RightHandCarForm, ImportCarsForm


def home(request):
    popular_cars = RightHandCar.objects.all()[:6]
    total_calculations = OwnershipCalculation.objects.count()
    total_cars = RightHandCar.objects.count()

    try:
        from .api_services import update_all_rates
        rates = update_all_rates()
    except:
        rates = {}

    context = {
        'popular_cars': popular_cars,
        'total_calculations': total_calculations,
        'total_cars': total_cars,
        'recent_calculations': OwnershipCalculation.objects.order_by('-created_at')[:3],
        'rates': rates,
    }

    return render(request, 'calculator/home.html', context)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('home')
        else:
            messages.error(request, 'Исправьте ошибки в форме')
    else:
        form = UserCreationForm()
    
    return render(request, 'calculator/register.html', {'form': form})


def car_list(request):
    form = CarFilterForm(request.GET or None)
    cars = RightHandCar.objects.all().order_by('brand', 'model')
    
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
        if year_to:
            cars = cars.filter(year_from__lte=year_to)
    
    paginator = Paginator(cars, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    available_brands = RightHandCar.objects.values_list('brand', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_cars': cars.count(),
        'available_brands': available_brands,
    }
    
    return render(request, 'calculator/car_list.html', context)


def calculation_create(request):
    if request.method == 'POST':
        form = CalculationForm(request.POST)
        if form.is_valid():
            calculation = form.save(commit=False)
            if request.user.is_authenticated:
                calculation.user = request.user
            calculation.save()
            
            try:
                from .api_services import get_jpy_to_rub_rate
                exchange_rate = get_jpy_to_rub_rate()
            except:
                exchange_rate = 0.6
                
            calculation = calculate_ownership_cost(calculation, exchange_rate)
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
    
    context = {
        'form': form,
    }
    
    return render(request, 'calculator/calculation_form.html', context)


def generate_cost_chart(breakdown):
    if not MATPLOTLIB_AVAILABLE:
        return None
    
    try:
        labels = ['Таможня', 'Адаптация', 'Страховка', 'Топливо', 'ТО', 'Налог']
        sizes = [
            float(breakdown.get('customs', 0)),
            float(breakdown.get('adaptation', 0)),
            float(breakdown.get('insurance', 0)),
            float(breakdown.get('fuel', 0)),
            float(breakdown.get('maintenance', 0)),
            float(breakdown.get('tax', 0))
        ]
        
        colors = ['#ff3b30', '#ff9500', '#007aff', '#34c759', '#5ac8fa', '#af52de']
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        explode = [0.1 if size == max(sizes) else 0 for size in sizes]
        
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            explode=explode,
            shadow=True,
            textprops={'fontsize': 11, 'fontweight': 'bold'}
        )
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')
        
        ax.legend(wedges, labels, title="Категории расходов", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        ax.axis('equal')
        
        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight', facecolor='#f8f9fa')
        buffer.seek(0)
        
        image_png = buffer.getvalue()
        buffer.close()
        plt.close(fig)
        
        graphic = base64.b64encode(image_png).decode('utf-8')
        return f"data:image/png;base64,{graphic}"
    
    except Exception as e:
        print(f"Error generating chart: {e}")
        return None


def calculation_result(request, calculation_id):
    calculation = get_object_or_404(OwnershipCalculation, id=calculation_id)
    
    if not calculation.total_cost:
        try:
            from .api_services import get_jpy_to_rub_rate
            exchange_rate = get_jpy_to_rub_rate()
        except:
            exchange_rate = 0.6
        calculation = calculate_ownership_cost(calculation, exchange_rate)
    
    cost_items = calculation.cost_items.all()
    
    try:
        from .api_services import get_jpy_to_rub_rate, get_russia_fuel_price
        exchange_rate = get_jpy_to_rub_rate()
        fuel_price = get_russia_fuel_price(calculation.region)
    except:
        exchange_rate = 0.6
        fuel_price = 55.5
    
    price_rub = float(calculation.purchase_price_jpy) * float(exchange_rate)
    total_cost_with_car = float(calculation.total_cost or 0)
    
    breakdown = {
        'customs': float(calculation.customs_cost or 0),
        'adaptation': float(calculation.adaptation_cost or 0),
        'insurance': float(calculation.insurance_cost or 0),
        'fuel': float(calculation.fuel_cost or 0),
        'maintenance': float(calculation.maintenance_cost or 0),
        'tax': float(calculation.tax_cost or 0),
    }
    
    keys = list(breakdown.keys())
    for key in keys:
        if total_cost_with_car > 0:
            breakdown[f'{key}_percent'] = round((breakdown[key] / total_cost_with_car) * 100, 1)
        else:
            breakdown[f'{key}_percent'] = 0
    
    chart_image = generate_cost_chart(breakdown)
    
    max_percent = max([
        breakdown.get('customs_percent', 0),
        breakdown.get('adaptation_percent', 0),
        breakdown.get('fuel_percent', 0),
        breakdown.get('insurance_percent', 0),
        breakdown.get('maintenance_percent', 0),
        breakdown.get('tax_percent', 0)
    ])
    
    context = {
        'calculation': calculation,
        'car': calculation.car,
        'total_cost': total_cost_with_car,
        'additional_costs': float(calculation.additional_costs or 0),
        'per_year': total_cost_with_car / float(calculation.ownership_years) if total_cost_with_car else 0,
        'price_rub': price_rub,
        'price_jpy': float(calculation.purchase_price_jpy),
        'mileage': calculation.annual_mileage,
        'years': calculation.ownership_years,
        'region': calculation.get_region_display(),
        'breakdown': breakdown,
        'cost_items': cost_items,
        'exchange_rate': exchange_rate,
        'fuel_price': fuel_price,
        'max_percent': max_percent,
        'chart_image': chart_image,
        'matplotlib_available': MATPLOTLIB_AVAILABLE,
    }
    
    return render(request, 'calculator/result.html', context)


@login_required
def my_calculations(request):
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
    calculation = get_object_or_404(OwnershipCalculation, id=calculation_id, user=request.user)
    
    if request.method == 'POST':
        calculation.delete()
        messages.success(request, 'Расчет успешно удален.')
        return redirect('my_calculations')
    
    return render(request, 'calculator/calculation_confirm_delete.html', {'calculation': calculation})


def calculate_ownership_cost(calculation, exchange_rate=0.6):
    try:
        from .api_services import (
            calculate_customs_cost,
            calculate_adaptation_cost,
            calculate_insurance_cost,
            calculate_transport_tax,
            get_russia_fuel_price
        )
        
        price_rub = float(calculation.purchase_price_jpy) * float(exchange_rate)
        
        customs_data = calculate_customs_cost(
            calculation.purchase_price_jpy,
            calculation.car.engine_volume,
            calculation.purchase_year
        )
        customs_cost = float(customs_data['total'])
        
        adaptation_data = calculate_adaptation_cost(
            calculation.car.engine_volume,
            calculation.region,
            calculation.purchase_year
        )
        adaptation_cost = float(adaptation_data['total'])
        
        insurance_data = calculate_insurance_cost(
            price_rub,
            calculation.region,
            calculation.purchase_year,
            calculation.car.engine_volume
        )
        annual_insurance = float(insurance_data['annual'])
        insurance_cost = annual_insurance * calculation.ownership_years
        
        fuel_price = float(get_russia_fuel_price(calculation.region))
        total_km = calculation.annual_mileage * calculation.ownership_years
        fuel_cost = (total_km / 100) * calculation.car.fuel_consumption * fuel_price
        
        maintenance_per_year = 25000 * (1 + (calculation.car.engine_volume - 2.0) * 0.2)
        maintenance_cost = maintenance_per_year * calculation.ownership_years
        
        tax_data = calculate_transport_tax(
            calculation.car.engine_volume,
            calculation.region,
            calculation.ownership_years
        )
        tax_cost = float(tax_data['total'])
        
        delivery_cost = 100000 if calculation.region == 'vladivostok' else 150000
        registration_cost = 5000
        
    except Exception as e:
        price_rub = float(calculation.purchase_price_jpy) * float(exchange_rate)
        
        CUSTOMS_DUTY_RATE = 0.48
        RECYCLING_FEE = 20000
        ADAPTATION_COST = 150000
        
        customs_cost = price_rub * CUSTOMS_DUTY_RATE + RECYCLING_FEE
        adaptation_cost = ADAPTATION_COST
        annual_insurance = (price_rub * 0.05)
        insurance_cost = annual_insurance * calculation.ownership_years
        
        try:
            fuel_price = 55.5
        except:
            fuel_price = 55.5
            
        total_km = calculation.annual_mileage * calculation.ownership_years
        fuel_cost = (total_km / 100) * calculation.car.fuel_consumption * fuel_price
        
        maintenance_per_year = 30000
        maintenance_cost = maintenance_per_year * calculation.ownership_years
        
        tax_rate = 50
        car_power = 150
        annual_tax = car_power * tax_rate
        tax_cost = annual_tax * calculation.ownership_years
        
        delivery_cost = 150000
        registration_cost = 5000
    
    one_time_costs = customs_cost + adaptation_cost + delivery_cost + registration_cost
    yearly_costs = (insurance_cost / calculation.ownership_years) + (fuel_cost / calculation.ownership_years) + (maintenance_cost / calculation.ownership_years) + (tax_cost / calculation.ownership_years)
    additional_costs = one_time_costs + (yearly_costs * calculation.ownership_years)
    total_cost_with_car = price_rub + additional_costs
    
    calculation.customs_cost = customs_cost
    calculation.adaptation_cost = adaptation_cost
    calculation.insurance_cost = insurance_cost
    calculation.fuel_cost = fuel_cost
    calculation.maintenance_cost = maintenance_cost
    calculation.tax_cost = tax_cost
    calculation.total_cost = total_cost_with_car
    calculation.additional_costs = additional_costs
    
    calculation.save()
    
    CostItem.objects.filter(calculation=calculation).delete()
    
    CostItem.objects.create(
        calculation=calculation,
        category='calculation',
        year=1,
        amount=customs_cost,
        description=f'Таможенные пошлины и утильсбор (курс: {exchange_rate:.4f})'
    )
    
    CostItem.objects.create(
        calculation=calculation,
        category='adaptation',
        year=1,
        amount=adaptation_cost,
        description='Адаптация под российские условия'
    )
    
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


@login_required
def car_create(request):
    if not request.user.is_superuser:
        messages.error(request, 'У вас нет прав для добавления автомобилей')
        return redirect('car_list')
    
    if request.method == 'POST':
        form = RightHandCarForm(request.POST, request.FILES)
        if form.is_valid():
            car = form.save()
            messages.success(request, f'Автомобиль {car.brand} {car.model} успешно добавлен!')
            return redirect('car_detail', car_id=car.id)
    else:
        form = RightHandCarForm()
    
    return render(request, 'calculator/car_form.html', {'form': form, 'title': 'Добавить автомобиль'})


@login_required
def car_update(request, car_id):
    if not request.user.is_superuser:
        messages.error(request, 'У вас нет прав для редактирования автомобилей')
        return redirect('car_list')
    
    car = get_object_or_404(RightHandCar, id=car_id)
    
    if request.method == 'POST':
        form = RightHandCarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            form.save()
            messages.success(request, f'Автомобиль {car.brand} {car.model} успешно обновлен!')
            return redirect('car_detail', car_id=car.id)
    else:
        form = RightHandCarForm(instance=car)
    
    return render(request, 'calculator/car_form.html', {'form': form, 'title': 'Редактировать автомобиль', 'car': car})


@login_required
def car_delete(request, car_id):
    if not request.user.is_superuser:
        messages.error(request, 'У вас нет прав для удаления автомобилей')
        return redirect('car_list')
    
    car = get_object_or_404(RightHandCar, id=car_id)
    
    if request.method == 'POST':
        car.delete()
        messages.success(request, 'Автомобиль успешно удален')
        return redirect('car_list')
    
    return render(request, 'calculator/car_confirm_delete.html', {'car': car})


def car_detail(request, car_id):
    car = get_object_or_404(RightHandCar, id=car_id)
    
    calculations = OwnershipCalculation.objects.filter(car=car).order_by('-created_at')[:5]
    
    avg_calculations = OwnershipCalculation.objects.filter(car__model=car.model)
    avg_total_cost = avg_calculations.aggregate(Avg('total_cost'))['total_cost__avg']
    
    context = {
        'car': car,
        'calculations': calculations,
        'avg_total_cost': float(avg_total_cost) if avg_total_cost else 0,
        'total_calculations': calculations.count(),
    }
    
    return render(request, 'calculator/car_detail.html', context)


@login_required
def car_import(request):
    if not request.user.is_superuser:
        messages.error(request, 'У вас нет прав для импорта автомобилей')
        return redirect('car_list')
    
    if request.method == 'POST':
        form = ImportCarsForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']
            update_existing = form.cleaned_data['update_existing']
            
            try:
                imported_count = 0
                updated_count = 0
                
                csv_text = csv_file.read().decode('utf-8').splitlines()
                
                import csv
                reader = csv.DictReader(csv_text)
                
                for row in reader:
                    defaults = {
                        'generation': row.get('generation', ''),
                        'year_from': int(row.get('year_from', 2000)),
                        'year_to': int(row.get('year_to', 2005)),
                        'engine_volume': float(row.get('engine_volume', 2.0)),
                        'fuel_type': row.get('fuel_type', 'petrol'),
                        'fuel_consumption': float(row.get('fuel_consumption', 10.0)) if row.get('fuel_consumption') else None,
                    }
                    
                    car, created = RightHandCar.objects.update_or_create(
                        brand=row['brand'],
                        model=row['model'],
                        defaults=defaults
                    )
                    
                    if created:
                        imported_count += 1
                    elif update_existing:
                        updated_count += 1
                
                messages.success(request, f'Импорт завершен: добавлено {imported_count}, обновлено {updated_count} автомобилей')
                return redirect('car_list')
                
            except Exception as e:
                messages.error(request, f'Ошибка импорта: {str(e)}')
    else:
        form = ImportCarsForm()
    
    return render(request, 'calculator/car_import.html', {'form': form})


def api_car_details(request, car_id):
    try:
        car = RightHandCar.objects.get(id=car_id)
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': car.id,
                'brand': car.brand,
                'model': car.model,
                'generation': car.generation,
                'year_from': car.year_from,
                'year_to': car.year_to,
                'engine_volume': car.engine_volume,
                'fuel_type': car.fuel_type,
                'fuel_consumption': car.fuel_consumption,
            }
        })
    except RightHandCar.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Автомобиль не найден'}, status=404)


def quick_calculate(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            
            price_jpy = float(data.get('price_jpy', 0))
            engine_volume = float(data.get('engine_volume', 2.0))
            car_year = int(data.get('year', 2000))
            region = data.get('region', 'moscow')
            annual_mileage = int(data.get('annual_mileage', 15000))
            ownership_years = int(data.get('ownership_years', 3))
            fuel_consumption = float(data.get('fuel_consumption', 10.0))
            
            try:
                from .api_services import (
                    get_jpy_to_rub_rate,
                    get_russia_fuel_price,
                    calculate_customs_cost,
                    calculate_adaptation_cost,
                    calculate_insurance_cost,
                    calculate_transport_tax
                )
                
                exchange_rate = float(get_jpy_to_rub_rate())
                fuel_price = float(get_russia_fuel_price(region))
                
                price_rub = price_jpy * exchange_rate
                
                customs_data = calculate_customs_cost(price_jpy, engine_volume, car_year)
                customs_cost = float(customs_data['total'])
                
                adaptation_data = calculate_adaptation_cost(engine_volume, region, car_year)
                adaptation_cost = float(adaptation_data['total'])
                
                insurance_data = calculate_insurance_cost(price_rub, region, car_year, engine_volume)
                annual_insurance = float(insurance_data['annual'])
                
                fuel_cost = calculate_fuel_cost(annual_mileage, ownership_years, fuel_price, fuel_consumption)
                
                maintenance_cost = calculate_maintenance_cost(car_year, engine_volume, ownership_years)
                
                tax_data = calculate_transport_tax(engine_volume, region, ownership_years)
                tax_cost = float(tax_data['total'])
                
            except Exception as e:
                exchange_rate = 0.6
                fuel_price = 55.5
                
                price_rub = price_jpy * exchange_rate
                
                customs_cost = calculate_customs_duty(price_rub, engine_volume, car_year)
                adaptation_cost = calculate_adaptation_cost(engine_volume, region)
                annual_insurance = calculate_insurance_cost(price_rub, region, car_year)
                fuel_cost = calculate_fuel_cost(annual_mileage, ownership_years, fuel_price, fuel_consumption)
                maintenance_cost = calculate_maintenance_cost(car_year, engine_volume, ownership_years)
                tax_cost = calculate_tax_cost(engine_volume, region, ownership_years)
            
            one_time_costs = customs_cost + adaptation_cost
            total_yearly_costs = (annual_insurance + (fuel_cost / ownership_years) + (maintenance_cost / ownership_years) + (tax_cost / ownership_years)) * ownership_years
            additional_costs = one_time_costs + total_yearly_costs
            total_cost_with_car = price_rub + additional_costs
            
            result = {
                'success': True,
                'calculations': {
                    'price_rub': round(price_rub, 2),
                    'price_jpy': price_jpy,
                    'customs_cost': round(customs_cost, 2),
                    'adaptation_cost': round(adaptation_cost, 2),
                    'annual_insurance': round(annual_insurance, 2),
                    'fuel_cost': round(fuel_cost, 2),
                    'maintenance_cost': round(maintenance_cost, 2),
                    'tax_cost': round(tax_cost, 2),
                    'additional_costs': round(additional_costs, 2),
                    'total_cost': round(total_cost_with_car, 2),
                    'cost_per_year': round(total_cost_with_car / ownership_years, 2),
                    'exchange_rate': exchange_rate
                }
            }
            
            return JsonResponse(result)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


def calculate_customs_duty(price_rub, engine_volume, car_year):
    if car_year < 2010:
        duty_rate = 0.48 if engine_volume <= 3.0 else 0.53
    else:
        duty_rate = 0.48
    
    recycling_fee = 20000
    return (price_rub * duty_rate) + recycling_fee


def calculate_adaptation_cost(engine_volume, region):
    base_cost = 120000
    
    if engine_volume > 3.0:
        base_cost *= 1.2
    elif engine_volume > 2.5:
        base_cost *= 1.1
    
    if region in ['moscow', 'spb']:
        base_cost *= 1.15
    
    return base_cost


def calculate_insurance_cost(price_rub, region, car_year):
    base_rate = 0.05
    
    if car_year < 2000:
        age_coeff = 1.3
    elif car_year < 2010:
        age_coeff = 1.1
    else:
        age_coeff = 1.0
    
    if region in ['moscow', 'spb']:
        region_coeff = 1.2
    else:
        region_coeff = 1.0
    
    return price_rub * base_rate * age_coeff * region_coeff


def calculate_fuel_cost(annual_mileage, years, fuel_price, fuel_consumption):
    total_km = annual_mileage * years
    return (total_km / 100) * fuel_consumption * fuel_price


def calculate_maintenance_cost(car_year, engine_volume, years):
    base_cost = 25000
    
    if car_year < 2000:
        age_coeff = 1.5
    elif car_year < 2010:
        age_coeff = 1.2
    else:
        age_coeff = 1.0
    
    if engine_volume > 3.0:
        volume_coeff = 1.3
    elif engine_volume > 2.0:
        volume_coeff = 1.1
    else:
        volume_coeff = 1.0
    
    return base_cost * age_coeff * volume_coeff * years


def calculate_tax_cost(engine_volume, region, years):
    tax_rates = {
        'moscow': 25,
        'spb': 35,
        'center': 20,
        'siberia': 18,
        'east': 15
    }
    rate = tax_rates.get(region, 25)
    
    horse_power = engine_volume * 70
    
    return horse_power * rate * years


def api_save_calculation(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            car_id = data.get('car_id')
            price_jpy = float(data.get('price_jpy', 0))
            engine_volume = float(data.get('engine_volume', 2.0))
            car_year = int(data.get('year', 2000))
            region = data.get('region', 'moscow')
            annual_mileage = int(data.get('annual_mileage', 15000))
            ownership_years = int(data.get('ownership_years', 3))
            
            calculation = OwnershipCalculation.objects.create(
                user=request.user if request.user.is_authenticated else None,
                car=RightHandCar.objects.get(id=car_id) if car_id else None,
                purchase_price_jpy=price_jpy,
                annual_mileage=annual_mileage,
                ownership_years=ownership_years,
                region=region,
            )
            
            try:
                from .api_services import get_jpy_to_rub_rate
                exchange_rate = get_jpy_to_rub_rate()
            except:
                exchange_rate = 0.6
                
            calculation = calculate_ownership_cost(calculation, exchange_rate)
            
            return JsonResponse({
                'success': True,
                'calculation_id': calculation.id,
                'message': 'Расчет сохранен успешно'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


def api_currency_rate(request):
    currency = request.GET.get('currency', 'JPY')
    
    try:
        from .api_services import get_jpy_to_rub_rate, get_cbr_currency_rate
        
        if currency == 'JPY':
            rate = get_jpy_to_rub_rate()
        else:
            rate = get_cbr_currency_rate(currency)
            
        return JsonResponse({
            'success': True,
            'currency': currency,
            'rate': rate,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def api_all_rates(request):
    try:
        from .api_services import update_all_rates
        rates = update_all_rates()
        
        return JsonResponse({
            'success': True,
            'rates': rates,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)