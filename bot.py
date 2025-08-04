import os
import logging
import traceback
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler
)
from flask_app import create_app, db as flask_db
from flask_app.models import SessionLog
from embeddings import init_vector_store, VectorStoreInitializationError
from chains import init_qa_chain

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Глобальные переменные для хранения состояния бота
retriever = None
qa_chain = None
is_initialized = False
initialization_error = None

def setup_environment():
    """Настройка окружения и загрузка конфигурации"""
    global flask_app
    
    try:
        # Загрузка переменных окружения
        if not load_dotenv():
            logger.warning("No .env file found or it's empty")
            
        # Проверка обязательных переменных окружения
        required_vars = ["TELEGRAM_TOKEN", "HUGGINGFACEHUB_API_TOKEN"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        # Инициализация Flask приложения
        try:
            flask_app = create_app()
            with flask_app.app_context():
                flask_db.create_all()
                logger.info("Database tables verified/created")
                
        except Exception as e:
            error_msg = f"Failed to initialize Flask app: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise
            
        logger.info("Environment setup completed successfully")
        
    except Exception as e:
        logger.critical(f"Critical error during environment setup: {str(e)}")
        logger.critical(traceback.format_exc())
        raise

# Инициализация окружения при импорте модуля
try:
    setup_environment()
except Exception as e:
    logger.critical("Failed to initialize environment. Bot cannot start.")
    raise

# Загрузка конфигурации
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN not set in .env")

async def initialize_resources():
    """
    Асинхронная инициализация ресурсов бота.
    
    Returns:
        bool: True если инициализация прошла успешно, иначе False
    """
    global retriever, qa_chain, is_initialized, initialization_error
    
    try:
        logger.info("Starting resource initialization...")
        
        # Сброс состояния
        is_initialized = False
        initialization_error = None
        
        # Инициализация векторного хранилища
        try:
            logger.info("Initializing vector store...")
            retriever = await asyncio.to_thread(init_vector_store)
            if not retriever:
                raise ValueError("Vector store initialization returned None")
            logger.info("Vector store initialized successfully")
            
        except VectorStoreInitializationError as e:
            error_msg = f"Failed to initialize vector store: {str(e)}"
            logger.error(error_msg)
            initialization_error = error_msg
            return False
            
        except Exception as e:
            error_msg = f"Unexpected error initializing vector store: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            initialization_error = error_msg
            return False
        
        # Инициализация QA цепи
        try:
            logger.info("Initializing QA chain...")
            qa_chain, system_prompt = await asyncio.to_thread(init_qa_chain, retriever)
            if not qa_chain:
                raise ValueError("QA chain initialization returned None")
            logger.info(f"QA chain initialized successfully with system prompt: {system_prompt[:100]}...")
            
            # Сохраняем system_prompt в глобальной области видимости
            global _system_prompt
            _system_prompt = system_prompt
            
        except Exception as e:
            error_msg = f"Failed to initialize QA chain: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            initialization_error = error_msg
            return False
        
        # Успешное завершение инициализации
        is_initialized = True
        logger.info("Resource initialization completed successfully")
        return True
        
    except Exception as e:
        error_msg = f"Critical error during resource initialization: {str(e)}"
        logger.critical(error_msg)
        logger.critical(traceback.format_exc())
        initialization_error = error_msg
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я AI-ассистент отдела продаж. "
        "Задайте мне вопрос о наших продуктах или услугах."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Асинхронный обработчик входящих сообщений.
    
    Args:
        update: Объект обновления от Telegram API
        context: Контекст выполнения обработчика
    """
    global is_initialized, initialization_error
    
    # Проверка инициализации бота
    if not is_initialized:
        error_msg = "Бот еще не инициализирован. "
        if initialization_error:
            error_msg += f"Ошибка инициализации: {initialization_error}"
        else:
            error_msg += "Попробуйте через 30 секунд."
            
        logger.warning(f"Bot not initialized. Error: {initialization_error or 'No error details'}")
        await update.message.reply_text(error_msg)
        return
        
    # Получение данных сообщения
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    query = (update.message.text or '').strip()
    
    logger.info(f"New message from user {user_id} (@{username}): {query[:100]}")

    # Валидация запроса
    if not query:
        await update.message.reply_text("Пожалуйста, введите текст запроса.")
        return
        
    if len(query) < 3:
        await update.message.reply_text("Пожалуйста, задайте более развернутый вопрос (минимум 3 символа).")
        return

    if len(query) > 1000:
        await update.message.reply_text("Ваш запрос слишком длинный. Пожалуйста, ограничьтесь 1000 символами.")
        return

    try:
        # Проверяем инициализацию QA цепи
        if not qa_chain:
            raise RuntimeError("QA цепь не инициализирована")

        # Отправляем уведомление о начале обработки
        processing_msg = await update.message.reply_text("⏳ Обрабатываю ваш запрос...")
        
        # Асинхронное выполнение запроса к LLM
        logger.info(f"Processing query from user {user_id}")
        try:
            # Get relevant context from the retriever
            try:
                logger.info(f"Retrieving context for query: {query[:100]}...")
                docs = await asyncio.to_thread(lambda: retriever.get_relevant_documents(query))
                context = "\n\n".join([doc.page_content for doc in docs])
                logger.info(f"Retrieved context length: {len(context)} characters")
                
                # Create the input dictionary with the expected format
                chain_input = {
                    "question": query,  # The question to answer
                    "context": context  # The retrieved context
                }
                
                # Log the input for debugging
                logger.info(f"QA chain input keys: {chain_input.keys()}")
                logger.info(f"Query length: {len(query)} characters, Context length: {len(context)} characters")
                
                # Call the QA chain without timeout
                logger.info("Calling QA chain...")
                try:
                    # Call the QA chain directly without timeout
                    result = await asyncio.to_thread(lambda: qa_chain(chain_input))
                    logger.info("QA chain call completed successfully")
                except Exception as e:
                    logger.error(f"Error in QA chain call: {str(e)}")
                    logger.error(traceback.format_exc())
                    raise RuntimeError(f"Ошибка при генерации ответа: {str(e)}")
                
            except Exception as e:
                logger.error(f"Error in QA chain processing: {str(e)}")
                logger.error(traceback.format_exc())
                raise RuntimeError(f"Ошибка при обработке запроса: {str(e)}")
            
            if not result:
                raise ValueError("QA chain returned no result")
                
            # Get the result using the output key we defined in init_qa_chain
            answer = result.get("result", "").strip()
            
            if not answer:
                # If result is empty, try to get any available output
                answer = str(result) if result else "Не удалось получить ответ от модели"
            
            # Extract only the assistant's response (after the last <|im_start|>assistant tag)
            if "<|im_start|>assistant" in answer:
                # Split by assistant tag and take the last part (the actual response)
                answer = answer.split("<|im_start|>assistant")[-1]
            
            # Remove any remaining tags
            answer = answer.replace("<|im_start|>", "").replace("<|im_end|>", "").strip()
            
            # Remove any system prompt that might be in the response
            if "# Роль и задачи ассистента" in answer:
                answer = answer.split("# Роль и задачи ассистента")[0].strip()
                
            # Remove any leading/trailing whitespace and normalize spaces
            import re
            answer = re.sub(r'\s+', ' ', answer).strip()
            
            # If we still have a very long response, truncate it
            if len(answer) > 4000:
                logger.warning("Response too long, truncating...")
                answer = answer[:4000] + "\n\n[Ответ обрезан из-за ограничений Telegram]"
            
            logger.info(f"Generated answer length: {len(answer)} characters")
                
        except Exception as e:
            error_msg = f"Ошибка при обработке запроса: {str(e)}"
            logger.error(f"Error in QA chain: {error_msg}")
            logger.error(traceback.format_exc())
            raise
            
        # Сохранение лога в базу данных
        try:
            with flask_app.app_context():
                log = SessionLog(
                    user_id=user_id,
                    username=username,
                    query=query,
                    response=answer[:2000],  # Обрезаем для SQLite
                    timestamp=datetime.utcnow()
                )
                flask_db.session.add(log)
                flask_db.session.commit()
                logger.info(f"Query from user {user_id} logged to database")
                
        except Exception as e:
            logger.error(f"Failed to log query to database: {str(e)}")
            # Продолжаем выполнение, даже если не удалось сохранить лог
            
        # Отправка ответа пользователю
        try:
            await processing_msg.edit_text(answer)
            logger.info(f"Response sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send response to user {user_id}: {str(e)}")
            await update.message.reply_text(
                "Произошла ошибка при отправке ответа. "
                "Попробуйте задать вопрос снова."
            )
            
    except Exception as e:
        error_msg = (
            "Извините, при обработке вашего запроса произошла ошибка. "
            "Попробуйте переформулировать вопрос или повторить позже."
        )
        logger.error(f"Error processing message from user {user_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        try:
            await update.message.reply_text(error_msg)
        except Exception as e:
            logger.critical(f"CRITICAL: Failed to send error message to user {user_id}: {str(e)}")


async def post_init(application: Application) -> None:
    """
    Post-initialization hook for the Telegram bot application.
    
    This function is called after the application is created but before it starts polling.
    It initializes all required resources and handles any initialization errors.
    
    Args:
        application: The Telegram bot application instance
    """
    global is_initialized, initialization_error
    
    try:
        logger.info("Starting bot initialization...")
        
        # Initialize resources
        success = await initialize_resources()
        
        if not success:
            error_msg = (
                "⚠️ Не удалось инициализировать бота. "
                f"Причина: {initialization_error or 'неизвестная ошибка'}"
            )
            logger.critical("Bot initialization failed")
            
            # Try to notify admin if possible
            admin_id = os.getenv("ADMIN_TELEGRAM_ID")
            if admin_id and admin_id.isdigit():
                try:
                    await application.bot.send_message(
                        chat_id=int(admin_id),
                        text=f"❌ Ошибка инициализации бота: {initialization_error or 'Неизвестная ошибка'}"
                    )
                except Exception as e:
                    logger.error(f"Failed to send error notification to admin: {str(e)}")
            
            raise RuntimeError(f"Bot initialization failed: {initialization_error}")
            
        logger.info("Bot initialization completed successfully")
        
        # Send startup notification to admin
        admin_id = os.getenv("ADMIN_TELEGRAM_ID")
        if admin_id and admin_id.isdigit():
            try:
                await application.bot.send_message(
                    chat_id=int(admin_id),
                    text="✅ Бот успешно запущен и готов к работе!"
                )
            except Exception as e:
                logger.warning(f"Failed to send startup notification to admin: {str(e)}")
                
    except Exception as e:
        logger.critical(f"Critical error in post_init: {str(e)}")
        logger.critical(traceback.format_exc())
        raise


def main():
    # Создание и настройка приложения
    application = Application.builder().token(TOKEN).post_init(post_init).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling(
        poll_interval=0.5,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()