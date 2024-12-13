import logging
import asyncio  # Для использования asyncio.sleep

from service.thread_service import batch_threads

logger = logging.getLogger(__name__)


async def job_collect_media(dvach, posted_media, media_queue, batch_size=5, delay=10):
    """Сбор медиа с 2ch пакетами по batch_size тредов с паузой delay между пакетами."""
    logger.info("Начинаем сбор медиа с Двача...")

    try:
        threads = dvach.fetch_threads(board_name="b")
        logger.info("Получено %d тредов.", len(threads))
    except Exception as e:
        logger.error(f"Не удалось получить треды: {e}")
        return

    threads_processed = 0
    media_found = 0

    # Разделяем список тредов на пакеты
    for batch in range(0, len(threads), batch_size):
        # Проверяем размер очереди
        while media_queue.qsize() > 21:
            logger.info("Очередь переполнена (%d элементов). Ожидание освобождения...", media_queue.qsize())
            await asyncio.sleep(60)  # Ждём 5 секунд перед повторной проверкой

        # Обрабатываем текущий пакет
        current_batch = threads[batch:batch + batch_size]
        media_found, threads_processed = await batch_threads(
            batch_size, delay, dvach, media_found, media_queue,
            posted_media, current_batch, threads_processed
        )

        logger.info("Обработан пакет из %d тредов. Общая обработка: %d тредов, найдено медиа: %d",
                    len(current_batch), threads_processed, media_found)

    logger.info("Сбор медиа завершен. Обработано тредов: %d, найдено медиа: %d, очередь размером: %d",
                threads_processed, media_found, media_queue.qsize())

    # Очистка posted_media для уменьшения потребления памяти
    if len(posted_media) > 10000:#
        logger.info("Очистка коллекции отправленных медиа.")
        posted_media.clear()


#

