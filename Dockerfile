FROM python:3.11-slim

# Установим системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Настраиваем виртуальное окружение
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Копируем приложение
WORKDIR /app
COPY . /app

# Устанавливаем зависимости
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Запуск
CMD ["python", "chatGpt.py"]
