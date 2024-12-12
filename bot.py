import asyncio
import logging
import os
import requests
import nest_asyncio
from telegram import Bot, Update
from telegram.ext import CommandHandler, MessageHandler, filters, ApplicationBuilder, ContextTypes
from service.dvach_service import DvachService
from service.media_poster import post_media_from_queue
from utils.media_utils import check_chat_access
from service.tasks import job_collect_media

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

nest_asyncio.apply()

# Загрузка переменных окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "-1002162401416")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_API_ENDPOINT = "https://api.openai.com/v1/chat/completions"
POST_INTERVAL = int(os.environ.get("TELEGRAM_POST_INTERVAL", "40"))  # Пауза между отправками в секундах
FETCH_BATCH_SIZE = int(os.environ.get("FETCH_BATCH_SIZE", "1"))  # Количество тредов за раз
FETCH_DELAY = int(os.environ.get("FETCH_DELAY", "40"))  # Пауза между пакетами в секундах

# Проверка и логирование переменных окружения
required_vars = ["BOT_TOKEN", "TELEGRAM_CHANNEL_ID", "OPENAI_API_KEY"]
missing = [var for var in required_vars if not globals().get(var)]
if missing:
    raise ValueError(f"Не заданы переменные окружения: {', '.join(missing)}")
logger.info(", ".join(f"{var}: {globals().get(var)}" for var in required_vars + ["POST_INTERVAL", "FETCH_BATCH_SIZE", "FETCH_DELAY"]))

# Инициализация объектов
application = ApplicationBuilder().token(BOT_TOKEN).build()
bot: Bot = application.bot

dvach = DvachService()
posted_media = set()
media_queue = asyncio.Queue()

# Telegram обработчики
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напишите мне сообщение, и я отвечу с помощью ChatGPT, или подождите публикации из 2ch.")

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

# Плановая задача
def scheduled_job():
    logger.info("Запуск плановой задачи по сбору медиа...")
    asyncio.create_task(job_collect_media(dvach, posted_media, media_queue, FETCH_BATCH_SIZE, FETCH_DELAY))

async def main():
    logger.info("Запуск бота...")
    await check_chat_access(bot, TELEGRAM_CHANNEL_ID)
    asyncio.create_task(post_media_from_queue(bot, TELEGRAM_CHANNEL_ID, POST_INTERVAL, media_queue))

    # Добавляем обработчики команд и сообщений
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Запускаем задачу сбора медиа каждые 1 минуту
    while True:
        scheduled_job()
        logger.info("Количество элементов в очереди: " + str(media_queue.qsize()))
        await asyncio.sleep(FETCH_DELAY)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки. Завершаем работу...")
    except Exception as e:
        logger.exception("Критическая ошибка в работе бота: %s", e)
