
import requests
import logging
import time

class DvachService:
    BASE_URL = "https://2ch.hk"

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def fetch_threads(self, board="b", max_retries=3, delay=6):
        url = f"{self.BASE_URL}/{board}/threads.json"
        self.logger.info(f"Попытка получить список тредов с {url}")

        for attempt in range(max_retries):
            self.logger.debug(f"Попытка {attempt+1} из {max_retries} получить треды.")
            try:
                response = requests.get(url)
                response.raise_for_status()
                data_json = response.json()
                self.logger.debug(f"Ответ получен. Ключи: {list(data_json.keys()) if isinstance(data_json, dict) else 'не dict'}")
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
            self.logger.debug(f"Попытка {attempt+1} из {max_retries} получить данные треда {num}.")
            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                self.logger.debug(f"Ответ для треда {num} получен. Ключи: {list(data.keys()) if isinstance(data, dict) else 'не dict'}")

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
                    self.logger.warning(f"Посты отсутствуют в треде {num}, thread_info ключи: {list(thread_info.keys())}, data: {data}")
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

                self.logger.info(f"Тред {num} получен: ОП-комментарий длиной {len(op_comment)} символов, медиафайлов: {files_found}")

                return {
                    "caption": op_comment,
                    "media": media_urls
                }
            except requests.exceptions.HTTPError as e:
                self.logger.error(f"HTTP Error при получении треда {num}: {e}")
                if attempt < max_retries - 1:
                    self.logger.info(f"Повторная попытка через {delay} секунд.")
                    time.sleep(delay)
                else:#
                    self.logger.exception("Исчерпаны попытки получения данных треда {thread_num}.")
                    raise
            except Exception as e:
                self.logger.exception(f"Неожиданная ошибка при обработке данных треда {num}: {e}")
                raise
#