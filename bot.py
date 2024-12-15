# bot.py
import asyncio
import logging
import os
import re

from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from game import RPGGame
from service.dvach_service import DvachService
from service.media_poster import post_media_from_queue
from utils.media_utils import check_chat_access
from service.tasks import job_collect_media
from telegram.error import TelegramError
from service.ChatGPTService import ChatGPTClient

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "-1002162401416")
POST_INTERVAL = int(os.environ.get("TELEGRAM_POST_INTERVAL", "30"))
FETCH_BATCH_SIZE = int(os.environ.get("FETCH_BATCH_SIZE", "1"))
FETCH_DELAY = int(os.environ.get("FETCH_DELAY", "40"))

# Проверка и логирование переменных окружения
required_vars = ["BOT_TOKEN", "TELEGRAM_CHANNEL_ID"]
missing = [var for var in required_vars if not globals().get(var)]
if missing:
    raise ValueError(f"Не заданы переменные окружения: {', '.join(missing)}")
logger.info(", ".join(f"{var}: {globals().get(var)}" for var in required_vars + ["POST_INTERVAL", "FETCH_BATCH_SIZE", "FETCH_DELAY"]))

# Создаем приложение
application = ApplicationBuilder().token(BOT_TOKEN).build()
bot: Bot = application.bot

# Инициализация сервисов и ресурсов
dvach = DvachService()
chat_gpt_client = ChatGPTClient(api_key=os.environ.get("OPENAI_API_KEY"), prompt_file="prompt.md")
posted_media = set()
media_queue = asyncio.Queue()

# Инициализация игры
game = RPGGame(bot)
game.register_handlers(application)

async def send_anecdotes_task(bot, chat_gpt_client, channel_id):
    """Фоновая задача отправки анекдотов в указанный канал."""
    while True:
        try:
            logger.info("Генерация анекдота...")
            anecdote = await chat_gpt_client.generate_response()
            message = await bot.send_message(chat_id=channel_id, text=anecdote, parse_mode="HTML")
            # Закрепляем сообщение
            await bot.pin_chat_message(chat_id=channel_id, message_id=message.message_id, disable_notification=True)
            logger.info("Анекдот успешно отправлен и закреплён.")
        except TelegramError as e:
            logger.error(f"Ошибка при отправке анекдота: {e}")
        except Exception as e:
            logger.error(f"Ошибка при генерации анекдота: {e}")
        await asyncio.sleep(345)  # Ждём 345 секунд перед следующим анекдотом

async def media_collector_task(dvach, posted_media, media_queue, fetch_batch_size, fetch_delay):
    """Фоновая задача по сбору медиа с 2ch."""
    while True:
        logger.info("Запуск плановой задачи по сбору медиа...")
        # job_collect_media должен быть асинхронным, убедитесь в этом или адаптируйте код
        await job_collect_media(dvach, posted_media, media_queue, fetch_batch_size, fetch_delay)
        logger.info(f"Количество элементов в очереди: {media_queue.qsize()}")
        await asyncio.sleep(fetch_delay)

async def post_init(application):
    """Функция, вызываемая после инициализации приложения, перед запуском поллинга."""
    await check_chat_access(bot, TELEGRAM_CHANNEL_ID)
    # Запускаем фоновые задачи
    # application.create_task(send_anecdotes_task(bot, chat_gpt_client, TELEGRAM_CHANNEL_ID))
    application.create_task(post_media_from_queue(bot, TELEGRAM_CHANNEL_ID, POST_INTERVAL, media_queue))
    application.create_task(media_collector_task(dvach, posted_media, media_queue, FETCH_BATCH_SIZE, FETCH_DELAY))
    logger.info("Бот инициализирован и фоновые задачи запущены.")

# Назначаем post_init коллбек
application.post_init = post_init

if __name__ == "__main__":
    # Запускаем бота с помощью run_polling()
    # run_polling() — блокирующий вызов, который завершится только при остановке бота.
    application.run_polling()
