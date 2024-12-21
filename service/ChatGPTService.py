import logging
import os
import aiohttp
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI приложение
app = FastAPI()

# Модель для входящих данных
class UserInput(BaseModel):
    player_message: str  # Сообщение от игрока
    prompt: str          # Контекст (промпт) для ChatGPT

# Класс для взаимодействия с OpenAI API
class ChatGPTClient:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("Переменная окружения OPENAI_API_KEY не задана!")

    async def generate_response(self, messages: List[dict]):
        """
        Генерация ответа на основе списка сообщений.
        :param messages: Список сообщений для ChatGPT.
        :return: Ответ от OpenAI.
        """
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "max_tokens": 2000,
            "temperature": 0.7
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as resp:
                    if resp.status != 200:
                        error = await resp.text()
                        logger.error(f"API запрос не удался: {resp.status} {error}")
                        raise HTTPException(status_code=resp.status, detail="Ошибка при запросе к OpenAI API")
                    result = await resp.json()
                    return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            logger.exception(f"Ошибка при запросе к OpenAI API: {e}")
            raise HTTPException(status_code=500, detail="Произошла ошибка при генерации ответа.")
