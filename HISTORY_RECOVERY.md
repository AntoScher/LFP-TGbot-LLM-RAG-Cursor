# Восстановление истории агента

Этот документ описывает различные способы восстановления истории диалогов с AI-агентом.

## Быстрый старт

```bash
# Запуск скрипта восстановления
python restore_history.py

# Или восстановление из JSON файла напрямую:
python -c "from restore_history import HistoryRestorer; HistoryRestorer().restore_from_json('example_history.json')"
```

## Источники данных для восстановления

### 1. JSON файлы

**Формат данных:**
```json
[
  {
    "user_id": 123456789,
    "query": "Вопрос пользователя",
    "response": "Ответ агента",
    "timestamp": "2024-01-01T12:00:00"
  }
]
```

**Использование:**
```python
from restore_history import HistoryRestorer
restorer = HistoryRestorer()
restorer.restore_from_json('path/to/history.json')
```

### 2. Экспорт Telegram

Для восстановления из экспорта Telegram Desktop:

1. Откройте Telegram Desktop
2. Перейдите в чат с ботом
3. Меню → Экспорт истории чата
4. Выберите формат JSON
5. Используйте полученный файл

**Использование:**
```python
restorer.restore_from_telegram_export('export.json', user_id=123456789)
```

### 3. Файлы логов

**Ожидаемый формат:**
```
[2024-01-01 12:00:00] USER 123456789: Какие у вас продукты?
[2024-01-01 12:00:05] BOT: У нас есть широкий ассортимент...
[2024-01-01 12:01:00] USER 123456789: Сколько это стоит?
[2024-01-01 12:01:05] BOT: Стоимость зависит от...
```

**Использование:**
```python
restorer.restore_from_logs('path/to/bot.log')
```

## Резервное копирование

### Создание резервной копии

```python
# Автоматическое имя файла
backup_file = restorer.backup_current_history()

# Пользовательское имя файла
backup_file = restorer.backup_current_history('my_backup.json')
```

### Восстановление из резервной копии

```python
restorer.restore_from_json('history_backup_20240115_123000.json')
```

## Управление историей

### Получение статистики

```python
stats = restorer.get_history_stats()
print(stats)
# Вывод:
# {
#   'total_conversations': 150,
#   'unique_users': 25,
#   'oldest_record': '2024-01-01T10:00:00',
#   'newest_record': '2024-01-15T18:30:00'
# }
```

### Очистка истории

```python
# ВНИМАНИЕ: Это удалит ВСЮ историю!
restorer.clear_history(confirm=True)
```

## Сценарии восстановления

### Сценарий 1: Потеря базы данных

1. Создайте новую базу данных (запустите бота один раз)
2. Восстановите из резервной копии JSON:
   ```bash
   python restore_history.py
   # Выберите опцию 1, укажите путь к файлу резервной копии
   ```

### Сценарий 2: Миграция с другого бота

1. Экспортируйте историю из Telegram
2. Используйте восстановление из экспорта:
   ```bash
   python restore_history.py
   # Выберите опцию 2, укажите файл экспорта и ID пользователя
   ```

### Сценарий 3: Восстановление из логов сервера

1. Найдите файлы логов с историей диалогов
2. Убедитесь, что формат соответствует ожидаемому
3. Восстановите:
   ```bash
   python restore_history.py
   # Выберите опцию 3, укажите путь к файлу логов
   ```

## Автоматизация

### Регулярное резервное копирование

Добавьте в crontab для ежедневного резервного копирования:

```bash
# Резервное копирование каждый день в 2:00
0 2 * * * cd /path/to/your/bot && python -c "from restore_history import HistoryRestorer; HistoryRestorer().backup_current_history()"
```

### Скрипт для автоматического восстановления

```bash
#!/bin/bash
# auto_restore.sh

BACKUP_DIR="/path/to/backups"
LATEST_BACKUP=$(ls -t $BACKUP_DIR/history_backup_*.json | head -1)

if [ -f "$LATEST_BACKUP" ]; then
    echo "Восстанавливаем из $LATEST_BACKUP"
    python -c "from restore_history import HistoryRestorer; HistoryRestorer().restore_from_json('$LATEST_BACKUP')"
else
    echo "Файлы резервных копий не найдены"
fi
```

## Устранение проблем

### Ошибка: "База данных заблокирована"

Остановите бота перед восстановлением:
```bash
pkill -f bot.py
python restore_history.py
```

### Ошибка: "Неверный формат JSON"

Проверьте структуру JSON файла:
```bash
python -m json.tool your_file.json
```

### Ошибка: "Превышен лимит символов"

История автоматически обрезается до 2000 символов для совместимости с SQLite.

### Дублирование записей

Скрипт не проверяет дубликаты. Перед восстановлением:
1. Создайте резервную копию текущей истории
2. Очистите базу данных
3. Восстановите из файла

## Примеры использования

### Пример 1: Простое восстановление

```python
from restore_history import HistoryRestorer

restorer = HistoryRestorer()
count = restorer.restore_from_json('example_history.json')
print(f"Восстановлено {count} записей")
```

### Пример 2: Полная миграция

```python
# Создаем резервную копию старой истории
old_backup = restorer.backup_current_history('old_history.json')

# Очищаем базу
restorer.clear_history(confirm=True)

# Восстанавливаем из нового источника
restorer.restore_from_json('new_history.json')

# Проверяем статистику
stats = restorer.get_history_stats()
print(f"Новая история содержит {stats['total_conversations']} диалогов")
```

## Безопасность

- Всегда создавайте резервные копии перед изменениями
- Храните резервные копии в безопасном месте
- Не передавайте файлы истории третьим лицам (могут содержать персональные данные)
- Регулярно проверяйте целостность данных

## Поддержка

При возникновении проблем:
1. Проверьте логи бота
2. Убедитесь в корректности формата входных файлов
3. Попробуйте восстановить небольшую порцию данных для тестирования