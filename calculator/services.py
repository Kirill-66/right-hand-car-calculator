from decimal import Decimal

def calculate_ownership_cost(car, price_jpy, years, mileage, region):
    """Основная функция расчета стоимости владения"""
    JPY_TO_RUB = Decimal('0.60')
    price_rub = Decimal(price_jpy) * JPY_TO_RUB
    
    calculations = {
        'customs': price_rub * Decimal('0.3') + Decimal('20000'),
        'adaptation': Decimal('80000') if region in ['moscow', 'spb'] else Decimal('60000'),
        'insurance': Decimal('25000') * Decimal(years),
        'fuel': (Decimal(mileage) / Decimal('100')) * Decimal(str(car.fuel_consumption)) * Decimal('55') * Decimal(years),
        'maintenance': Decimal('40000') * Decimal(years),
        'tax': Decimal('35') * Decimal(str(car.engine_volume)) * Decimal(years) * Decimal('100'),
    }
    
    total = sum(calculations.values())
    
    return {
        'total': total,
        'breakdown': calculations,
        'per_year': total / Decimal(years),
        'price_rub': price_rub,
    }