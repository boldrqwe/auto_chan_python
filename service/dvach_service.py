import requests
import logging
import time

class DvachService:
    BASE_URL = "https://2ch.hk"

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def fetch_threads(self, board_name="b", retry_limit=3, retry_delay_seconds=6):
        threads_url = f"{self.BASE_URL}/{board_name}/threads.json"
        self.logger.info(f"Попытка получить список тредов с {threads_url}")

        for retry_attempt in range(retry_limit):
            self.logger.debug(f"Попытка {retry_attempt + 1} из {retry_limit} получить треды.")
            try:
                response = requests.get(threads_url)
                response.raise_for_status()
                threads_data = response.json()
                self.logger.debug(f"Ответ получен. Ключи: {list(threads_data.keys()) if isinstance(threads_data, dict) else 'не dict'}")
                thread_list = threads_data.get("threads", [])
                self.logger.info(f"Получено тредов: {len(thread_list)}")
                return thread_list
            except requests.exceptions.HTTPError as http_error:
                self.logger.error(f"HTTP Error при получении тредов с {threads_url}: {http_error}")
                if retry_attempt < retry_limit - 1:
                    self.logger.info(f"Повторная попытка через {retry_delay_seconds} секунд.")
                    time.sleep(retry_delay_seconds)
                else:
                    self.logger.exception("Исчерпаны попытки получения тредов.")
                    raise
            except Exception as unexpected_error:
                self.logger.exception(f"Неожиданная ошибка при получении тредов: {unexpected_error}")
                raise

    def fetch_thread_data(self, thread_id, board_name="b", retry_limit=3, retry_delay_seconds=10):
        thread_url = f"{self.BASE_URL}/{board_name}/res/{thread_id}.json"
        self.logger.info(f"Попытка получить данные треда {thread_id} с {thread_url}")

        for retry_attempt in range(retry_limit):
            self.logger.debug(f"Попытка {retry_attempt + 1} из {retry_limit} получить данные треда {thread_id}.")
            try:
                response = requests.get(thread_url)
                response.raise_for_status()
                thread_data = response.json()
                self.logger.debug(f"Ответ для треда {thread_id} получен. Ключи: {list(thread_data.keys()) if isinstance(thread_data, dict) else 'не dict'}")

                threads_info = thread_data.get("threads", [])
                if not threads_info:
                    self.logger.warning(f"Информация о тредах отсутствует или пуста для треда {thread_id}, данные: {thread_data}")
                    return None

                if not isinstance(threads_info, list) or len(threads_info) == 0:
                    self.logger.warning(f"threads_info не список или пуст для треда {thread_id}. data: {thread_data}")
                    return None

                thread_metadata = threads_info[0]
                post_list = thread_metadata.get("posts", [])
                if not post_list:
                    self.logger.warning(f"Посты отсутствуют в треде {thread_id}, ключи thread_metadata: {list(thread_metadata.keys())}, данные: {thread_data}")
                    return None

                op_post_data = post_list[0]
                op_comment_text = op_post_data.get("comment", "Без текста")

                media_url_list = []
                total_files_found = 0
                for post_data in post_list:
                    post_number = post_data.get("num", "Unknown")
                    attached_files = post_data.get("files", [])
                    if not isinstance(attached_files, list):
                        self.logger.debug(f"Поле 'files' в посте {post_number} не является списком: {attached_files}")
                        continue
                    for file_metadata in attached_files:
                        file_path = file_metadata.get("path")
                        if file_path:
                            full_file_url = f"{self.BASE_URL}{file_path}"
                            media_url_list.append(full_file_url)
                            total_files_found += 1

                self.logger.info(f"Тред {thread_id} получен: ОП-комментарий длиной {len(op_comment_text)} символов, медиафайлов: {total_files_found}")

                return {
                    "caption": op_comment_text,
                    "media": media_url_list
                }
            except requests.exceptions.HTTPError as http_error:
                self.logger.error(f"HTTP Error при получении треда {thread_id}: {http_error}")
                if retry_attempt < retry_limit - 1:
                    self.logger.info(f"Повторная попытка через {retry_delay_seconds} секунд.")
                    time.sleep(retry_delay_seconds)
                else:
                    self.logger.exception(f"Исчерпаны попытки получения данных треда {thread_id}.")
                    raise
            except Exception as unexpected_error:
                self.logger.exception(f"Неожиданная ошибка при обработке данных треда {thread_id}: {unexpected_error}")
                raise
