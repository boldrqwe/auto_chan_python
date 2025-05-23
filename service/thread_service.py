import asyncio
import logging

from utils.harkach_markup_converter import HarkachMarkupConverter
from utils.thread_utils import filter_new_media, fetch_thread_data_safe, group_split

__STEP = 10

logger = logging.getLogger(__name__)

converter = HarkachMarkupConverter()


async def batch_threads(batch_size, delay, dvach, media_found, media_queue, posted_media, threads, threads_processed):
    """
    Обрабатывает пакеты тредов и вызывает обработку каждого треда.
    """
    filter_keywords = {"fap", "dark", "afp"}  # Набор слов для фильтрации caption

    for i in range(0, len(threads), batch_size):
        batch = threads[i:i + batch_size]

        for thread in batch:


            # Проверяем caption на наличие запрещённых слов
            caption = thread.get("comment", "").lower()
            if any(keyword in caption for keyword in filter_keywords):
                logger.info(f"Тред {thread} отфильтрован из-за содержания: '{caption}'.")
                continue

            # Обрабатываем тред, если он прошёл фильтрацию
            await process_thread(thread, dvach, media_queue, posted_media, media_found, threads_processed)

        # Пауза перед следующим пакетом тредов
        logger.info("Пакет тредов обработан. Ждём %d секунд перед следующим пакетом.", delay)
        await asyncio.sleep(delay)

    return media_found, threads_processed


async def process_thread(thread, dvach, media_queue, posted_media, media_found, threads_processed):
    """
    Обрабатывает один тред: загружает данные, фильтрует медиа, формирует группы и добавляет их в очередь.
    """
    thread_num = thread.get("num") or thread.get("thread_num")
    if not thread_num:
        logger.debug(f"Пропускаем тред без номера: {thread}")
        return

    # Безопасное получение данных треда
    t_data = await fetch_thread_data_safe(dvach, thread_num)
    if not t_data:
        return

    # Фильтрация новых медиа
    new_media = filter_new_media(t_data["media"], posted_media)
    if not new_media:
        logger.debug("Нет новых медиа в треде %s.", thread_num)
        return

    # Добавляем новые медиа в список отправленных
    posted_media.update(new_media)

    # Преобразуем разметку для caption
    raw_caption = t_data["caption"][:1024]
    thread_link = f"https://2ch.su/b/res/{thread_num}.html"  # Формирование ссылки на тред
    caption_html = converter.convert_to_tg_html(raw_caption)

    # Добавляем ссылку на тред в конец caption
    caption_html += f"\n===========\n<a href=\"{thread_link}\">Ссылка на тред</a>"

    # Разбиваем медиа на группы и добавляем их в очередь
    media_groups = []
    for j in range(0, len(new_media), __STEP):
        await group_split(caption_html, j, media_groups, new_media)

    for g in media_groups:
        await media_queue.put(g)
        media_found += len(g)

    threads_processed += 1
    logger.info("Тред %s обработан. Новых медиа: %d, групп: %d.", thread_num, len(new_media), len(media_groups))

#
