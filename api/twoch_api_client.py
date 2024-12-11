import requests
import logging

class TwoCHApiClient:
    def __init__(self, base_url="https://2ch.hk"):
        self.base_url = base_url.rstrip('/')
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_boards(self):
        url = f"{self.base_url}/api/mobile/v2/boards"
        self.logger.info(f"Запрос списка досок: {url}")
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        self.logger.debug(f"Ответ на get_boards: ключи {list(data.keys()) if isinstance(data, dict) else 'не dict'}")
        return data

    def get_thread_posts_after(self, board: str, thread_id: int, post_num: int):
        url = f"{self.base_url}/api/mobile/v2/after/{board}/{thread_id}/{post_num}"
        self.logger.info(f"Запрос постов после {post_num} в треде {thread_id} на доске {board}: {url}")
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        self.logger.debug(f"Ответ keys: {list(data.keys()) if isinstance(data, dict) else 'не dict'}")
        return data

    def get_thread_info(self, board: str, thread_id: int):
        url = f"{self.base_url}/api/mobile/v2/info/{board}/{thread_id}"
        self.logger.info(f"Запрос информации о треде {thread_id} на доске {board}: {url}")
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        self.logger.debug(f"Ответ keys: {list(data.keys()) if isinstance(data, dict) else 'не dict'}")
        return data

    def get_post(self, board: str, post_num: int):
        url = f"{self.base_url}/api/mobile/v2/post/{board}/{post_num}"
        self.logger.info(f"Запрос поста {post_num} на доске {board}: {url}")
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        self.logger.debug(f"Ответ keys: {list(data.keys()) if isinstance(data, dict) else 'не dict'}")
        return data

    def get_captcha_id(self, board: str = None, thread_id: int = None):
        url = f"{self.base_url}/api/captcha/emoji/id"
        self.logger.info(f"Запрос captcha_id board={board}, thread={thread_id}: {url}")
        params = {}
        if board:
            params['board'] = board
        if thread_id:
            params['thread'] = thread_id
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        self.logger.debug(f"Ответ keys: {list(data.keys()) if isinstance(data, dict) else 'не dict'}")
        return data

    def show_emoji_captcha(self, captcha_id: str):
        url = f"{self.base_url}/api/captcha/emoji/show"
        self.logger.info(f"Запрос состояния emoji капчи {captcha_id}: {url}")
        params = {'id': captcha_id}
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        self.logger.debug(f"Ответ keys: {list(data.keys()) if isinstance(data, dict) else 'не dict'}")
        return data

    def click_emoji_captcha(self, captchaTokenID: str, emojiNumber: int):
        url = f"{self.base_url}/api/captcha/emoji/click"
        self.logger.info(f"Клик по emoji капче captchaTokenID={captchaTokenID}, emojiNumber={emojiNumber}: {url}")
        payload = {
            "captchaTokenID": captchaTokenID,
            "emojiNumber": emojiNumber
        }
        r = requests.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        self.logger.debug(f"Ответ keys: {list(data.keys()) if isinstance(data, dict) else 'не dict'}")
        return data

    def get_app_id(self, public_key: str, board: str = None, thread_id: int = None):
        url = f"{self.base_url}/api/captcha/app/id/{public_key}"
        self.logger.info(f"Запрос app_id public_key={public_key}, board={board}, thread={thread_id}: {url}")
        params = {}
        if board:
            params['board'] = board
        if thread_id:
            params['thread'] = thread_id
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        self.logger.debug(f"Ответ keys: {list(data.keys()) if isinstance(data, dict) else 'не dict'}")
        return data

    def create_post(self, board: str, captcha_type: str, comment: str,
                    thread_id: int = None, files: list = None,
                    name: str = None, email: str = None, subject: str = None):
        url = f"{self.base_url}/user/posting"
        self.logger.info(f"Создание поста на доске {board}, thread_id={thread_id}, captcha_type={captcha_type}: {url}")
        data = {
            "captcha_type": captcha_type,
            "board": board,
            "comment": comment
        }
        if thread_id:
            data["thread"] = str(thread_id)
        if name:
            data["name"] = name
        if email:
            data["email"] = email
        if subject:
            data["subject"] = subject

        files_payload = []
        if files:
            for f in files:
                self.logger.debug(f"Прикрепляем файл {f} к посту.")
                files_payload.append(('file[]', (f, open(f, 'rb'))))

        r = requests.post(url, data=data, files=files_payload if files else None)
        r.raise_for_status()
        response_data = r.json()
        self.logger.debug(f"Ответ на создание поста keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'не dict'}")
        return response_data
