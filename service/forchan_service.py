from utils.harkach_markup_converter import HarkachMarkupConverter
import asyncio
import logging
import requests
from utils.media_utils import create_input_media

converter = HarkachMarkupConverter()


class ForchanService:
    BASE_URL = "https://a.4cdn.org"

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def fetch_threads(self, board_name="b"):
        """Fetch a list of threads from the specified board."""
        url = f"{self.BASE_URL}/{board_name}/threads.json"
        try:
            self.logger.info(f"Получение списка тредов с {url}")
            response = requests.get(url)
            response.raise_for_status()
            threads_data = response.json()
            threads = [t['no'] for page in threads_data for t in page['threads']]
            self.logger.info(f"Получено тредов: {len(threads)} с доски /{board_name}/")
            return threads
        except Exception as e:
            self.logger.exception(f"Ошибка при получении списка тредов с /{board_name}/: {e}")
            return []

    def fetch_thread_data(self, thread_id, board_name="b"):
        """Fetch data from a specific thread, including media links."""
        url = f"{self.BASE_URL}/{board_name}/thread/{thread_id}.json"
        try:
            self.logger.info(f"Получение данных треда {thread_id} с {url}")
            response = requests.get(url)
            response.raise_for_status()
            thread_data = response.json()

            op_post = thread_data['posts'][0]
            op_comment = op_post.get('com', "Без текста")

            media_urls = []
            for post in thread_data['posts']:
                if 'tim' in post and 'ext' in post:
                    media_url = f"https://i.4cdn.org/{board_name}/{post['tim']}{post['ext']}"
                    media_urls.append(media_url)

            self.logger.info(f"Тред {thread_id} получен: ОП-комментарий длиной {len(op_comment)} символов, медиафайлов: {len(media_urls)}")

            return {
                "caption": op_comment,
                "media": media_urls
            }

        except Exception as e:
            self.logger.exception(f"Ошибка при обработке треда {thread_id} с /{board_name}/: {e}")
            return None

    async def collect_media_periodically(self, posted_media, media_queue, board_name="b", max_group_size=6, delay=10):
        """
        Периодически собирает медиа-ссылки и добавляет их в очередь группами по max_group_size.
        Только первый элемент группы содержит caption с красивой ссылкой на тред.
        """
        while True:
            try:
                self.logger.info(f"Начало сбора медиа с доски /{board_name}/...")
                threads = self.fetch_threads(board_name)

                for thread_id in threads:
                    thread_data = self.fetch_thread_data(thread_id, board_name)

                    if not thread_data or not thread_data.get("media"):
                        self.logger.info(f"Нет медиа для треда {thread_id}")
                        continue

                    # Получаем все медиа из треда и фильтруем уже отправленные
                    all_media = [url for url in thread_data["media"] if url not in posted_media and not url.endswith(".webm")]


                    if not all_media:
                        self.logger.info(f"Новых медиа в треде {thread_id} нет.")
                        continue

                    self.logger.info(f"Тред {thread_id}: найдено новых медиа: {len(all_media)}")

                    # Формируем ссылку на тред
                    thread_url = f"https://boards.4chan.org/{board_name}/thread/{thread_id}"
                    formatted_link = f'\n===========\n<a href="{thread_url}">Ссылка на тред</a>'

                    # Разбиваем медиа на группы по max_group_size
                    for i in range(0, len(all_media), max_group_size):
                        # Ожидаем, если очередь переполнена
                        while media_queue.qsize() >= 21:
                            self.logger.info("Очередь переполнена. Ожидание освобождения...")
                            await asyncio.sleep(10)  # Проверяем каждые 10 секунд

                        media_group_urls = all_media[i:i + max_group_size]

                        # Конвертируем в InputMedia и добавляем caption только первому элементу
                        media_group = []
                        for idx, url in enumerate(media_group_urls):
                            caption = None
                            if idx == 0:  # Caption только для первого элемента группы
                                thread_caption = converter.convert_to_tg_html(thread_data["caption"])
                                caption = f"{thread_caption}{formatted_link}"

                            media_group.append(create_input_media(url, caption))

                        # Добавляем группу в очередь
                        await media_queue.put(media_group)


                    # Помечаем медиа как отправленные
                    posted_media.update(all_media)

                    self.logger.info(f"Тред {thread_id} полностью обработан.")

                    # Задержка перед обработкой следующего треда
                    await asyncio.sleep(25)

                self.logger.info("Обработка всех тредов завершена. Ожидание перед новым циклом.")
                await asyncio.sleep(delay)

            except Exception as e:
                self.logger.exception(f"Ошибка при сборе медиа: {e}")
                await asyncio.sleep(delay)


# Пример использования:
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    forchan_service = ForchanService()

    posted_media = set()
    media_queue = asyncio.Queue()

    # Параметры
    board_name = "b"
    max_group_size = 6
    delay = 30

    # Запуск сбора медиа в асинхронном режиме
    asyncio.run(forchan_service.collect_media_periodically(posted_media, media_queue, board_name, max_group_size, delay))
