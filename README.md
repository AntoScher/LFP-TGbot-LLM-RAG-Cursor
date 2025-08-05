# LFP-TGbot-LLM-RAG

Telegram-бот с RAG-архитектурой для ответов на вопросы с использованием:
- Векторного хранилища ChromaDB
- Моделей эмбеддингов HuggingFace
- LangChain для работы с цепочками

## 📋 Требования

- Python 3.11 (рекомендуется)
- Miniconda/Anaconda для управления окружением
- Телеграм-бот токен

## 🚀 Быстрый старт

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/LFP-TGbot-LLM-RAG.git
cd LFP-TGbot-LLM-RAG
```

2. Создайте и активируйте conda окружение:
```bash
conda create -n lfp_bot_py311 python=3.11
conda activate lfp_bot_py311
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте переменные окружения:
Создайте файл `.env` на основе `.env.example` и укажите ваш токен бота:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
```

5. Запустите бота:
```bash
.\start_bot.ps1
```

## 🛠 Технические детали

### Основные компоненты

- `bot.py` - основной файл с логикой бота
- `embeddings.py` - работа с эмбеддингами и векторным хранилищем
- `chains.py` - цепочки LangChain для обработки запросов
- `start_bot.ps1` - скрипт для запуска бота в Windows

## 🔧 Устранение неполадок

### Очистка базы данных ChromaDB
Если возникли проблемы с векторным хранилищем, можно удалить папку `chroma_db` и перезапустить бота.

### Обновление зависимостей
Текущие версии зависимостей зафиксированы в `requirements.txt`. Для обновления можно использовать:
```bash
pip freeze > requirements.txt
```

## 📝 Лицензия

MIT
