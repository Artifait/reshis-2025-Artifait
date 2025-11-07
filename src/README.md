# Электронный дневник

## Архитектура

Проект построен по принципам **Clean Architecture** с четким разделением на слои:

```
src/
├── domain/                    # Domain Layer (Entities, Use Cases)
│   ├── entities/             # Бизнес-сущности
│   ├── use_cases/           # Сценарии использования
│   └── repositories/        # Интерфейсы репозиториев
├── infrastructure/          # Infrastructure Layer
│   ├── database/           # Реализация базы данных
│   ├── repositories/       # Реализация репозиториев
│   └── external/           # Внешние сервисы
├── application/            # Application Layer
│   ├── services/          # Сервисы приложения
│   └── dto/              # Data Transfer Objects
├── presentation/          # Presentation Layer
│   ├── web/              # Web контроллеры
│   └── templates/        # Шаблоны
└── config/               # Конфигурация
```

## Функциональность

- **Учет оценок** - ведение журнала оценок по всем предметам с комментариями
- **Учет посещаемости** - отметка присутствия учащихся на уроках
- **Расписание** - просмотр расписания уроков по дням недели
- **Отчеты** - аналитические отчеты для родителей и учителей

## Установка и запуск

1. **Активация виртуального окружения:**
```bash
source venv/bin/activate
```

2. **Установка зависимостей:**
```bash
pip install -r requirements.txt
```

3. **Инициализация базы данных:**
```bash
python init_data.py
```

4. **Запуск приложения:**
```bash
python run.py
```

5. **Откройте браузер и перейдите по адресу:** http://localhost:5001

## Система авторизации

Приложение поддерживает ролевую модель с разными уровнями доступа:

### Роли пользователей:
- **Школьник** - видит только свои оценки и расписание
- **Родитель** - видит данные своих детей
- **Учитель** - может выставлять оценки и отмечать посещаемость
- **Администратор** - полный доступ ко всем функциям

### Тестовые учетные данные:
- **Администратор:** admin / admin123
- **Учитель:** teacher1 / teacher123  
- **Родитель:** parent1 / parent123
- **Школьники:**
  - student1 / student123 (Иван Петров)
  - student2 / student123 (Мария Сидорова)
  - student3 / student123 (Алексей Козлов)
  - student4 / student123 (Елена Морозова)

## Структура проекта

```
reshis/
├── run.py                    # Точка входа в приложение
├── init_data.py             # Инициализация данных
├── seed.json                # Тестовые данные
├── domain/                  # Domain Layer
│   ├── entities/           # Бизнес-сущности
│   └── repositories/       # Интерфейсы репозиториев
├── infrastructure/         # Infrastructure Layer
│   ├── database/          # База данных SQLite
│   └── repositories/      # Реализация репозиториев
├── application/           # Application Layer
│   └── services/         # Сервисы приложения
├── presentation/         # Presentation Layer
│   ├── web/             # Web контроллеры
│   └── templates/       # HTML шаблоны
├── static/              # Статические файлы
├── requirements.txt     # Зависимости Python
└── instance/diary.db   # База данных SQLite
```

## Технологии

- **Backend**: Flask, SQLite3
- **Frontend**: HTML5, CSS3
- **База данных**: SQLite
- **Стили**: CSS Grid, Flexbox, градиенты
