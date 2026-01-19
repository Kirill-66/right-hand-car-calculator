from django import forms
from datetime import datetime
from django.utils.safestring import mark_safe
from .models import OwnershipCalculation, RightHandCar


class CalculationForm(forms.ModelForm):
    """Форма для расчета стоимости владения праворульным автомобилем"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_year = datetime.now().year
        
        self.fields['purchase_year'].max_value = current_year
        self.fields['purchase_year'].initial = current_year
        
        self.fields['purchase_price_jpy'].help_text = mark_safe(
            'Средняя цена на аукционе в Японии<br>'
            '<small class="text-muted">1 ¥ ≈ 0.6 ₽ (примерный курс)</small>'
        )
        
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
        max_value=100000000,
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

class RightHandCarForm(forms.ModelForm):
    """Форма для добавления/редактирования автомобилей в базу данных"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['avg_price_jpy'].help_text = mark_safe(
            'Средняя цена на японских аукционах<br>'
            '<small class="text-muted">Пример: 500000 ¥ ≈ 300,000 ₽</small>'
        )
        
        self.fields['fuel_consumption'].help_text = 'Средний расход в смешанном цикле (л/100км)'
        
        self.fields['brand'].widget.attrs.update({
            'list': 'brand-list',
            'autocomplete': 'off'
        })
        
        self.fields['model'].widget.attrs.update({
            'list': 'model-list',
            'autocomplete': 'off'
        })
    
    BRAND_CHOICES = [
        ('toyota', 'Toyota'),
        ('nissan', 'Nissan'),
        ('subaru', 'Subaru'),
        ('mitsubishi', 'Mitsubishi'),
        ('honda', 'Honda'),
        ('mazda', 'Mazda'),
        ('suzuki', 'Suzuki'),
        ('daihatsu', 'Daihatsu'),
        ('isuzu', 'Isuzu'),
        ('lexus', 'Lexus'),
        ('infiniti', 'Infiniti'),
        ('acura', 'Acura'),
    ]
    
    TRANSMISSION_CHOICES = [
        ('manual', 'Механическая'),
        ('automatic', 'Автоматическая'),
        ('cvt', 'Вариатор'),
        ('dsg', 'Робот'),
    ]
    
    DRIVE_CHOICES = [
        ('fwd', 'Передний'),
        ('rwd', 'Задний'),
        ('awd', 'Полный'),
        ('4wd', '4WD'),
    ]
    
    brand = forms.ChoiceField(
        label="🏷️ Марка",
        choices=BRAND_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control-custom select',
            'id': 'id_brand'
        })
    )
    
    model = forms.CharField(
        label="🚘 Модель",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control-custom',
            'id': 'id_model',
            'placeholder': 'Например: Mark II, Skyline, Impreza'
        })
    )
    
    generation = forms.CharField(
        label="📐 Поколение",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control-custom',
            'placeholder': 'Например: JZX100, R34, GC8'
        })
    )
    
    year_from = forms.IntegerField(
        label="📅 Год от",
        min_value=1970,
        max_value=2024,
        widget=forms.NumberInput(attrs={
            'class': 'form-control-custom',
            'placeholder': '1998'
        })
    )
    
    year_to = forms.IntegerField(
        label="📅 Год до",
        min_value=1970,
        max_value=2024,
        widget=forms.NumberInput(attrs={
            'class': 'form-control-custom',
            'placeholder': '2004'
        })
    )
    
    engine_volume = forms.FloatField(
        label="⚙️ Объем двигателя (л)",
        min_value=0.5,
        max_value=8.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control-custom',
            'step': '0.1',
            'placeholder': '2.0'
        })
    )
    
    fuel_type = forms.ChoiceField(
        label="⛽ Тип топлива",
        choices=[
            ('petrol', 'Бензин'),
            ('diesel', 'Дизель'),
            ('hybrid', 'Гибрид'),
            ('electric', 'Электрический'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control-custom select'
        })
    )
    
    fuel_consumption = forms.FloatField(
        label="📊 Расход топлива (л/100км)",
        min_value=0,
        max_value=30,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control-custom',
            'step': '0.1',
            'placeholder': '10.5'
        })
    )
    
    power_hp = forms.IntegerField(
        label="💨 Мощность (л.с.)",
        min_value=0,
        max_value=1000,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control-custom',
            'placeholder': '280'
        })
    )
    
    transmission = forms.ChoiceField(
        label="🔧 Коробка передач",
        choices=TRANSMISSION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control-custom select'
        })
    )
    
    drive_type = forms.ChoiceField(
        label="🌀 Привод",
        choices=DRIVE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control-custom select'
        })
    )
    
    description = forms.CharField(
        label="📝 Описание",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control-custom',
            'rows': 4,
            'placeholder': 'Особенности модели, характерные проблемы, популярные модификации...'
        })
    )
    
    image = forms.ImageField(
        label="🖼️ Изображение",
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control-custom',
            'accept': 'image/*'
        })
    )
    
    avg_price_jpy = forms.IntegerField(
        label="💰 Средняя цена в Японии (¥)",
        min_value=0,
        max_value=20000000,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control-custom',
            'placeholder': '500000'
        })
    )
    
    class Meta:
        model = RightHandCar
        fields = [
            'brand', 'model', 'generation', 'year_from', 'year_to',
            'engine_volume', 'fuel_type', 'fuel_consumption',
            'power_hp', 'transmission', 'drive_type', 'description',
            'image', 'avg_price_jpy'
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        year_from = cleaned_data.get('year_from')
        year_to = cleaned_data.get('year_to')
        
        if year_from and year_to:
            if year_from > year_to:
                self.add_error('year_to', 'Год окончания не может быть раньше года начала')
            
            if (year_to - year_from) > 30:
                self.add_error('year_to', 'Слишком большой диапазон лет производства')
        
        engine_volume = cleaned_data.get('engine_volume')
        fuel_consumption = cleaned_data.get('fuel_consumption')
        
        if engine_volume and not fuel_consumption:
            if engine_volume <= 1.6:
                cleaned_data['fuel_consumption'] = 8.0
            elif engine_volume <= 2.5:
                cleaned_data['fuel_consumption'] = 11.0
            else:
                cleaned_data['fuel_consumption'] = 15.0
        
        power_hp = cleaned_data.get('power_hp')
        if engine_volume and not power_hp:
            cleaned_data['power_hp'] = int(engine_volume * 120)
        
        return cleaned_data
    
class ImportCarsForm(forms.Form):
    csv_file = forms.FileField(
        label="CSV файл",
        help_text="Файл должен содержать колонки: brand,model,generation,year_from,year_to,engine_volume,fuel_type",
        widget=forms.FileInput(attrs={
            'accept': '.csv,.txt',
            'class': 'form-control'
        })
    )
    
    update_existing = forms.BooleanField(
        label="Обновить существующие записи",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            raise forms.ValidationError("Файл должен быть в формате CSV")
        
        return csv_file