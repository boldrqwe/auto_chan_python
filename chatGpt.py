import asyncio
import logging
import os
import requests
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ApplicationBuilder, ContextTypes

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

# Загрузка переменных окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_API_ENDPOINT = "https://api.openai.com/v1/chat/completions"

# Проверка переменных окружения
required_vars = ["BOT_TOKEN", "OPENAI_API_KEY"]
missing = [var for var in required_vars if not globals().get(var)]
if missing:
    raise ValueError(f"Не заданы переменные окружения: {', '.join(missing)}")
logger.info(", ".join(f"{var}: {globals().get(var)}" for var in required_vars))

# Инициализация объектов
application = ApplicationBuilder().token(BOT_TOKEN).build()


# Telegram обработчики
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напишите мне сообщение, и я отвечу с помощью ChatGPT.")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    logger.info(f"Получено сообщение: {user_message}")

    # Запрос к ChatGPT API
    logger.info("Отправка текста в OpenAI")
    response = requests.post(
        OPENAI_API_ENDPOINT,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ]
        }
    )

    result = response.json()

    if response.status_code != 200 or "error" in result:
        error_message = result.get("error", {}).get("message", "Неизвестная ошибка")
        logger.error(f"Ошибка OpenAI API: {error_message}")
        await update.message.reply_text(f"Произошла ошибка при обращении к OpenAI API: {error_message}")
    else:
        chatgpt_reply = result['choices'][0]['message']['content']
        logger.info(f"Ответ ChatGPT: {chatgpt_reply}")
        await update.message.reply_text(chatgpt_reply)


# Добавляем обработчики команд и сообщений
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

# Запуск Telegram-бота
if __name__ == "__main__":
    try:
        asyncio.run(application.run_polling())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем.")
