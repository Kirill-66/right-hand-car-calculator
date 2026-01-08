import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('calculator', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OwnershipCalculation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, 
                 serialize=False, verbose_name='ID')),
                ('purchase_price_jpy', models.IntegerField(default=500000, 
                 verbose_name='Цена в Японии (¥)')),
                ('purchase_year', models.IntegerField(default=2024, 
                 verbose_name='Год покупки')),
                ('annual_mileage', models.IntegerField(default=15000, 
                 verbose_name='Годовой пробег (км)')),
                ('ownership_years', models.IntegerField(choices=[
                    (1, '1 год'), (2, '2 года'), (3, '3 года'), 
                    (4, '4 года'), (5, '5 лет')], default=3, 
                    verbose_name='Срок владения')),
                ('region', models.CharField(choices=[
                    ('moscow', 'Москва'), ('spb', 'Санкт-Петербург'), 
                    ('vladivostok', 'Владивосток'), ('ekb', 'Екатеринбург'), 
                    ('other', 'Другой')], default='moscow', max_length=20, 
                    verbose_name='Регион')),
                ('created_at', models.DateTimeField(auto_now_add=True, 
                 verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, 
                 verbose_name='Дата обновления')),
                ('car', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, 
                 to='calculator.righthandcar', verbose_name='Автомобиль')),
                ('user', models.ForeignKey(blank=True, null=True, 
                 on_delete=django.db.models.deletion.CASCADE, 
                 to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Расчет владения',
                'verbose_name_plural': 'Расчеты владения',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CostItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, 
                 serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[
                    ('calculation', 'Растаможка/Утильсбор'),
                    ('adaptation', 'Адаптация под РФ'),
                    ('insurance', 'Страховка (ОСАГО/КАСКО)'),
                    ('maintenance', 'Техобслуживание'),
                    ('spare_parts', 'Запчасти'),
                    ('fuel', 'Топливо'),
                    ('tax', 'Транспортный налог'),
                    ('other', 'Прочие расходы')], max_length=20, 
                    verbose_name='Категория')),
                ('year', models.IntegerField(help_text='1, 2, 3...', 
                 verbose_name='Год владения')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, 
                 verbose_name='Сумма (руб)')),
                ('description', models.TextField(blank=True, 
                 verbose_name='Описание')),
                ('calculation', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='cost_items', 
                    to='calculator.ownershipcalculation', 
                    verbose_name='Расчет')),
            ],
            options={
                'verbose_name': 'Статья расходов',
                'verbose_name_plural': 'Статьи расходов',
                'ordering': ['calculation', 'year', 'category'],
            },
        ),
    ]