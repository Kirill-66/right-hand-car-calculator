from django import forms
from .models import OwnershipCalculation, RightHandCar

class CalculationForm(forms.ModelForm):
    """Форма для расчета стоимости владения"""
    
    # Автомобиль с кастомным виджетом
    car = forms.ModelChoiceField(
        queryset=RightHandCar.objects.all(),
        label="Выберите автомобиль",
        widget=forms.Select(attrs={
            'class': 'form-control-custom select',
            'placeholder': '-- Выберите модель --'
        })
    )
    
    # Цена в Японии
    purchase_price_jpy = forms.IntegerField(
        label="Цена в Японии (¥)",
        min_value=100000,
        max_value=5000000,
        initial=500000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control-custom',
            'placeholder': '500000'
        })
    )
    
    # Годовой пробег
    annual_mileage = forms.IntegerField(
        label="Годовой пробег (км)",
        min_value=5000,
        max_value=50000,
        initial=15000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control-custom',
            'placeholder': '15000'
        })
    )
    
    # Срок владения
    OWNERSHIP_CHOICES = [
        (1, '1 год'),
        (2, '2 года'),
        (3, '3 года'),
        (4, '4 года'),
        (5, '5 лет'),
    ]
    
    ownership_years = forms.ChoiceField(
        label="Срок владения",
        choices=OWNERSHIP_CHOICES,
        initial=3,
        widget=forms.Select(attrs={
            'class': 'form-control-custom select'
        })
    )
    
    # Регион
    REGION_CHOICES = [
        ('moscow', 'Москва'),
        ('spb', 'Санкт-Петербург'),
        ('vladivostok', 'Владивосток'),
        ('ekb', 'Екатеринбург'),
        ('other', 'Другой регион'),
    ]
    
    region = forms.ChoiceField(
        label="Ваш регион",
        choices=REGION_CHOICES,
        initial='moscow',
        widget=forms.Select(attrs={
            'class': 'form-control-custom select'
        })
    )
    
    class Meta:
        model = OwnershipCalculation
        fields = ['car', 'purchase_price_jpy', 'annual_mileage', 'ownership_years', 'region']
        
        # Удаляем дублирующиеся виджеты, т.к. переопределили поля
        widgets = {}
        
        labels = {
            'purchase_price_jpy': 'Цена в Японии (иены)',
            'annual_mileage': 'Годовой пробег (км)',
            'ownership_years': 'Срок владения',
            'region': 'Ваш регион',
        }
        
        help_texts = {
            'purchase_price_jpy': 'Средняя цена на аукционе в Японии',
            'annual_mileage': 'Сколько примерно проезжаете за год',
        }