import asyncio
import logging
import os
import re

import nest_asyncio
from telegram import Bot
from telegram.ext import ApplicationBuilder
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

nest_asyncio.apply()

# Загрузка переменных окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "-1002162401416")
POST_INTERVAL = int(os.environ.get("TELEGRAM_POST_INTERVAL", "40"))  # Пауза между отправками в секундах
FETCH_BATCH_SIZE = int(os.environ.get("FETCH_BATCH_SIZE", "1"))  # Количество тредов за раз
FETCH_DELAY = int(os.environ.get("FETCH_DELAY", "40"))  # Пауза между пакетами в секундах

# Проверка и логирование переменных окружения
required_vars = ["BOT_TOKEN", "TELEGRAM_CHANNEL_ID"]
missing = [var for var in required_vars if not globals().get(var)]
if missing:
    raise ValueError(f"Не заданы переменные окружения: {', '.join(missing)}")
logger.info(", ".join(f"{var}: {globals().get(var)}" for var in required_vars + ["POST_INTERVAL", "FETCH_BATCH_SIZE", "FETCH_DELAY"]))

application = ApplicationBuilder().token(BOT_TOKEN).build()
bot: Bot = application.bot

# Инициализация сервисов
dvach = DvachService()
chat_gpt_client = ChatGPTClient(api_key=os.environ.get("OPENAI_API_KEY"), prompt_file="prompt.md")
posted_media = set()
media_queue = asyncio.Queue()

def scheduled_job():
    logger.info("Запуск плановой задачи по сбору медиа...")
    media = job_collect_media(dvach, posted_media, media_queue, FETCH_BATCH_SIZE, FETCH_DELAY)
    asyncio.create_task(media)

async def send_anecdote():
    def escape_markdown_v2(text):
        """Экранирование символов для MarkdownV2."""
        return re.sub(r'([_*\[\]()~`>#+-=|{}.!])', r'\\\1', text)

    while True:
        try:
            logger.info("Генерация анекдота...")
            anecdote = chat_gpt_client.generate_response()
            escaped_anecdote = escape_markdown_v2(anecdote)  # Экранирование текста
            message = await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=escaped_anecdote, parse_mode="MarkdownV2")
            # Закрепление сообщения
            await bot.pin_chat_message(chat_id=TELEGRAM_CHANNEL_ID, message_id=message.message_id, disable_notification=True)
            logger.info("Анекдот успешно отправлен и закреплён.")
        except TelegramError as e:
            logger.error(f"Ошибка при отправке анекдота: {e}")
        await asyncio.sleep(500)  # Интервал в 1 минуту

async def main():
    logger.info("Запуск бота...")
    await check_chat_access(bot, TELEGRAM_CHANNEL_ID)
    asyncio.create_task(post_media_from_queue(bot, TELEGRAM_CHANNEL_ID, POST_INTERVAL, media_queue))
    asyncio.create_task(send_anecdote())  # Отправка анекдотов независимо

    # Запуск задач: сбор медиа
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

