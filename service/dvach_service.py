import logging
import time

from api.twoch_api_client import TwoCHApiClient

class DvachService:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.api_client = TwoCHApiClient()

    def fetch_threads(self, board_name="b", retry_limit=3, retry_delay_seconds=6):
        for retry_attempt in range(retry_limit):
            try:
                self.logger.info(f"Попытка получить список тредов на доске {board_name}.")
                data = self.api_client.get_boards()
                threads = next((board["threads"] for board in data.get("boards", []) if board["id"] == board_name), [])
                self.logger.info(f"Получено тредов: {len(threads)}")
                return threads
            except Exception as e:
                self.logger.exception(f"Ошибка при получении списка тредов: {e}")
                if retry_attempt < retry_limit - 1:
                    self.logger.info(f"Повторная попытка через {retry_delay_seconds} секунд.")
                    time.sleep(retry_delay_seconds)
                else:
                    self.logger.error("Исчерпаны попытки получения тредов.")
                    raise

    def fetch_thread_data(self, thread_id, board_name="b", retry_limit=3, retry_delay_seconds=10):
        for retry_attempt in range(retry_limit):
            try:
                self.logger.info(f"Попытка получить данные треда {thread_id} на доске {board_name}.")
                thread_info = self.api_client.get_thread_info(board=board_name, thread_id=thread_id)
                post_list = thread_info.get("posts", [])

                if not post_list:
                    self.logger.warning(f"Посты отсутствуют в треде {thread_id} на доске {board_name}.")
                    return None

                op_post_data = post_list[0]
                op_comment_text = op_post_data.get("comment", "Без текста")

                media_url_list = []
                for post_data in post_list:
                    attached_files = post_data.get("files", [])
                    for file_metadata in attached_files:
                        file_path = file_metadata.get("path")
                        if file_path:
                            media_url_list.append(f"{self.api_client.base_url}{file_path}")

                self.logger.info(f"Тред {thread_id} получен: ОП-комментарий длиной {len(op_comment_text)} символов, медиафайлов: {len(media_url_list)}")

                return {
                    "caption": op_comment_text,
                    "media": media_url_list
                }
            except Exception as e:
                self.logger.exception(f"Ошибка при получении данных треда {thread_id}: {e}")
                if retry_attempt < retry_limit - 1:
                    self.logger.info(f"Повторная попытка через {retry_delay_seconds} секунд.")
                    time.sleep(retry_delay_seconds)
                else:
                    self.logger.error("Исчерпаны попытки получения данных треда.")
                    raise
