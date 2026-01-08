from django import forms
from datetime import datetime
from django.utils.safestring import mark_safe
from .models import OwnershipCalculation, RightHandCar


class CalculationForm(forms.ModelForm):
    """Форма для расчета стоимости владения праворульным автомобилем"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_year = datetime.now().year
        
        # Динамически обновляем год покупки
        self.fields['purchase_year'].max_value = current_year
        self.fields['purchase_year'].initial = current_year
        
        # Добавляем курс валют в подсказку
        self.fields['purchase_price_jpy'].help_text = mark_safe(
            'Средняя цена на аукционе в Японии<br>'
            '<small class="text-muted">1 ¥ ≈ 0.6 ₽ (примерный курс)</small>'
        )
        
        # Оптимизируем запрос для выбора автомобиля
        self.fields['car'].queryset = RightHandCar.objects.all().order_by('brand', 'model')
    
    car = forms.ModelChoiceField(
        queryset=RightHandCar.objects.none(),
        label="🚗 Автомобиль",
        empty_label="-- Выберите модель --",
        widget=forms.Select(attrs={
            'class': 'form-control-custom select',
            'id': 'id_car',
            'data-placeholder': 'Начните вводить название...'
        })
    )
    
    purchase_price_jpy = forms.IntegerField(
        label="💰 Цена в Японии",
        min_value=100000,
        max_value=10000000,
        initial=500000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control-custom',
            'id': 'id_purchase_price_jpy',
            'placeholder': '500000',
            'step': '10000'
        })
    )
    
    purchase_year = forms.IntegerField(
        label="📅 Год покупки",
        min_value=1990,
        max_value=2024,
        initial=2024,
        widget=forms.NumberInput(attrs={
            'class': 'form-control-custom',
            'id': 'id_purchase_year',
            'placeholder': '2024',
            'min': '1990'
        })
    )
    
    annual_mileage = forms.IntegerField(
        label="🛣️ Годовой пробег",
        min_value=1000,
        max_value=100000,
        initial=15000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control-custom',
            'id': 'id_annual_mileage',
            'placeholder': '15000',
            'step': '1000'
        })
    )
    
    OWNERSHIP_CHOICES = [
        (1, '1 год'),
        (2, '2 года'),
        (3, '3 года'),
        (4, '4 года'),
        (5, '5 лет'),
    ]
    
    ownership_years = forms.ChoiceField(
        label="📅 Срок владения",
        choices=OWNERSHIP_CHOICES,
        initial=3,
        widget=forms.Select(attrs={
            'class': 'form-control-custom select',
            'id': 'id_ownership_years'
        })
    )
    
    REGION_CHOICES = [
        ('moscow', '🏛️ Москва'),
        ('spb', '🌉 Санкт-Петербург'),
        ('vladivostok', '⛴️ Владивосток'),
        ('ekb', '🏔️ Екатеринбург'),
        ('other', '📍 Другой регион'),
    ]
    
    region = forms.ChoiceField(
        label="🗺️ Регион",
        choices=REGION_CHOICES,
        initial='moscow',
        widget=forms.Select(attrs={
            'class': 'form-control-custom select',
            'id': 'id_region'
        })
    )
    
    class Meta:
        model = OwnershipCalculation
        fields = [
            'car',
            'purchase_price_jpy',
            'purchase_year',
            'annual_mileage',
            'ownership_years',
            'region'
        ]
        
        labels = {
            'purchase_price_jpy': 'Цена в Японии (¥)',
            'purchase_year': 'Год покупки',
            'annual_mileage': 'Годовой пробег (км)',
            'ownership_years': 'Срок владения',
            'region': 'Регион',
        }
        
        help_texts = {
            'purchase_price_jpy': 'Средняя цена на аукционе в Японии',
            'annual_mileage': 'Сколько примерно проезжаете за год',
            'purchase_year': 'Планируемый год покупки',
        }
    
    def clean_purchase_price_jpy(self):
        """Валидация цены автомобиля"""
        price = self.cleaned_data.get('purchase_price_jpy')
        if price < 100000:
            raise forms.ValidationError(
                "Цена слишком низкая. Минимальная цена 100,000 ¥"
            )
        if price > 10000000:
            raise forms.ValidationError(
                "Цена слишком высокая. Максимальная цена 10,000,000 ¥"
            )
        return price
    
    def clean_annual_mileage(self):
        """Валидация годового пробега"""
        mileage = self.cleaned_data.get('annual_mileage')
        if mileage < 1000:
            raise forms.ValidationError(
                "Пробег слишком маленький. Минимум 1,000 км в год"
            )
        if mileage > 100000:
            raise forms.ValidationError(
                "Пробег слишком большой. Максимум 100,000 км в год"
            )
        return mileage
    
    def clean_purchase_year(self):
        """Валидация года покупки"""
        year = self.cleaned_data.get('purchase_year')
        current_year = datetime.now().year
        
        if year < 1990:
            raise forms.ValidationError(
                "Год покупки не может быть раньше 1990"
            )
        if year > current_year + 2:
            raise forms.ValidationError(
                f"Год покупки не может быть позже {current_year + 2}"
            )
        return year
    
    def clean(self):
        """Комплексная валидация всей формы"""
        cleaned_data = super().clean()
        purchase_year = cleaned_data.get('purchase_year')
        car = cleaned_data.get('car')
        
        # Проверка совместимости года покупки и года выпуска автомобиля
        if car and purchase_year:
            if purchase_year < car.year_from:
                self.add_error(
                    'purchase_year',
                    f"Год покупки ({purchase_year}) раньше начала выпуска этой модели ({car.year_from})"
                )
            if purchase_year > car.year_to:
                self.add_error(
                    'purchase_year',
                    f"Год покупки ({purchase_year}) позже окончания выпуска этой модели ({car.year_to})"
                )
        
        return cleaned_data


class CarFilterForm(forms.Form):
    """Форма для фильтрации автомобилей в каталоге"""
    
    BRAND_CHOICES = [
        ('', 'Все марки'),
        ('toyota', 'Toyota'),
        ('nissan', 'Nissan'),
        ('subaru', 'Subaru'),
        ('mitsubishi', 'Mitsubishi'),
        ('honda', 'Honda'),
    ]
    
    FUEL_CHOICES = [
        ('', 'Все типы'),
        ('petrol', 'Бензин'),
        ('diesel', 'Дизель'),
    ]
    
    brand = forms.ChoiceField(
        label="Марка",
        choices=BRAND_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'filter-brand'
        })
    )
    
    fuel_type = forms.ChoiceField(
        label="Тип топлива",
        choices=FUEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'filter-fuel'
        })
    )
    
    year_from = forms.IntegerField(
        label="Год от",
        min_value=1990,
        max_value=2024,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1990',
            'id': 'filter-year-from'
        })
    )
    
    year_to = forms.IntegerField(
        label="Год до",
        min_value=1990,
        max_value=2024,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '2024',
            'id': 'filter-year-to'
        })
    )
    
    def clean_year_from(self):
        year_from = self.cleaned_data.get('year_from')
        if year_from and year_from < 1990:
            raise forms.ValidationError("Год не может быть раньше 1990")
        return year_from
    
    def clean_year_to(self):
        year_to = self.cleaned_data.get('year_to')
        if year_to and year_to > 2024:
            raise forms.ValidationError("Год не может быть позже 2024")
        return year_to
    
    def clean(self):
        cleaned_data = super().clean()
        year_from = cleaned_data.get('year_from')
        year_to = cleaned_data.get('year_to')
        
        if year_from and year_to and year_from > year_to:
            self.add_error(
                'year_to',
                '"Год до" не может быть меньше "Год от"'
            )
        
        return cleaned_data