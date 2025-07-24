import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler
)
from flask_app import create_app, db
from flask_app.models import SessionLog
from embeddings import init_vector_store
from chains import init_qa_chain
import asyncio

# Загрузка конфигурации
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN not set in .env")

# Инициализация Flask приложения для работы с БД
flask_app = create_app()

# Глобальные переменные для кэширования ресурсов
retriever = None
qa_chain = None

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def initialize_resources():
    """Асинхронная инициализация ресурсов"""
    global retriever, qa_chain

    logger.info("Initializing vector store...")
    retriever = await asyncio.to_thread(init_vector_store)
    logger.info("Vector store initialized")

    logger.info("Initializing QA chain...")
    qa_chain = await asyncio.to_thread(init_qa_chain, retriever)
    logger.info("QA chain initialized")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я AI-ассистент отдела продаж. "
        "Задайте мне вопрос о наших продуктах или услугах."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Асинхронный обработчик сообщений"""
    if not qa_chain:
        await update.message.reply_text("Система инициализируется, попробуйте через 30 секунд...")
        return

    user_id = update.effective_user.id
    query = update.message.text.strip()

    # Валидация запроса
    if len(query) < 3:
        await update.message.reply_text("Пожалуйста, задайте более развернутый вопрос.")
        return

    if len(query) > 1000:
        await update.message.reply_text("Ваш запрос слишком длинный. Пожалуйста, ограничьтесь 1000 символами.")
        return

    try:
        # Логирование начала обработки
        logger.info(f"Processing query from {user_id}: {query[:50]}...")

        # Асинхронное выполнение запроса к LLM
        result = await asyncio.to_thread(qa_chain, {"query": query})
        answer = result["result"]

        # Обрезка слишком длинных ответов
        if len(answer) > 4000:
            answer = answer[:4000] + "\n\n[Ответ обрезан из-за ограничений Telegram]"

        # Сохранение в базу данных
        with flask_app.app_context():
            log = SessionLog(
                user_id=user_id,
                query=query,
                response=answer[:2000]  # Обрезаем для SQLite
            )
            db.session.add(log)
            db.session.commit()

        # Отправка ответа пользователю
        await update.message.reply_text(answer)

        # Логирование успешного завершения
        logger.info(f"Response sent to {user_id}")

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text(
            "Произошла ошибка при обработке вашего запроса. "
            "Попробуйте задать вопрос иначе или повторить позже."
        )


def main():
    # Создание и настройка приложения
    application = Application.builder().token(TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Инициализация ресурсов перед запуском
    application.run_polling(
        on_start=initialize_resources,
        poll_interval=0.5,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()