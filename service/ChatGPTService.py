# service/ChatGPTService.py

import logging

import aiohttp

logger = logging.getLogger(__name__)


class ChatGPTClient:
    def __init__(self, api_key, prompt_file):
        self.api_key = api_key
        self.prompt_file = prompt_file
        # Загрузка промпта из файла
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                self.prompt = f.read()
        except FileNotFoundError:
            logger.error(f"Файл промпта '{prompt_file}' не найден.")
            self.prompt = ""

    async def generate_response(self, user_input=None):
        url = "https://api.openai.com/v1/chat/completions"  # Убедитесь, что URL актуален
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-4",  # Проверьте, что используете правильную модель
            "messages": [
                {"role": "system", "content": self.prompt}
            ] if not user_input else [
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": user_input}
            ],
            "max_tokens": 150,
            "temperature": 0.7
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as resp:
                    if resp.status != 200:
                        error = await resp.text()
                        logger.error(f"API запрос не удался с кодом {resp.status}: {error}")
                        raise Exception(f"API запрос не удался с кодом {resp.status}: {error}")
                    result = await resp.json()
                    return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            logger.exception(f"Ошибка при запросе к API OpenAI: {e}")
            return "Произошла ошибка при генерации анекдота."
