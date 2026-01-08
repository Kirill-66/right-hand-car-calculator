import requests
from datetime import datetime
from django.core.cache import cache

def get_cbr_currency_rate(currency_code="JPY"):
    cache_key = f"cbr_currency_rate_{currency_code}"
    cached_rate = cache.get(cache_key)
    
    if cached_rate is not None:
        return cached_rate
    
    try:
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'Valute' in data:
                for currency in data['Valute'].values():
                    if currency['CharCode'] == currency_code:
                        rate = currency['Value'] / currency['Nominal']
                        cache.set(cache_key, rate, 86400)
                        return round(rate, 4)
            
            return get_currency_rate_fallback(currency_code)
        else:
            return get_currency_rate_fallback(currency_code)
            
    except Exception:
        return get_currency_rate_fallback(currency_code)


def get_currency_rate_fallback(currency_code="JPY"):
    fallback_rates = {
        'USD': 90.50,
        'EUR': 98.20,
        'JPY': 0.60,
        'CNY': 12.50,
        'GBP': 114.30,
    }
    
    return fallback_rates.get(currency_code, 1.0)


def get_jpy_to_rub_rate():
    cache_key = "jpy_rub_rate"
    cached_rate = cache.get(cache_key)
    
    if cached_rate is not None:
        return cached_rate
    
    try:
        jpy_rate = get_cbr_currency_rate("JPY")
        
        if jpy_rate > 0.1:
            cache.set(cache_key, jpy_rate, 86400)
            return jpy_rate
        
        usd_rate = get_cbr_currency_rate("USD")
        jpy_usd_rate = 150.0
        jpy_rub_rate = usd_rate / jpy_usd_rate
        
        cache.set(cache_key, jpy_rub_rate, 86400)
        return round(jpy_rub_rate, 4)
        
    except Exception:
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
        'other': 53.5,
    }
    
    price = region_prices.get(region, 55.0)
    cache.set(cache_key, price, 86400)
    
    return price


def calculate_customs_cost(price_jpy, engine_volume, year):
    exchange_rate = get_jpy_to_rub_rate()
    price_rub = price_jpy * exchange_rate
    
    recycling_fee = 20000
    
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
    
    current_year = datetime.now().year
    car_age = current_year - year
    
    if car_age >= 7:
        age_multiplier = 1.5
    elif car_age >= 3:
        age_multiplier = 1.0
    else:
        age_multiplier = 0.8
    
    customs_duty = price_rub * base_rate * age_multiplier
    vat = (price_rub + customs_duty) * 0.2
    total_customs = customs_duty + vat + recycling_fee
    
    return {
        'exchange_rate': exchange_rate,
        'price_rub': round(price_rub),
        'customs_duty': round(customs_duty),
        'vat': round(vat),
        'recycling_fee': recycling_fee,
        'total': round(total_customs)
    }


def update_all_rates():
    rates = {}
    currencies = ['USD', 'EUR', 'JPY', 'CNY', 'GBP']
    
    for currency in currencies:
        rates[currency] = get_cbr_currency_rate(currency)
    
    return rates