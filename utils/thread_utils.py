import logging
import re

from utils.media_utils import create_input_media

__STEP = 6

logger = logging.getLogger(__name__)


async def fetch_thread_data_safe(dvach, thread_num):
    """
    Безопасно получает данные треда, обрабатывая возможные исключения.
    """
    try:
        return dvach.fetch_thread_data(thread_num, board="b")
    except Exception as e:
        logger.error(f"Не удалось получить данные треда {thread_num}: {e}")
        return None






def filter_new_media(media_items, previously_posted_media, log_file="filtered_media.log"):
    """
    Фильтрует медиа, которые уже были отправлены, или содержат исключаемую подстроку.
    Записывает отфильтрованные записи в лог-файл.

    :param media_items: Список новых медиа объектов.
    :param previously_posted_media: Список уже отправленных медиа объектов.
    :param excluded_substring: Подстрока, по которой осуществляется фильтрация.
    :param log_file: Имя файла для записи отфильтрованных записей.
    :return: Список отфильтрованных медиа объектов.
    """
    excluded_pattern = re.compile(r"(?i)(fap|afp|paf|pfa|apf|fpa|ФУРРЯТНИЦА)")
    filtered_out = []

    result = []
    for media_item in media_items:
        if media_item not in previously_posted_media \
           and not excluded_pattern.search(media_item.get('message', '')) \
           and not excluded_pattern.search(media_item.get('name', '')):
            result.append(media_item)
        else:
            filtered_out.append(media_item)

    # Запись отфильтрованных записей в лог-файл
    if filtered_out:
        with open(log_file, "a", encoding="utf-8") as log:
            for item in filtered_out:
                log.write(f"Отфильтровано: {item}\n")

    return result


async def group_split(caption_html, j, media_groups, new_media):
    """
    Разбивает список медиа на группы, добавляя подпись только к первому элементу первой группы.
    """
    group = []
    batch_group = new_media[j:j + __STEP]
    for idx, u in enumerate(batch_group):
        # Первый элемент первой группы с подписью
        if j == 0 and idx == 0:
            group.append(create_input_media(u, caption=caption_html))
        else:
            group.append(create_input_media(u))
    media_groups.append(group)