import asyncio
import logging
import os
import tempfile
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ApplicationBuilder, ContextTypes

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

# Flask для health-check
app = Flask(__name__)

# Загрузка переменных окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "-1002162401416")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_API_ENDPOINT = "https://api.openai.com/v1/images/generations"
POST_INTERVAL = int(os.environ.get("TELEGRAM_POST_INTERVAL", "40"))
FETCH_BATCH_SIZE = int(os.environ.get("FETCH_BATCH_SIZE", "1"))
FETCH_DELAY = int(os.environ.get("FETCH_DELAY", "40"))

# Проверка переменных окружения
required_vars = ["BOT_TOKEN", "TELEGRAM_CHANNEL_ID", "OPENAI_API_KEY"]
missing = [var for var in required_vars if not globals().get(var)]
if missing:
    raise ValueError(f"Не заданы переменные окружения: {', '.join(missing)}")
logger.info(", ".join(f"{var}: {globals().get(var)}" for var in required_vars + ["POST_INTERVAL", "FETCH_BATCH_SIZE", "FETCH_DELAY"]))

# Инициализация объектов
application = ApplicationBuilder().token(BOT_TOKEN).build()
bot = application.bot

# Telegram обработчики
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправьте мне картинку и текст для создания комикса.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        image_path = tmp_file.name
        await photo_file.download_to_drive(image_path)

    caption = update.message.caption or ""
    logger.info("Отправка изображения и текста в OpenAI")
    response = requests.post(
        OPENAI_API_ENDPOINT,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "prompt": caption,
            "n": 1,
            "size": "1024x1024"
        }
    )
    result = response.json()
    if "error" in result:
        await update.message.reply_text(f"Ошибка: {result['error']}")
    else:
        await update.message.reply_text(f"Ваш комикс: {result['data'][0]['url']}")
    os.remove(image_path)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправьте мне картинку вместе с текстом для создания комикса!")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

@app.route('/')
def health_check():
    return "Бот работает!"

if __name__ == "__main__":
    def run_telegram_bot():
        loop = asyncio.new_event_loop()  # Создаем новый цикл событий
        asyncio.set_event_loop(loop)  # Устанавливаем его в текущем потоке
        loop.run_until_complete(application.run_polling())

    telegram_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    telegram_thread.start()

    from gevent.pywsgi import WSGIServer
    logger.info("Запуск Flask-сервера...")
    try:
        http_server = WSGIServer(('0.0.0.0', 5000), app)
        http_server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Остановка сервера...")
        application.shutdown()  # Завершение работы Telegram-бота
        http_server.stop()


