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