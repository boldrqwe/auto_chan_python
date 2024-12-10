import asyncio
import logging

logger = logging.getLogger(__name__)  #

from media_utils import filter_accessible_media


async def post_media_from_queue(bot, channel_id, interval, media_queue):
    while True:
        try:
            media_group = await media_queue.get()
            logger.info(f"Отправка медиагруппы: {media_group}")

            # Фильтрация доступных ссылок
            filtered_media_group = await filter_accessible_media(media_group)
            if not filtered_media_group:
                logger.warning("Нет доступных медиа для отправки. Пропускаем группу.")
                continue

            # Отправка медиагруппы
            await bot.send_media_group(chat_id=channel_id, media=filtered_media_group)
            logger.info("Медиагруппа успешно отправлена.")

        except asyncio.TimeoutError:
            logger.warning("Отправка медиагруппы прервана по таймауту. Это не критическая ошибка.")
        except Exception as e:
            if "Timed out" in str(e):
                logger.warning("Пропущена ошибка таймаута отправки медиагруппы. Продолжаем работу.")
            else:
                logger.error(f"Ошибка при отправке медиагруппы: {e}")
        finally:
            await asyncio.sleep(interval)
