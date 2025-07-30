# Используем базовый образ с Python 3.11
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем pip и обновляем его
RUN pip install --upgrade pip setuptools wheel

# Сначала устанавливаем numpy отдельно
RUN pip install --no-cache-dir numpy==1.24.3

# Устанавливаем CPU-версию PyTorch
RUN pip install --no-cache-dir \
    torch==2.0.1 \
    torchvision \
    torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

# Копируем зависимости
WORKDIR /app
COPY requirements.txt .

# Устанавливаем оставшиеся зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем совместимые версии SQLAlchemy и Flask-SQLAlchemy
RUN pip install --no-cache-dir \
    SQLAlchemy==1.4.46 \
    Flask-SQLAlchemy==2.5.1

# Копируем исходный код
COPY . .

# Переменные окружения для CPU
ENV DEVICE=cpu
ENV CACHE_DIR=/tmp/huggingface
ENV PYTHONUNBUFFERED=1

# Создаем директорию для кэша
RUN mkdir -p ${CACHE_DIR} && chmod 777 ${CACHE_DIR}

# Запускаем бота
CMD ["python", "bot.py"]
