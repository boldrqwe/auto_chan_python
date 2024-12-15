import os  # Добавьте этот импорт
from multiprocessing import Process
import asyncio
from app.main import app  # Ваше FastAPI приложение
from bot import application  # Ваш Telegram бот
import uvicorn

def start_fastapi():
    """Запуск FastAPI сервера."""
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

def start_bot():
    """Запуск Telegram-бота."""
    asyncio.run(application.run_polling())

if __name__ == "__main__":
    # Создаём два процесса для запуска FastAPI и бота
    process_api = Process(target=start_fastapi)
    process_bot = Process(target=start_bot)

    process_api.start()
    process_bot.start()