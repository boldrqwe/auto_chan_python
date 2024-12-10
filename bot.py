import asyncio
import logging
import os

import nest_asyncio
from telegram import Bot
from telegram.ext import ApplicationBuilder

from dvach_service import DvachService
from media_poster import post_media_from_queue
from media_utils import check_chat_access
from tasks import job_collect_media

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

dvach = DvachService()
posted_media = set()
media_queue = asyncio.Queue()

def scheduled_job():
    logger.info("Запуск плановой задачи по сбору медиа...")
    asyncio.create_task(job_collect_media(dvach, posted_media, media_queue, FETCH_BATCH_SIZE, FETCH_DELAY))

async def main():
    logger.info("Запуск бота...")
    await check_chat_access(bot, TELEGRAM_CHANNEL_ID)
    asyncio.create_task(post_media_from_queue(bot, TELEGRAM_CHANNEL_ID, POST_INTERVAL, media_queue))

    # Запускаем задачу сбора медиа каждые 1 минуту
    while True:
        scheduled_job()
        logger.info("Количество элементов в очереди: " + str(media_queue.qsize()))
        await asyncio.sleep(FETCH_DELAY)  # Ждём 60 секунд перед следующим сбором

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки. Завершаем работу...")
    except Exception as e:
        logger.exception("Критическая ошибка в работе бота: %s", e)

