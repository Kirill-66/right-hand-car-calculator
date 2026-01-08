from django.core.management.base import BaseCommand
from calculator.api_services import get_currency_rate

class Command(BaseCommand):
    help = 'Обновляет курсы валют в кэше'
    
    def handle(self, *args, **kwargs):
        currencies = ["USD", "EUR", "JPY"]
        
        for currency in currencies:
            rate = get_currency_rate(currency)
            self.stdout.write(
                self.style.SUCCESS(f'Курс {currency}: {rate} RUB')
            )