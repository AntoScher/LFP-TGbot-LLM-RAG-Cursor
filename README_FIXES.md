# Руководство по исправлению проблем Telegram бота с Intel Arc

## Анализ проблем

Ваш проект имеет несколько критических проблем, которые мешают работе ChromaDB и оптимизации для Intel Arc:

### 1. **Проблемы с зависимостями**
- Устаревшие импорты LangChain (deprecated warnings)
- Несовместимые версии пакетов
- Отсутствие специализированных пакетов для Intel Arc

### 2. **Проблемы с ChromaDB**
- База данных была пустой (0 документов)
- Проблемы с инициализацией векторного хранилища
- Неправильные импорты

### 3. **Проблемы с Intel Arc оптимизацией**
- Сложная логика инициализации
- Отсутствие четкого разделения CPU/GPU режимов
- Проблемы с совместимостью

## Решения

### Шаг 1: Обновление зависимостей

1. **Создайте резервную копию текущего окружения:**
```bash
conda create -n bot_backup --clone base
```

2. **Установите обновленные зависимости:**
```bash
pip install -r requirements_fixed.txt
```

### Шаг 2: Исправление структуры проекта

1. **Системный промпт перемещен в корневую директорию:**
   - `system_prompt.txt` теперь в корне проекта
   - Упрощена структура файлов

2. **Обновленные файлы с исправленными импортами:**
   - `embeddings_fixed.py` - исправленные импорты LangChain
   - `chains_fixed.py` - упрощенная логика Intel Arc
   - `bot_fixed.py` - обновленный бот с fallback импортами
   - `load_knowledge_base_fixed.py` - исправленная загрузка БЗ

### Шаг 3: Диагностика и исправление

Запустите скрипт диагностики:
```bash
python diagnose_and_fix.py
```

Этот скрипт:
- Проверит все компоненты системы
- Автоматически исправит проблемы с ChromaDB
- Установит недостающие пакеты
- Создаст резервные копии

### Шаг 4: Перезагрузка базы знаний

```bash
python load_knowledge_base_fixed.py
```

### Шаг 5: Запуск исправленного бота

```bash
python bot_fixed.py
```

## Оптимизации для Intel Core Ultra 7 155H

### Настройки окружения

Создайте файл `.env` с настройками:

```env
# Telegram Bot
TELEGRAM_TOKEN=your_telegram_token
HUGGINGFACEHUB_API_TOKEN=your_hf_token
ADMIN_TELEGRAM_ID=your_admin_id

# Device configuration
DEVICE=cpu  # или xpu для Intel Arc
MODEL_NAME=Qwen/Qwen2-1.5B-Instruct

# Performance settings
TOKENIZERS_PARALLELISM=false
CUDA_VISIBLE_DEVICES=
```

### Рекомендации по производительности

1. **Для CPU режима (рекомендуется для стабильности):**
   ```env
   DEVICE=cpu
   ```

2. **Для Intel Arc GPU (экспериментально):**
   ```env
   DEVICE=xpu
   ```

3. **Оптимизация памяти:**
   - Используйте модели размером до 1.5B параметров
   - Включите `low_cpu_mem_usage=True`
   - Используйте `torch.float16` для GPU

## Структура исправленного проекта

```
LFP-TGbot-LLM-RAG-Cursor/
├── system_prompt.txt          # Системный промпт (перемещен в корень)
├── requirements_fixed.txt     # Обновленные зависимости
├── embeddings_fixed.py        # Исправленные эмбеддинги
├── chains_fixed.py           # Исправленные цепи
├── bot_fixed.py              # Исправленный бот
├── load_knowledge_base_fixed.py  # Исправленная загрузка БЗ
├── diagnose_and_fix.py       # Скрипт диагностики
├── knowledge_base/           # База знаний (только .md файлы)
│   ├── product_catalog.md
│   ├── delivery_terms.md
│   └── knowledge_base.md
└── chroma_db/               # Векторная база данных
```

## Проверка работоспособности

1. **Проверка ChromaDB:**
```bash
python check_chroma_db.py
```

2. **Проверка эмбеддингов:**
```bash
python check_encodings.py
```

3. **Тест извлечения:**
```bash
python test_retrieval.py
```

## Устранение неполадок

### Проблема: "ChromaDB collection is empty"
**Решение:** Запустите `python load_knowledge_base_fixed.py`

### Проблема: "Intel XPU not available"
**Решение:** Установите `DEVICE=cpu` в `.env` файле

### Проблема: "ImportError: langchain_community"
**Решение:** Установите `pip install langchain-community==0.2.0`

### Проблема: "Vector store initialization failed"
**Решение:** Запустите `python diagnose_and_fix.py`

## Мониторинг и логи

- Логи бота: `bot.log`
- Логи диагностики: вывод в консоль
- База данных сессий: `instance/` (SQLite)

## Производительность

### Ожидаемые результаты на Intel Core Ultra 7 155H:

- **CPU режим:** 2-5 секунд на запрос
- **Intel Arc режим:** 1-3 секунды на запрос (экспериментально)
- **Память:** ~4-6 GB RAM
- **ChromaDB:** ~100-500 MB на диске

## Дополнительные рекомендации

1. **Регулярное обновление базы знаний:**
   - Запускайте `load_knowledge_base_fixed.py` при изменении файлов
   - Проверяйте целостность ChromaDB

2. **Мониторинг производительности:**
   - Следите за использованием памяти
   - Проверяйте логи на ошибки
   - Мониторьте время ответа бота

3. **Резервное копирование:**
   - Регулярно создавайте резервные копии `chroma_db/`
   - Сохраняйте конфигурационные файлы

## Контакты для поддержки

При возникновении проблем:
1. Запустите `python diagnose_and_fix.py`
2. Проверьте логи в `bot.log`
3. Убедитесь в корректности `.env` файла
4. Проверьте доступность всех зависимостей 