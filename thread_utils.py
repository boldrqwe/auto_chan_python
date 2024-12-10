import logging

from media_utils import create_input_media

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


def filter_new_media(media, posted_media):
    """
    Фильтрует медиа, которые уже были отправлены.
    """
    return [m for m in media if m not in posted_media]


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