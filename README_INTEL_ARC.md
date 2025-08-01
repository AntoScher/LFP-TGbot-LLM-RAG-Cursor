# Intel Arc GPU Optimization Guide

## Обзор

Этот проект оптимизирован для работы с Intel Arc GPU с использованием Intel Extension for PyTorch (IPEX) и Intel Extension for Transformers (ITREX).

## Системные требования

### Аппаратные требования
- Intel Arc GPU (A3xx, A5xx, A7xx серии)
- Минимум 8GB системной памяти
- Рекомендуется 16GB+ для больших моделей

### Программные требования
- Windows 10/11 (64-bit)
- Python 3.11+
- Intel Arc Graphics Driver (последняя версия)
- Intel oneAPI Base Toolkit (опционально)

## Установка

### 1. Установка драйверов Intel Arc

1. Скачайте последние драйверы с [официального сайта Intel](https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-whql-windows.html)
2. Установите драйверы и перезагрузите систему
3. Убедитесь, что GPU определяется в Диспетчере устройств

### 2. Настройка окружения

```powershell
# Запустите скрипт настройки для Intel Arc
.\setup_intel_arc.ps1
```

Скрипт автоматически:
- Создаст новое conda окружение `lfp_bot_intel_arc`
- Установит Intel Extension for PyTorch
- Установит Intel Extension for Transformers
- Настроит переменные окружения

### 3. Активация окружения

```powershell
conda activate lfp_bot_intel_arc
```

### 4. Проверка установки

```powershell
python check_gpu.py
```

Успешная установка должна показать:
```
XPU available: True
IPEX XPU available: True
✅ Intel XPU is available and ready to use!
```

## Конфигурация

### Переменные окружения (.env)

```env
# Device configuration for Intel Arc
DEVICE=xpu
XPU_DEVICE_ID=0

# Intel XPU specific settings
INTEL_EXTENSION_FOR_PYTORCH_VERBOSE=1
SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS=1
```

### Оптимизации производительности

1. **Квантование моделей**: Автоматическое квантование до INT4 для экономии памяти
2. **Flash Attention**: Ускорение внимания в трансформерах
3. **Оптимизация памяти**: Эффективное использование VRAM

## Использование

### Базовое использование

```python
from intel_arc_optimization import setup_intel_environment, get_optimized_device

# Настройка окружения
setup_intel_environment()

# Получение оптимального устройства
device = get_optimized_device()  # Вернет "xpu" если доступен
```

### Загрузка модели с оптимизациями

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from intel_arc_optimization import get_model_config, optimize_model

# Конфигурация модели
config = get_model_config("Qwen/Qwen2-1.5B-Instruct")

# Загрузка модели
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2-1.5B-Instruct",
    **config
)

# Применение оптимизаций
model = optimize_model(model)
```

## Устранение неполадок

### Проблема: XPU не определяется

**Решение:**
1. Проверьте установку драйверов Intel Arc
2. Убедитесь, что GPU не используется другими приложениями
3. Перезагрузите систему

### Проблема: Ошибка импорта IPEX

**Решение:**
```powershell
conda activate lfp_bot_intel_arc
pip uninstall intel-extension-for-pytorch
pip install intel-extension-for-pytorch
```

### Проблема: Недостаточно памяти

**Решение:**
1. Уменьшите размер модели
2. Используйте квантование
3. Закройте другие приложения

## Производительность

### Ожидаемые улучшения

- **Скорость инференса**: 2-4x быстрее CPU
- **Эффективность памяти**: До 50% экономии VRAM
- **Параллельная обработка**: Поддержка batch processing

### Мониторинг производительности

```python
import torch
import time

# Измерение времени инференса
start_time = time.time()
output = model.generate(input_ids, max_length=100)
end_time = time.time()

print(f"Время генерации: {end_time - start_time:.2f} секунд")
```

## Дополнительные ресурсы

- [Intel Extension for PyTorch Documentation](https://intel.github.io/intel-extension-for-pytorch/)
- [Intel Extension for Transformers](https://github.com/intel/intel-extension-for-transformers)
- [Intel Arc GPU Support](https://www.intel.com/content/www/us/en/products/docs/discrete-gpus/arc/software.html) 