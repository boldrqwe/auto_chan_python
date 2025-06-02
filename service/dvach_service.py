import asyncio
import hashlib
import logging

import aiohttp
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)
import time


class DvachService:
    BASE_URL = "https://2ch.su"

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    import logging

    logger = logging.getLogger(__name__)

    async def review_thread_task(dvach, bot, chat_gpt_client, channel_id, fetch_delay=300):
        posted_review = set()
        while True:
            try:
                logger.info("Начинаем сбор медиа с Двача...")

                # Получение списка тредов
                threads = await dvach.fetch_threads(board="b")
                logger.info("Получено %d тредов.", len(threads))

                # Выбор самого популярного треда
                thread = max(
                    (t for t in threads if t["num"] not in posted_review),
                    key=lambda x: x["posts_count"],
                    default=None
                )

                if not thread:
                    logger.info("Нет новых тредов для обработки.")
                    await asyncio.sleep(fetch_delay)
                    continue

                thread_num_ = thread['num']
                logger.info(f"Обрабатываем тред {thread_num_} с {thread['posts_count']} постами.")

                # Сохранение обработанного треда
                posted_review.add(thread["num"])

                # Промпт для анализа
                prompt = dvach.read_file_line_by_line("service/promt.txt")

                # Получение содержимого треда
                content = await dvach.get_thread_content(thread["num"])
                if not content.get("threads"):
                    logger.error(f"Тред {thread_num_} не содержит данных.")
                    continue



                filtered_posts = [
                    {"num": post["num"], "comment": post["comment"]}
                    for post in content["threads"][0]["posts"][:40]
                ]


                logger.info(f"Тред {thread_num_} содержит {len(str(filtered_posts))} символов текста.")


                # Формирование сообщений
                messages = [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": str(filtered_posts)}
                ]

                # Генерация рецензии
                logger.info(f"Генерация рецензии для треда {thread_num_}...")
                response = await chat_gpt_client.generate_response(messages)
                thread_url = f"{BASE_URL}/b/res/{thread_num_}.html"
                final_response = f"Ссылка на тред: {thread_url}\n==================================\n{response}"
                # Отправка рецензии в Telegram
                logger.info(f"Отправляем рецензию на тред {thread_num_} в канал...")
                await bot.send_message(chat_id=channel_id, text=final_response, parse_mode="HTML")
                logger.info(f"Рецензия на тред {thread_num_} успешно отправлена.")

            except Exception as e:
                logger.error(f"Ошибка в review_thread_task: {e}")

            # Ожидание перед следующей итерацией
            await asyncio.sleep(fetch_delay)

    async def get_new_threads(self, board: str) -> list:
        """Получает список тредов для указанной доски."""
        url = f"{BASE_URL}/{board}/catalog.json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Ошибка при загрузке каталога: {response.status}")
                    return []
                data = await response.json()
                return data.get("threads", [])

    def read_file_line_by_line(self,filename):
        with open(filename, "r", encoding="utf-8") as file:
            content = file.read()
        return content

    import logging

    logger = logging.getLogger(__name__)

    async def get_thread_content(self, thread_id: str) -> dict:
        """Получает содержимое треда по ID."""
        url = f"{BASE_URL}/b/res/{thread_id}.json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Ошибка при загрузке треда {thread_id}: {response.status}")
                    return {}
                return await response.json()

    async def fetch_threads(self, board="b", max_retries=3, delay=6):
        url = f"{self.BASE_URL}/{board}/threads.json"
        self.logger.info(f"Попытка получить список тредов с {url}")

        for attempt in range(max_retries):
            self.logger.debug(f"Попытка {attempt + 1} из {max_retries} получить треды.")
            try:
                response = requests.get(url, headers=self._get_default_headers())
                response.raise_for_status()
                data_json = response.json()
                self.logger.debug(
                    f"Ответ получен. Ключи: {list(data_json.keys()) if isinstance(data_json, dict) else 'не dict'}")
                threads = data_json.get("threads", [])
                self.logger.info(f"Получено тредов: {len(threads)}")
                return threads
            except requests.exceptions.HTTPError as e:
                self.logger.error(f"HTTP Error при получении тредов с {url}: {e}")
                if attempt < max_retries - 1:
                    self.logger.info(f"Повторная попытка через {delay} секунд.")
                    time.sleep(delay)
                else:
                    self.logger.exception("Исчерпаны попытки получения тредов.")
                    raise
            except Exception as e:
                self.logger.exception(f"Неожиданная ошибка при получении тредов: {e}")
                raise

    def fetch_thread_data(self, num, board="b", max_retries=3, delay=10):
        url = f"{self.BASE_URL}/{board}/res/{num}.json"
        self.logger.info(f"Попытка получить данные треда {num} с {url}")

        for attempt in range(max_retries):
            self.logger.debug(f"Попытка {attempt + 1} из {max_retries} получить данные треда {num}.")
            try:
                response = requests.get(url, headers=self._get_default_headers())
                response.raise_for_status()
                data = response.json()
                self.logger.debug(
                    f"Ответ для треда {num} получен. Ключи: {list(data.keys()) if isinstance(data, dict) else 'не dict'}")

                threads_data = data.get("threads", [])
                if not threads_data:
                    self.logger.warning(f"threads_data отсутствуют или пусты для треда {num}, данные: {data}")
                    return None

                if not isinstance(threads_data, list) or len(threads_data) == 0:
                    self.logger.warning(f"threads_data не список или пуст для треда {num}. data: {data}")
                    return None

                thread_info = threads_data[0]
                posts = thread_info.get("posts", [])
                if not posts:
                    self.logger.warning(
                        f"Посты отсутствуют в треде {num}, thread_info ключи: {list(thread_info.keys())}, data: {data}")
                    return None

                op_post = posts[0]
                op_comment = op_post.get("comment", "Без текста")

                media_urls = []
                files_found = 0
                for post in posts:
                    p_num = post.get("num", "Unknown")
                    files = post.get("files", [])
                    if not isinstance(files, list):
                        self.logger.debug(f"Поле 'files' в посте {p_num} не является списком: {files}")
                        continue
                    for f in files:
                        file_path = f.get("path")
                        if file_path:
                            full_url = f"{self.BASE_URL}{file_path}"
                            media_urls.append(full_url)
                            files_found += 1

                self.logger.info(
                    f"Тред {num} получен: ОП-комментарий длиной {len(op_comment)} символов, медиафайлов: {files_found}")

                return {
                    "caption": op_comment,
                    "media": media_urls
                }
            except requests.exceptions.HTTPError as e:
                self.logger.error(f"HTTP Error при получении треда {num}: {e}")
                if attempt < max_retries - 1:
                    self.logger.info(f"Повторная попытка через {delay} секунд.")
                    time.sleep(delay)
                else:  #
                    self.logger.exception("Исчерпаны попытки получения данных треда {thread_num}.")
                    raise
            except Exception as e:
                self.logger.exception(f"Неожиданная ошибка при обработке данных треда {num}: {e}")
                raise

    #

    def compress_text_by_length(self,text, max_length=5):
        words = text.split()
        word_to_hash = {}
        compressed_text = []

        for word in words:
            if len(word) <= max_length:
                compressed_text.append(word)
            else:
                if word not in word_to_hash:
                    word_to_hash[word] = hashlib.md5(word.encode('utf-8')).hexdigest()[:5]
                compressed_text.append(word_to_hash[word])

        return word_to_hash, " ".join(compressed_text)


    def calculate_saving(original_text, compressed_text):
        return 100 * (1 - len(compressed_text) / len(original_text))

    def _get_default_headers(self):
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": f"{self.BASE_URL}/b/",
            "Accept": "application/json"
        }

