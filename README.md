# JDM Calculator (Right-Hand Car Calculator)

## О проекте
JDM Calculator — веб-сервис для расчета полной стоимости владения праворульным автомобилем из Японии. **Актуальное название проекта: Right-Hand Car Calculator**.

## Технологический стек
### Backend
- Python 3.x
- Django 4.2.11
- MySQL (используется в текущей версии)

### Frontend
- HTML5, CSS3, JavaScript
- Bootstrap 5
- Chart.js (для визуализации расходов)

### База данных
- MySQL (текущая реализация)
- PostgreSQL (планируется в будущих версиях)

## Установка и запуск

### Требования
- Python 3.8+
- MySQL Server
- Git

### Шаги установки
1. **Клонирование репозитория**
   ```bash
   git clone https://github.com/ваш-аккаунт/right-hand-car-calculator.git
   cd right-hand-car-calculator

Настройка виртуального окружения
bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

Установка зависимостей
bash
pip install -r requirements.txt

Настройка базы данных MySQL
sql
CREATE DATABASE car_calculator;
CREATE USER 'jdm_user'@'localhost' IDENTIFIED BY 'ваш_пароль';
GRANT ALL PRIVILEGES ON car_calculator.* TO 'jdm_user'@'localhost';
FLUSH PRIVILEGES;

Настройка переменных окружения
Создайте файл .env на основе .env.example:
env
SECRET_KEY=ваш-секретный-ключ
DEBUG=False
DB_NAME=car_calculator
DB_USER=jdm_user
DB_PASSWORD=ваш_пароль
DB_HOST=localhost
DB_PORT=3306

Применение миграций
bash
python manage.py migrate

Запуск сервера

bash
python manage.py runserver

Доступ к сайту
Откройте в браузере: http://localhost:8000

Структура проекта
text
right-hand-car-calculator/
├── calculator/          # Основное Django-приложение
│   ├── migrations/     # Миграции базы данных
│   ├── static/         # Статические файлы (CSS, JS, изображения)
│   ├── templates/      # HTML шаблоны
│   ├── models.py       # Модели данных (Car, Calculation, User)
│   ├── views.py        # Контроллеры
│   ├── urls.py         # Маршруты приложения
│   └── admin.py        # Админ-панель Django
├── carcost/            # Настройки проекта Django
│   ├── settings.py     # Конфигурация
│   ├── urls.py         # Главные URL-маршруты
│   └── wsgi.py         # WSGI конфигурация
├── static/             # Глобальные статические файлы
├── media/              # Загружаемые файлы (в .gitignore)
├── .env.example        # Шаблон переменных окружения
├── requirements.txt    # Зависимости Python
├── manage.py           # Управляющий скрипт Django
├── README.md           # Эта документация
└── TZ.md              # Техническое задание

Функциональность
Реализовано
Главная страница с информацией о сервисе

Калькулятор стоимости владения автомобилем

Визуализация расходов (диаграммы Chart.js)

База автомобилей с характеристиками

Расчет таможенных пошлин, доставки, страховки

Адаптивный дизайн для мобильных устройств

Планы по доработке
Экспорт расчетов в PDF

Сравнение нескольких автомобилей

Уведомления об изменениях курсов валют

Мобильное приложение

Лицензия
Проект распространяется под лицензией MIT. Подробнее см. в файле LICENSE.