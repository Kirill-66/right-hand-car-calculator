from django.db import models
from django.contrib.auth.models import User

class RightHandCar(models.Model):
    """Модель праворульного автомобиля"""
    
    BRAND_CHOICES = [
        ('toyota', 'Toyota'),
        ('nissan', 'Nissan'),
        ('subaru', 'Subaru'),
        ('mitsubishi', 'Mitsubishi'),
        ('honda', 'Honda'),
    ]
    
    brand = models.CharField(max_length=20, choices=BRAND_CHOICES)
    model = models.CharField(max_length=50)
    generation = models.CharField(max_length=30, blank=True)
    year_from = models.IntegerField()
    year_to = models.IntegerField()
    engine_volume = models.FloatField(help_text="в литрах")
    fuel_type = models.CharField(max_length=10, 
                                choices=[('petrol', 'Бензин'), ('diesel', 'Дизель')])
    fuel_consumption = models.FloatField(help_text="л/100км средний")
    
    def __str__(self):
        return f"{self.get_brand_display()} {self.model}"


class OwnershipCalculation(models.Model):
    """Расчет стоимости владения автомобилем"""
    
    # Если пользователь авторизован
    user = models.ForeignKey(User, on_delete=models.CASCADE, 
                            null=True, blank=True, verbose_name='Пользователь')
    
    # Выбранный автомобиль
    car = models.ForeignKey(RightHandCar, on_delete=models.CASCADE, 
                           verbose_name='Автомобиль')
    
    # Основные параметры расчета
    purchase_price_jpy = models.IntegerField('Цена в Японии (¥)', default=500000)
    purchase_year = models.IntegerField('Год покупки', default=2024)
    annual_mileage = models.IntegerField('Годовой пробег (км)', default=15000)
    
    # Срок владения (выбор из 1-5 лет)
    OWNERSHIP_CHOICES = [(i, f"{i} {'год' if i==1 else 'года' if i<5 else 'лет'}") 
                         for i in range(1, 6)]
    ownership_years = models.IntegerField('Срок владения', choices=OWNERSHIP_CHOICES, default=3)
    
    # Регион для расчета (влияет на страховку и цены)
    REGION_CHOICES = [
        ('moscow', 'Москва'),
        ('spb', 'Санкт-Петербург'),
        ('vladivostok', 'Владивосток'),
        ('ekb', 'Екатеринбург'),
        ('other', 'Другой'),
    ]
    region = models.CharField('Регион', max_length=20, choices=REGION_CHOICES, default='moscow')
    
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Расчет владения'
        verbose_name_plural = 'Расчеты владения'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Расчет #{self.id} - {self.car} на {self.ownership_years} лет"


class CostItem(models.Model):
    """Статья расходов для расчета"""
    
    CALCULATION = 'calculation'
    CUSTOMS = 'customs'
    ADAPTATION = 'adaptation'
    INSURANCE = 'insurance'
    MAINTENANCE = 'maintenance'
    SPARE_PARTS = 'spare_parts'
    FUEL = 'fuel'
    TAX = 'tax'
    OTHER = 'other'
    
    CATEGORY_CHOICES = [
        (CALCULATION, 'Растаможка/Утильсбор'),
        (ADAPTATION, 'Адаптация под РФ'),
        (INSURANCE, 'Страховка (ОСАГО/КАСКО)'),
        (MAINTENANCE, 'Техобслуживание'),
        (SPARE_PARTS, 'Запчасти'),
        (FUEL, 'Топливо'),
        (TAX, 'Транспортный налог'),
        (OTHER, 'Прочие расходы'),
    ]
    
    calculation = models.ForeignKey(OwnershipCalculation, on_delete=models.CASCADE, 
                                   related_name='cost_items', verbose_name='Расчет')
    
    category = models.CharField('Категория', max_length=20, choices=CATEGORY_CHOICES)
    year = models.IntegerField('Год владения', help_text='1, 2, 3...')
    amount = models.DecimalField('Сумма (руб)', max_digits=10, decimal_places=2)
    description = models.TextField('Описание', blank=True)
    
    class Meta:
        verbose_name = 'Статья расходов'
        verbose_name_plural = 'Статьи расходов'
        ordering = ['calculation', 'year', 'category']
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.year} год: {self.amount} руб"