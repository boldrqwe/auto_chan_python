import openai
import os

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

    def generate_response(self) -> str:
        try:
            prompt = self.read_prompt()  # Чтение промта из файла
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )
            return response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"Ошибка при генерации ответа: {e}"

