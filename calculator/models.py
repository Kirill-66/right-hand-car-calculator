from django.db import models
from django.contrib.auth.models import User


class RightHandCar(models.Model):
    BRAND_CHOICES = [
        ('toyota', 'Toyota'),
        ('nissan', 'Nissan'),
        ('subaru', 'Subaru'),
        ('mitsubishi', 'Mitsubishi'),
        ('honda', 'Honda'),
    ]
    
    FUEL_CHOICES = [
        ('petrol', 'Бензин'),
        ('diesel', 'Дизель'),
    ]
    
    brand = models.CharField(
        max_length=20,
        choices=BRAND_CHOICES,
        verbose_name="Марка"
    )
    
    model = models.CharField(max_length=50, verbose_name="Модель")
    generation = models.CharField(
        max_length=30,
        verbose_name="Поколение",
        blank=True
    )
    
    year_from = models.IntegerField(verbose_name="Год выпуска с")
    year_to = models.IntegerField(verbose_name="Год выпуска по")
    
    engine_volume = models.FloatField(
        verbose_name="Объем двигателя",
        help_text="в литрах"
    )
    
    fuel_type = models.CharField(
        max_length=10,
        choices=FUEL_CHOICES,
        verbose_name="Тип топлива"
    )
    
    fuel_consumption = models.FloatField(
        verbose_name="Расход топлива",
        help_text="л/100км средний"
    )
    
    description = models.TextField(
        verbose_name="Описание",
        blank=True
    )
    
    image_url = models.URLField(
        'URL изображения',
        max_length=500,
        blank=True,
        null=True,
        help_text='Ссылка на фото автомобиля (рекомендуется 400x250px)'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )
    
    class Meta:
        verbose_name = "Праворульный автомобиль"
        verbose_name_plural = "Праворульные автомобили"
        ordering = ['brand', 'model', 'year_from']
    
    def __str__(self):
        if self.generation:
            return f"{self.get_brand_display()} {self.model} ({self.generation})"
        return f"{self.get_brand_display()} {self.model}"
    
    @property
    def years_range(self):
        """Диапазон лет выпуска"""
        if self.year_from == self.year_to:
            return str(self.year_from)
        return f"{self.year_from}-{self.year_to}"
    
    @property
    def brand_display(self):
        """Человеко-читаемое название марки"""
        return self.get_brand_display()


class OwnershipCalculation(models.Model):
    REGION_CHOICES = [
        ('moscow', 'Москва'),
        ('spb', 'Санкт-Петербург'),
        ('vladivostok', 'Владивосток'),
        ('ekb', 'Екатеринбург'),
        ('other', 'Другой'),
    ]
    
    OWNERSHIP_YEARS_CHOICES = [
        (1, '1 год'),
        (2, '2 года'),
        (3, '3 года'),
        (4, '4 года'),
        (5, '5 лет'),
    ]
    
    car = models.ForeignKey(
        RightHandCar,
        on_delete=models.CASCADE,
        verbose_name="Автомобиль"
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        null=True,
        blank=True
    )
    
    purchase_price_jpy = models.IntegerField(
        verbose_name="Цена в Японии (¥)",
        default=500000
    )
    
    purchase_year = models.IntegerField(
        verbose_name="Год покупки",
        default=2024
    )
    
    annual_mileage = models.IntegerField(
        verbose_name="Годовой пробег (км)",
        default=15000
    )
    
    ownership_years = models.IntegerField(
        verbose_name="Срок владения",
        choices=OWNERSHIP_YEARS_CHOICES,
        default=3
    )
    
    region = models.CharField(
        max_length=20,
        verbose_name="Регион",
        choices=REGION_CHOICES,
        default='moscow'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )
    
    class Meta:
        verbose_name = "Расчет владения"
        verbose_name_plural = "Расчеты владения"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Расчет #{self.id}: {self.car.brand_display} {self.car.model}"
    
    @property
    def price_in_rub(self):
        """Конвертирует цену в йенах в рубли"""
        return self.purchase_price_jpy * 0.6
    
    @property
    def total_mileage(self):
        """Общий пробег за весь срок владения"""
        return self.annual_mileage * self.ownership_years


class CostItem(models.Model):
    CATEGORY_CHOICES = [
        ('calculation', 'Растаможка/Утильсбор'),
        ('adaptation', 'Адаптация под РФ'),
        ('insurance', 'Страховка (ОСАГО/КАСКО)'),
        ('maintenance', 'Техобслуживание'),
        ('spare_parts', 'Запчасти'),
        ('fuel', 'Топливо'),
        ('tax', 'Транспортный налог'),
        ('other', 'Прочие расходы'),
    ]
    
    calculation = models.ForeignKey(
        OwnershipCalculation,
        on_delete=models.CASCADE,
        related_name='cost_items',
        verbose_name="Расчет"
    )
    
    category = models.CharField(
        max_length=20,
        verbose_name="Категория",
        choices=CATEGORY_CHOICES
    )
    
    year = models.IntegerField(
        verbose_name="Год владения",
        help_text="1, 2, 3..."
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма (руб)"
    )
    
    description = models.TextField(
        verbose_name="Описание",
        blank=True
    )
    
    class Meta:
        verbose_name = "Статья расходов"
        verbose_name_plural = "Статьи расходов"
        ordering = ['calculation', 'year', 'category']
    
    def __str__(self):
        return f"{self.get_category_display()} ({self.year} год): {self.amount} ₽"