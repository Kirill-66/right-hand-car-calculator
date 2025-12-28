from django import forms
from .models import OwnershipCalculation, RightHandCar

class CalculationForm(forms.ModelForm):
    """Форма для расчета стоимости владения"""
    
    # Поле для выбора автомобиля с группировкой по маркам
    car = forms.ModelChoiceField(
        queryset=RightHandCar.objects.all(),
        label="Выберите автомобиль",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = OwnershipCalculation
        fields = ['car', 'purchase_price_jpy', 'annual_mileage', 'ownership_years', 'region']
        widgets = {
            'purchase_price_jpy': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Пример: 500000'
            }),
            'annual_mileage': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Пример: 15000'
            }),
            'ownership_years': forms.Select(attrs={'class': 'form-control'}),
            'region': forms.Select(attrs={'class': 'form-control'}),
        }
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