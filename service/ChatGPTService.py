import openai
import os
import re

# Настройки OpenAI API
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Класс для работы с OpenAI ChatGPT
class ChatGPTClient:
    def __init__(self, api_key: str, prompt_file: str = "prompt.md"):
        self.api_key = api_key
        openai.api_key = api_key
        self.prompt_file = prompt_file

    def read_prompt(self) -> str:
        """Чтение содержимого файла с промтом."""
        if not os.path.exists(self.prompt_file):
            raise FileNotFoundError(f"Файл {self.prompt_file} не найден.")
        with open(self.prompt_file, "r", encoding="utf-8") as file:
            return file.read().strip()

    def clean_prompt(self, prompt: str) -> str:
        """Очистка текста промта от лишних символов и отступов."""
        # Удаляем лишние пробелы, табуляции и пустые строки
        prompt = re.sub(r"\s+", " ", prompt)  # Убираем лишние пробелы между словами
        prompt = prompt.replace("\n", " ")      # Убираем переносы строк
        prompt = re.sub(r"\s{2,}", " ", prompt) # Убираем дублирующиеся пробелы
        return prompt.strip()

    def generate_response(self) -> str:
        try:
            raw_prompt = self.read_prompt()        # Чтение промта из файла
            cleaned_prompt = self.clean_prompt(raw_prompt)  # Очистка промта

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": cleaned_prompt}],
                max_tokens=800,
                temperature=0.7
            )
            return response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"Ошибка при генерации ответа: {e}"

