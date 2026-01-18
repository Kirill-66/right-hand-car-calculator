import requests
from datetime import datetime
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

def get_cbr_currency_rate(currency_code="JPY"):
    cache_key = f"cbr_currency_rate_{currency_code}"
    cached_rate = cache.get(cache_key)
    
    if cached_rate is not None:
        return cached_rate
    
    try:
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if currency_code in data['Valute']:
                currency = data['Valute'][currency_code]
                rate = currency['Value'] / currency['Nominal']
                cache.set(cache_key, rate, 3600)  # 1 час кэш
                logger.info(f"Successfully fetched {currency_code} rate: {rate}")
                return round(rate, 4)
            
        return get_currency_rate_fallback(currency_code)
            
    except Exception as e:
        logger.error(f"Error fetching {currency_code} rate: {e}")
        return get_currency_rate_fallback(currency_code)


def get_currency_rate_fallback(currency_code="JPY"):
    fallback_rates = {
        'USD': 90.50,
        'EUR': 98.20,
        'JPY': 0.60,
        'CNY': 12.50,
        'GBP': 114.30,
        'CHF': 105.75,
        'CAD': 67.25,
        'AUD': 59.80,
    }
    
    rate = fallback_rates.get(currency_code, 1.0)
    logger.warning(f"Using fallback rate for {currency_code}: {rate}")
    return rate


def get_jpy_to_rub_rate():
    cache_key = "jpy_rub_rate"
    cached_rate = cache.get(cache_key)
    
    if cached_rate is not None:
        return cached_rate
    
    try:
        jpy_rate = get_cbr_currency_rate("JPY")
        
        if 0.1 < jpy_rate < 2.0:  
            cache.set(cache_key, jpy_rate, 3600)
            return jpy_rate
        
        usd_rate = get_cbr_currency_rate("USD")
        try:
            jpy_usd_response = requests.get(
                'https://api.exchangerate-api.com/v4/latest/JPY',
                timeout=3
            )
            if jpy_usd_response.status_code == 200:
                jpy_usd_data = jpy_usd_response.json()
                jpy_usd_rate = jpy_usd_data['rates'].get('USD', 0.0067)
            else:
                jpy_usd_rate = 0.0067 
        except:
            jpy_usd_rate = 0.0067
        
        jpy_rub_rate = usd_rate * jpy_usd_rate
        
        if 0.1 < jpy_rub_rate < 2.0:
            cache.set(cache_key, jpy_rub_rate, 3600)
            return round(jpy_rub_rate, 4)
        
        return 0.60
        
    except Exception as e:
        logger.error(f"Error calculating JPY/RUB rate: {e}")
        return 0.60


def get_russia_fuel_price(region="moscow"):
    cache_key = f"russia_fuel_price_{region}"
    cached_price = cache.get(cache_key)
    
    if cached_price is not None:
        return cached_price
    
    region_prices = {
        'moscow': 55.5,
        'spb': 56.0,
        'vladivostok': 58.5,
        'ekb': 54.8,
        'novosibirsk': 53.9,
        'kazan': 53.2,
        'nnovgorod': 53.5,
        'samara': 53.0,
        'chelyabinsk': 52.8,
        'omsk': 52.5,
        'rostov': 53.3,
        'ufa': 52.9,
        'krasnoyarsk': 54.1,
        'perm': 53.0,
        'voronezh': 53.2,
        'volgograd': 52.8,
        'saratov': 52.5,
        'tyumen': 53.7,
        'krasnodar': 53.9,
        'tolyatti': 52.8,
        'barnaul': 52.6,
        'other': 53.5,
    }
    
    price = region_prices.get(region, 55.0)
    cache.set(cache_key, price, 86400)  
    
    return price


def calculate_customs_cost(price_jpy, engine_volume, year):
    """Расчет таможенных платежей для праворульного автомобиля"""
    
    exchange_rate = get_jpy_to_rub_rate()
    price_rub = price_jpy * exchange_rate
    
    current_year = datetime.now().year
    car_age = current_year - year
    
    if car_age >= 7:
        recycling_fee = 20000
    elif car_age >= 3:
        recycling_fee = 25000
    else:
        recycling_fee = 30000
    
    if engine_volume <= 1.0:
        base_rate = 0.15
    elif engine_volume <= 1.5:
        base_rate = 0.175
    elif engine_volume <= 1.8:
        base_rate = 0.2
    elif engine_volume <= 2.5:
        base_rate = 0.25
    elif engine_volume <= 3.0:
        base_rate = 0.3
    else:
        base_rate = 0.35
    
    if car_age >= 15:
        age_multiplier = 2.0
    elif car_age >= 10:
        age_multiplier = 1.8
    elif car_age >= 7:
        age_multiplier = 1.5
    elif car_age >= 3:
        age_multiplier = 1.0
    else:
        age_multiplier = 0.8
    
    customs_duty = price_rub * base_rate * age_multiplier
    
    vat = (price_rub + customs_duty) * 0.2
    
    excise = 0
    if engine_volume > 3.0:
        excise_rate_per_hp = 491  
        estimated_hp = engine_volume * 100  
        excise = excise_rate_per_hp * estimated_hp * 0.1 
    
    broker_fee = max(15000, price_rub * 0.01)
    
    total_customs = customs_duty + vat + excise + recycling_fee + broker_fee
    
    return {
        'exchange_rate': exchange_rate,
        'price_rub': round(price_rub),
        'customs_duty': round(customs_duty),
        'vat': round(vat),
        'excise': round(excise),
        'recycling_fee': recycling_fee,
        'broker_fee': round(broker_fee),
        'total': round(total_customs),
        'base_rate_percent': base_rate * 100,
        'age_multiplier': age_multiplier,
        'car_age_years': car_age,
    }


def calculate_adaptation_cost(engine_volume, region, car_year):
    """Расчет стоимости адаптации праворульного автомобиля"""
    
    base_cost = 120000  
    
    if engine_volume > 3.0:
        volume_multiplier = 1.3
    elif engine_volume > 2.5:
        volume_multiplier = 1.2
    elif engine_volume > 2.0:
        volume_multiplier = 1.1
    else:
        volume_multiplier = 1.0
    
    region_multipliers = {
        'moscow': 1.25,
        'spb': 1.20,
        'vladivostok': 1.15,
        'ekb': 1.10,
        'other': 1.05,
    }
    region_multiplier = region_multipliers.get(region, 1.05)
    
    current_year = datetime.now().year
    car_age = current_year - car_year
    if car_age > 20:
        age_multiplier = 1.4
    elif car_age > 15:
        age_multiplier = 1.3
    elif car_age > 10:
        age_multiplier = 1.2
    else:
        age_multiplier = 1.0
    
    total_cost = base_cost * volume_multiplier * region_multiplier * age_multiplier
    
    return {
        'base_cost': base_cost,
        'volume_multiplier': volume_multiplier,
        'region_multiplier': region_multiplier,
        'age_multiplier': age_multiplier,
        'total': round(total_cost),
    }


def calculate_insurance_cost(price_rub, region, car_year, engine_volume):
    """Расчет стоимости страховки"""
    
    base_rate = 0.05
    
    region_coefficients = {
        'moscow': 1.5,
        'spb': 1.4,
        'vladivostok': 1.2,
        'ekb': 1.3,
        'other': 1.1,
    }
    region_coeff = region_coefficients.get(region, 1.1)
    
    current_year = datetime.now().year
    car_age = current_year - car_year
    
    if car_age > 20:
        age_coeff = 2.0
    elif car_age > 15:
        age_coeff = 1.8
    elif car_age > 10:
        age_coeff = 1.5
    elif car_age > 5:
        age_coeff = 1.2
    else:
        age_coeff = 1.0
    
    if engine_volume > 3.0:
        engine_coeff = 1.5
    elif engine_volume > 2.5:
        engine_coeff = 1.3
    elif engine_volume > 2.0:
        engine_coeff = 1.1
    else:
        engine_coeff = 1.0
    
    annual_insurance = price_rub * base_rate * region_coeff * age_coeff * engine_coeff
    
    return {
        'base_rate_percent': base_rate * 100,
        'region_coeff': region_coeff,
        'age_coeff': age_coeff,
        'engine_coeff': engine_coeff,
        'annual': round(annual_insurance),
    }


def calculate_transport_tax(engine_volume, region, ownership_years):
    """Расчет транспортного налога"""
    
    tax_rates = {
        'moscow': 25,
        'spb': 35,
        'vladivostok': 18,
        'ekb': 22,
        'other': 20,
    }
    rate = tax_rates.get(region, 20)
    
    estimated_hp = engine_volume * 70
    
    annual_tax = estimated_hp * rate
    
    total_tax = annual_tax * ownership_years
    
    return {
        'rate_per_hp': rate,
        'estimated_hp': round(estimated_hp),
        'annual': round(annual_tax),
        'total': round(total_tax),
    }


def update_all_rates():
    """Обновление всех курсов валют"""
    
    cache_key = "all_currency_rates"
    cached_rates = cache.get(cache_key)
    
    if cached_rates is not None:
        return cached_rates
    
    rates = {}
    currencies = ['USD', 'EUR', 'JPY', 'CNY', 'GBP', 'CHF', 'CAD', 'AUD']
    
    for currency in currencies:
        rates[currency] = get_cbr_currency_rate(currency)
    
    rates['timestamp'] = datetime.now().isoformat()
    rates['fuel_prices'] = {
        'moscow': get_russia_fuel_price('moscow'),
        'spb': get_russia_fuel_price('spb'),
        'vladivostok': get_russia_fuel_price('vladivostok'),
        'average': 54.5,
    }
    
    cache.set(cache_key, rates, 3600)
    
    logger.info("Updated all currency rates")
    return rates


def get_japan_auction_prices(car_model, year):
    """Получение примерных цен с японских аукционов"""
    
    cache_key = f"japan_auction_{car_model}_{year}"
    cached_data = cache.get(cache_key)
    
    if cached_data is not None:
        return cached_data
    
    sample_prices = {
        'toyota_mark_ii': {
            1998: 300000,
            1999: 320000,
            2000: 350000,
            2001: 380000,
            2002: 400000,
            2003: 420000,
            2004: 450000,
        },
        'nissan_skyline': {
            1999: 500000,
            2000: 550000,
            2001: 600000,
            2002: 650000,
            2003: 700000,
            2004: 750000,
        },
        'subaru_impreza': {
            1998: 350000,
            1999: 380000,
            2000: 400000,
            2001: 420000,
            2002: 450000,
            2003: 480000,
            2004: 500000,
        },
    }
    
    model_key = car_model.lower().replace(' ', '_')
    
    if model_key in sample_prices:
        years = sample_prices[model_key]
        closest_year = min(years.keys(), key=lambda x: abs(x - year))
        price = years[closest_year]
        
        year_diff = year - closest_year
        if year_diff != 0:
            price = price * (1 - 0.05 * year_diff) 
        
        result = {
            'price_jpy': round(price),
            'source_year': closest_year,
            'model': car_model,
            'year': year,
            'confidence': 'estimated',
        }
    else:
        base_price = 400000
        current_year = datetime.now().year
        age = current_year - year
        depreciation = 0.07 * age  
        
        result = {
            'price_jpy': round(base_price * (1 - min(depreciation, 0.7))),  
            'source_year': None,
            'model': car_model,
            'year': year,
            'confidence': 'low',
        }
    
    cache.set(cache_key, result, 86400) 
    return result


def calculate_total_ownership_cost(params):
    """Полный расчет стоимости владения"""
    
    price_jpy = params.get('price_jpy', 500000)
    engine_volume = params.get('engine_volume', 2.0)
    car_year = params.get('year', 2000)
    region = params.get('region', 'moscow')
    annual_mileage = params.get('annual_mileage', 15000)
    ownership_years = params.get('ownership_years', 3)
    fuel_consumption = params.get('fuel_consumption', 10.0)
    
    exchange_rate = get_jpy_to_rub_rate()
    price_rub = price_jpy * exchange_rate
    
    customs_data = calculate_customs_cost(price_jpy, engine_volume, car_year)
    
    adaptation_data = calculate_adaptation_cost(engine_volume, region, car_year)
    
    insurance_data = calculate_insurance_cost(price_rub, region, car_year, engine_volume)
    
    fuel_price = get_russia_fuel_price(region)
    total_km = annual_mileage * ownership_years
    fuel_cost = (total_km / 100) * fuel_consumption * fuel_price
    
    maintenance_per_year = 25000 * (1 + (engine_volume - 2.0) * 0.2)  
    total_maintenance = maintenance_per_year * ownership_years
    
    tax_data = calculate_transport_tax(engine_volume, region, ownership_years)
    
    delivery_cost = 100000 if region == 'vladivostok' else 150000
    registration_cost = 5000
    
    one_time_costs = (
        customs_data['total'] +
        adaptation_data['total'] +
        delivery_cost +
        registration_cost
    )
    
    annual_costs = (
        insurance_data['annual'] +
        (fuel_cost / ownership_years) +
        maintenance_per_year +
        (tax_data['total'] / ownership_years)
    )
    
    total_cost = one_time_costs + (annual_costs * ownership_years)
    
    return {
        'success': True,
        'calculations': {
            'price_jpy': price_jpy,
            'price_rub': round(price_rub),
            'exchange_rate': exchange_rate,
            
            'customs': customs_data,
            'adaptation': adaptation_data,
            'insurance': insurance_data,
            'fuel': {
                'price_per_liter': fuel_price,
                'consumption': fuel_consumption,
                'total_km': total_km,
                'total_cost': round(fuel_cost),
                'annual_cost': round(fuel_cost / ownership_years),
            },
            'maintenance': {
                'annual': round(maintenance_per_year),
                'total': round(total_maintenance),
            },
            'tax': tax_data,
            'other_costs': {
                'delivery': delivery_cost,
                'registration': registration_cost,
            },
            
            'summary': {
                'one_time_costs': round(one_time_costs),
                'annual_costs': round(annual_costs),
                'total_cost': round(total_cost),
                'cost_per_year': round(total_cost / ownership_years),
                'ownership_years': ownership_years,
                'total_mileage': total_km,
            }
        }
    }