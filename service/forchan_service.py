import logging
import asyncio
import requests
import time

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
        """Collect media links periodically and add them to the media queue as groups with filtering."""
        while True:
            try:
                self.logger.info(f"Начало сбора медиа с доски /{board_name}/...")
                threads = self.fetch_threads(board_name)

                total_groups = 0
                for thread_id in threads:
                    thread_data = self.fetch_thread_data(thread_id, board_name)

                    if thread_data and thread_data.get("media"):
                        new_media = [url for url in thread_data["media"] if url not in posted_media]

                        # Разделяем медиа на группы по max_group_size
                        for i in range(0, len(new_media), max_group_size):
                            media_group = new_media[i:i + max_group_size]
                            media_group_with_caption = {
                                "caption": thread_data["caption"],
                                "media": media_group
                            }
                            await media_queue.put(media_group_with_caption)
                            total_groups += 1

                        # Помечаем добавленные ссылки как отправленные
                        posted_media.update(new_media)

                    # Перерыв между обработкой тредов
                    await asyncio.sleep(25)

                self.logger.info(f"Сбор завершён: добавлено {total_groups} групп в очередь.")

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
