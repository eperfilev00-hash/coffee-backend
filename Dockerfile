FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Копируем зависимости отдельно (кэш слоя)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Даём права на запуск скрипту
RUN chmod +x /app/entrypoint.sh

ENV PYTHONPATH=/app

EXPOSE 8000

# Теперь запускаем не uvicorn напрямую, а наш скрипт
CMD ["/app/entrypoint.sh"]