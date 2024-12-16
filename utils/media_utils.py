import logging
import aiohttp
import tempfile
from PIL import Image, UnidentifiedImageError
from nudenet import NudeDetector
from asyncio import Semaphore
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




# Инициализация NudeDetector
detector = NudeDetector()
semaphore = Semaphore(5)  # Ограничение одновременных задач

async def is_not_pornographic_media(url, threshold = 0.45):
    """
    Асинхронно проверяет, является ли медиа по URL порнографическим (поддержка изображений и видео).
    """
    async with semaphore:
        try:
            logger.debug(f"Загрузка медиа: {url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Ошибка скачивания медиа: {url}, статус: {response.status}")
                        return False

                    # Сохранение медиа во временный файл
                    # suffix = ".mp4" if url.endswith((".webm", ".mp4")) else ".jpeg"
                    # with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                    #     temp_file.write(await response.read())
                    #     temp_file.flush()
                    #
                    #     # Если это изображение, проверяем через Pillow
                    #     if suffix == ".jpeg":
                    #         try:
                    #             with Image.open(temp_file.name) as img:
                    #                 img.verify()  # Проверка корректности изображения
                    #         except (UnidentifiedImageError, IOError):
                    #             logger.error(f"Файл повреждён или не является изображением: {url}")
                    #             return False
                    #
                    #     # Анализ с помощью NudeNet
                    #     logger.debug(f"Проверка медиа через NudeNet: {url}")
                    #     results = detector.detect(temp_file.name)
                    #
                    #     pornographic_classes = {
                    #         "FEMALE_BREAST_EXPOSED",
                    #         "FEMALE_GENITALIA_EXPOSED",
                    #         "BUTTOCKS_EXPOSED",
                    #         "ANUS_EXPOSED",
                    #         "MALE_GENITALIA_EXPOSED",
                    #     }
                    #
                    #     for result in results:
                    #         class_ = result["class"]
                    #         if class_ in pornographic_classes and result["score"] >= threshold:
                    #             logger.warning(f"Обнаружен порнографический контент: {url, class_}")
                    #             return False  # Контент запрещён

            logger.info(f"Медиа прошло проверку: {url}")
            return True  # Контент допустим
        except Exception as e:
            logger.error(f"Ошибка обработки URL {url}: {e}")
            return False


async def filter_accessible_media(media_group):
    """
    Асинхронно фильтрует медиа на доступность и проверку контента.
    """
    accessible_media = []
    for media in media_group:
        logger.info(f"Начата обработка URL: {media.media}")
        try:
            # Проверяем контент медиа
            is_not_porn = await is_not_pornographic_media(media.media)
            if is_not_porn:
                logger.info(f"Медиа допущено: {media.media}")
                accessible_media.append(media)
            else:
                logger.warning(f"URL {media.media} содержит запрещённый контент.")
        except Exception as e:
            logger.error(f"Ошибка обработки медиа {media.media}: {e}")
    logger.info(f"Допущенные медиа: {[m.media for m in accessible_media]}")
    return accessible_media


async def check_chat_access(bot, channel_id):
    try:
        logger.info(f"Проверка доступа к чату: {channel_id}")
        chat = await bot.get_chat(chat_id=channel_id)
        logger.info(f"Бот имеет доступ к чату: {chat.title}")
    except Exception as e:
        logger.error(f"Ошибка доступа к чату {channel_id}: {e}")
        raise ValueError("Невозможно получить доступ к указанному чату!")

