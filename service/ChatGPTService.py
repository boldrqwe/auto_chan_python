import aiohttp
import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Модель для валидации входящих данных
class UserInput(BaseModel):
    user_input: str

# Класс для взаимодействия с OpenAI API
class ChatGPTClient:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.prompt_file = "prompt.md"
        try:
            with open(self.prompt_file, 'r', encoding='utf-8') as f:
                self.prompt = f.read()
        except FileNotFoundError:
            logger.error(f"Файл промпта '{self.prompt_file}' не найден.")
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
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "max_tokens": 1000,
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

# Инициализация FastAPI
app = FastAPI()
chat_client = ChatGPTClient()

# Эндпоинт для получения ответа от ChatGPT
@app.post("/chat")
async def chat(user_input: UserInput):
    """
    Эндпоинт для общения с ChatGPT.
    Ожидает JSON с полем `user_input`.
    """
    try:
        response = await chat_client.generate_response(user_input.user_input)
        return {"response": response}
    except HTTPException as e:
        logger.error(f"HTTP Exception: {e.detail}")
        raise e
    except Exception as e:
        logger.exception(f"Unhandled Exception: {e}")
        raise HTTPException(status_code=500, detail="Непредвиденная ошибка на сервере.")
