# JDM Calculator
# О проекте
JDM Calculator — это веб-сервис для расчета полной стоимости владения праворульным автомобилем из Японии. Сервис позволяет точно рассчитать все расходы, связанные с покупкой и оформлением JDM (Japanese Domestic Market) автомобиля, включая таможенные пошлины, доставку, растаможку и дополнительные сборы.

# Основные функции
# Реализованные функции
Главная страница с информацией о сервисе
Быстрый расчет стоимости популярных моделей автомобилей
Валютный виджет с актуальными курсами JPY, USD, EUR, CNY
Каталог популярных моделей с техническими характеристиками
Адаптивный дизайн для мобильных устройств и десктопов
Автоматический пересчет цен в рубли по текущему курсу

# Популярные модели для расчета
Toyota Mark II JZX100 (1998, 2.5 л, 280 л.с.)
Nissan Skyline GT-R R34 (2001, 2.6 л, 320 л.с.)
Subaru Legacy B4 BL5 (2005, 2.0 л, 250 л.с.)
Mitsubishi Lancer Evolution VIII (2003, 2.0 л, 280 л.с.)

# Технологический стек
Backend
Python 3.x
Django 4.x
PostgreSQL (планируется)

Frontend
HTML5
CSS3
JavaScript (Vanilla)
Bootstrap 5
Bootstrap Icons

# Инфраструктура
Docker (планируется)
Nginx (планируется)
Gunicorn (планируется)

# Установка и запуск
Предварительные требования
Python 3.8 или выше
pip (менеджер пакетов Python)
Виртуальное окружение Python (рекомендуется)

# Шаг 1: Клонирование репозитория
git clone <ссылка-на-репозиторий>
cd jdm-calculator

# Шаг 2: Создание виртуального окружения
python -m venv venv

Активация на Windows:
venv\Scripts\activate

# Шаг 3: Установка зависимостей
pip install django==4.2
pip install psycopg2-binary

# Шаг 4: Настройка базы данных
Создание базы данных PostgreSQL:
CREATE DATABASE jdm_calculator;
CREATE USER jdm_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE jdm_calculator TO jdm_user;

Настройка подключения в settings.py:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'jdm_calculator',
        'USER': 'jdm_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Шаг 5: Применение миграций
python manage.py makemigrations calculator
python manage.py migrate

# Шаг 6: Создание суперпользователя
python manage.py createsuperuser

# Шаг 7: Запуск сервера разработки
python manage.py runserver

# Структура проекта
jdm-calculator/
├── calculator/          # Основное приложение
│   ├── migrations/     # Миграции базы данных
│   ├── static/         # Статические файлы
│   │   └── calculator/
│   │       ├── css/    # CSS файлы
│   │       ├── js/     # JavaScript файлы
│   │       └── img/    # Изображения
│   ├── templates/      # HTML шаблоны
│   │   └── calculator/
│   │       ├── base.html
│   │       └── home.html
│   ├── models.py       # Модели данных
│   ├── views.py        # Представления
│   ├── urls.py         # URL маршруты
│   └── admin.py        # Админ-панель
├── jdm_calculator/     # Настройки проекта
│   ├── settings.py     # Настройки
│   ├── urls.py         # Главные URL
│   └── wsgi.py         # WSGI конфигурация
├── manage.py           # Управляющий скрипт
├── requirements.txt    # Зависимости Python
├── README.md           # Документация
└── TZ.md              # Техническое задание