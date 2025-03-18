# Используем минимальный образ Python 3.11
FROM python:3.11.6-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем только requirements.txt для установки зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта в контейнер
COPY . .

# Добавляем `app` в PYTHONPATH (чтобы корректно работали импорты)
ENV PYTHONPATH="/app"

# Открываем порты для FastAPI (8000) и Streamlit (8501)
EXPOSE 8000 8501

# Запускаем и FastAPI, и Streamlit в одном контейнере
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 & streamlit run app/frontend.py --server.port 8501 --server.headless true"]