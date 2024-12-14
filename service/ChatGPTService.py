import aiohttp
import os
import logging

logger = logging.getLogger(__name__)

class ChatGPTClient:
    def __init__(self, api_key, prompt_file):
        self.api_key = api_key
        self.prompt_file = prompt_file
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                self.prompt = f.read()
        except FileNotFoundError:
            logger.error(f"Файл промпта '{prompt_file}' не найден.")
            self.prompt = ""

    async def generate_response(self, user_input=None):
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = [{"role": "system", "content": self.prompt}]
        if user_input:
            messages.append({"role": "user", "content": user_input})

        data = {
            "model": "gpt-4",
            "messages": messages,
            "max_tokens": 500,
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
            return "Произошла ошибка при генерации ответа."
