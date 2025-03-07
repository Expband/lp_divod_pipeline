# Використовуємо офіційний Python 3.10 image як базовий
FROM python:3.10

# Встановлюємо робочу директорію всередині контейнера
WORKDIR /app

# Копіюємо файли залежностей
COPY requirements.txt .

# Встановлюємо залежності
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо всі файли проекту в контейнер
COPY . .

# Визначаємо змінні середовища
ENV PYTHONUNBUFFERED=1

# Запускаємо додаток за допомогою Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
