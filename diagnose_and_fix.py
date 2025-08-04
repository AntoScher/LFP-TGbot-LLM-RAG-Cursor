#!/usr/bin/env python3
"""
Скрипт диагностики и исправления проблем для Telegram бота с Intel Arc
"""

import os
import sys
import logging
import subprocess
import shutil
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_python_version():
    """Проверка версии Python"""
    version = sys.version_info
    logger.info(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3 or version.minor < 11:
        logger.error("Требуется Python 3.11 или выше")
        return False
    
    logger.info("✓ Python version is compatible")
    return True

def check_conda_environment():
    """Проверка conda окружения"""
    conda_env = os.getenv('CONDA_DEFAULT_ENV')
    if conda_env:
        logger.info(f"✓ Conda environment: {conda_env}")
        return True
    else:
        logger.warning("Conda environment not detected")
        return False

def check_intel_arc_support():
    """Проверка поддержки Intel Arc"""
    try:
        import torch
        logger.info(f"PyTorch version: {torch.__version__}")
        
        # Проверка XPU
        if hasattr(torch, 'xpu') and torch.xpu.is_available():
            device_name = torch.xpu.get_device_name(0)
            logger.info(f"✓ Intel XPU available: {device_name}")
            return True
        else:
            logger.info("Intel XPU not available, will use CPU")
            return False
            
    except ImportError:
        logger.error("PyTorch not installed")
        return False

def check_dependencies():
    """Проверка установленных зависимостей"""
    required_packages = [
        'torch', 'transformers', 'langchain', 'chromadb',
        'sentence-transformers', 'flask', 'python-telegram-bot'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✓ {package} installed")
        except ImportError:
            logger.error(f"✗ {package} not installed")
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        return False
    
    return True

def check_chroma_db():
    """Проверка базы данных ChromaDB"""
    chroma_dir = Path("./chroma_db")
    
    if not chroma_dir.exists():
        logger.warning("ChromaDB directory not found")
        return False
    
    try:
        from langchain_chroma import Chroma
        from langchain_huggingface import HuggingFaceEmbeddings
        
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"}
        )
        
        vectordb = Chroma(
            persist_directory=str(chroma_dir),
            embedding_function=embeddings
        )
        
        collection = vectordb._collection
        if collection:
            count = collection.count()
            logger.info(f"✓ ChromaDB loaded successfully with {count} documents")
            return True
        else:
            logger.error("ChromaDB collection is empty or corrupted")
            return False
            
    except Exception as e:
        logger.error(f"Error checking ChromaDB: {e}")
        return False

def check_knowledge_base():
    """Проверка базы знаний"""
    knowledge_dir = Path("./knowledge_base")
    
    if not knowledge_dir.exists():
        logger.error("Knowledge base directory not found")
        return False
    
    # Проверяем наличие файлов
    md_files = list(knowledge_dir.glob('*.md'))
    if not md_files:
        logger.error("No markdown files found in knowledge base")
        return False
    
    logger.info(f"✓ Found {len(md_files)} markdown files in knowledge base")
    
    # Проверяем системный промпт
    system_prompt = Path("./system_prompt.txt")
    if not system_prompt.exists():
        logger.warning("System prompt not found in root directory")
        return False
    
    logger.info("✓ System prompt found")
    return True

def fix_chroma_db():
    """Исправление базы данных ChromaDB"""
    logger.info("Attempting to fix ChromaDB...")
    
    try:
        # Удаляем старую базу
        chroma_dir = Path("./chroma_db")
        if chroma_dir.exists():
            shutil.rmtree(chroma_dir)
            logger.info("Removed old ChromaDB")
        
        # Перезагружаем базу знаний
        subprocess.run([sys.executable, "load_knowledge_base_fixed.py"], check=True)
        logger.info("✓ ChromaDB fixed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error fixing ChromaDB: {e}")
        return False

def install_missing_packages():
    """Установка недостающих пакетов"""
    logger.info("Installing missing packages...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements_fixed.txt"
        ], check=True)
        logger.info("✓ Packages installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing packages: {e}")
        return False

def create_backup():
    """Создание резервной копии"""
    backup_dir = Path("./backup")
    backup_dir.mkdir(exist_ok=True)
    
    # Копируем важные файлы
    important_files = [
        "bot.py", "embeddings.py", "chains.py", "load_knowledge_base.py"
    ]
    
    for file_name in important_files:
        file_path = Path(file_name)
        if file_path.exists():
            shutil.copy2(file_path, backup_dir / f"{file_name}.backup")
    
    logger.info("✓ Backup created")

def main():
    """Основная функция диагностики"""
    logger.info("=== Диагностика Telegram бота с Intel Arc ===")
    
    # Создаем резервную копию
    create_backup()
    
    # Проверки
    checks = [
        ("Python version", check_python_version),
        ("Conda environment", check_conda_environment),
        ("Intel Arc support", check_intel_arc_support),
        ("Dependencies", check_dependencies),
        ("Knowledge base", check_knowledge_base),
        ("ChromaDB", check_chroma_db),
    ]
    
    failed_checks = []
    
    for check_name, check_func in checks:
        logger.info(f"\n--- Checking {check_name} ---")
        if not check_func():
            failed_checks.append(check_name)
    
    # Исправления
    if failed_checks:
        logger.info(f"\n=== Исправление проблем ===")
        
        if "Dependencies" in failed_checks:
            install_missing_packages()
        
        if "ChromaDB" in failed_checks:
            fix_chroma_db()
        
        # Повторная проверка
        logger.info("\n=== Повторная проверка ===")
        for check_name, check_func in checks:
            if check_name in failed_checks:
                logger.info(f"\n--- Re-checking {check_name} ---")
                check_func()
    
    logger.info("\n=== Диагностика завершена ===")
    
    if not failed_checks:
        logger.info("✓ Все проверки пройдены успешно!")
        logger.info("Бот готов к запуску")
    else:
        logger.warning(f"⚠️ Проблемы найдены: {', '.join(failed_checks)}")
        logger.info("Попробуйте запустить бот после исправления проблем")

if __name__ == "__main__":
    main() 