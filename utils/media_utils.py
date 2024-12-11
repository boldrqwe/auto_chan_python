import logging

import httpx
from telegram import InputMediaPhoto, InputMediaVideo

logger = logging.getLogger(__name__)

def create_input_media(url: str, caption: str = None):
    """Определяем тип медиа для отправки в группу."""
    logger.debug(f"Создание медиа-объекта для URL: {url}, caption: {caption is not None}")
    if any(url.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif"]):
        return InputMediaPhoto(media=url, caption=caption, parse_mode='HTML')
    elif any(url.endswith(ext) for ext in [".webm", ".mp4"]):
        return InputMediaVideo(media=url, caption=caption, parse_mode='HTML')
    else:
        logger.debug("Неизвестный формат. Используем InputMediaPhoto по умолчанию.")
        return InputMediaPhoto(media=url, caption=caption, parse_mode='HTML')


async def is_url_accessible(url):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.head(url)
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Ошибка проверки URL {url}: {e}")
        return False

async def filter_accessible_media(media_group):
    accessible_media = []
    for media in media_group:
        if await is_url_accessible(media.media):
            accessible_media.append(media)
        else:
            logger.warning(f"URL недоступен: {media.media}")
    return accessible_media


async def check_chat_access(bot, channel_id):
    try:
        logger.info(f"Проверка доступа к чату: {channel_id}")
        chat = await bot.get_chat(chat_id=channel_id)
        logger.info(f"Бот имеет доступ к чату: {chat.title}")
    except Exception as e:
        logger.error(f"Ошибка доступа к чату {channel_id}: {e}")
        raise ValueError("Невозможно получить доступ к указанному чату!")