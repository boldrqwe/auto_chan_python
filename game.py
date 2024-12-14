# game.py

import random
from collections import defaultdict
import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
import logging

from service.ChatGPTService import ChatGPTClient

logger = logging.getLogger(__name__)

class RPGGame:
    def __init__(self, bot):
        self.bot = bot  # Экземпляр Telegram Bot
        self.players = {}  # {user_id: {"name": str, "class": str, "stats": dict}}
        self.current_event = {}  # {user_id: event}
        self.world_state = defaultdict(lambda: {"gold": 0, "resources": {}})  # Состояние мира для каждого пользователя
        self.chat_gpt_client = ChatGPTClient(api_key=os.environ.get("OPENAI_API_KEY"), prompt_file="prompt.md")

    async def start_game(self):
        # Асинхронная инициализация игры
        logger.info("Игра инициализирована!")
        # Дополнительная логика инициализации, если необходимо

    async def add_player(self, user_id):
        if user_id in self.players:
            await self.bot.send_message(user_id, "Вы уже добавлены в игру.")
            return

        self.world_state[user_id] = {"gold": 0, "resources": {}}
        self.players[user_id] = {
            "name": f"Player_{user_id}",
            "class": "Новичок",
            "stats": {
                "strength": 5,
                "agility": 5,
                "intelligence": 5,
                "charisma": 5,
                "health": 100,
            },
            "inventory": []
        }
        # Отправляем приветственное сообщение с кнопкой выбора класса
        keyboard = [
            [InlineKeyboardButton("Выбрать класс", callback_data="set_class")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await self.bot.send_message(
            user_id,
            "Игра началась! Вы - единственный игрок. Выберите класс.",
            reply_markup=reply_markup
        )

    async def set_class(self, user_id):
        if user_id not in self.players:
            await self.bot.send_message(user_id, "Сначала начните игру с помощью кнопки /startgame.")
            return

        # Отправляем сообщение с доступными классами
        keyboard = [
            [
                InlineKeyboardButton("Воин", callback_data="class_Воин"),
                InlineKeyboardButton("Лучник", callback_data="class_Лучник")
            ],
            [
                InlineKeyboardButton("Маг", callback_data="class_Маг"),
                InlineKeyboardButton("Разбойник", callback_data="class_Разбойник")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await self.bot.send_message(
            user_id,
            "Выберите класс вашего персонажа:",
            reply_markup=reply_markup
        )

    async def handle_class_selection(self, user_id, player_class):
        self.players[user_id]["class"] = player_class
        await self.bot.send_message(user_id, f"Класс успешно установлен: {player_class}")
        # Генерация вступительного описания с помощью ChatGPT
        intro = await self.chat_gpt_client.generate_response(f"Игрок выбрал класс {player_class}. Опиши его вступление в игру.")
        await self.bot.send_message(user_id, intro)
        # Предлагаем начать исследование мира
        keyboard = [
            [InlineKeyboardButton("Исследовать мир", callback_data="initiate_event")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await self.bot.send_message(
            user_id,
            "Что вы хотите сделать дальше?",
            reply_markup=reply_markup
        )

    async def initiate_event(self, user_id):
        if user_id not in self.players:
            await self.bot.send_message(user_id, "Сначала начните игру с помощью кнопки /startgame.")
            return

        events = [
            "Вы нашли заброшенный храм. Что будете делать?",
            "Вы встретили банду гоблинов. Будете сражаться или убегать?",
            "Перед вами торговец. Хотите поторговать?",
        ]
        event = random.choice(events)
        self.current_event[user_id] = event

        # Определяем варианты действий в зависимости от события
        if "храм" in event:
            options = ["Исследовать храм", "Игнорировать"]
            callback_prefix = "event_hрам"
        elif "гоблинов" in event:
            options = ["Сражаться", "Убегать"]
            callback_prefix = "event_гоблины"
        elif "торговец" in event:
            options = ["Торговать", "Отказаться"]
            callback_prefix = "event_торговец"
        else:
            options = ["Продолжить"]
            callback_prefix = "event_прочее"

        keyboard = [[InlineKeyboardButton(option, callback_data=f"action_{callback_prefix}_{option}")] for option in options]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await self.bot.send_message(user_id, event, reply_markup=reply_markup)

    async def execute_action(self, user_id, action):
        if user_id not in self.players:
            await self.bot.send_message(user_id, "Сначала начните игру с помощью кнопки /startgame.")
            return

        if user_id not in self.current_event or not self.current_event[user_id]:
            await self.bot.send_message(user_id, "Нет активных событий. Инициируйте событие с помощью кнопки \"Исследовать мир\".")
            return

        # Пример реализации действий
        outcomes = {
            "Исследовать храм": "Вы решили исследовать храм и нашли сокровищницу с золотом!",
            "Игнорировать": "Вы решили игнорировать храм и продолжить путь.",
            "Сражаться": "Вы вступили в бой с гоблинами и победили их, но потеряли немного здоровья.",
            "Убегать": "Вы успешно убежали от гоблинов, но потеряли немного золота.",
            "Торговать": "Вы обменяли часть ресурсов на полезные предметы у торговца.",
            "Отказаться": "Вы решили отказаться от торговли и продолжить путь.",
            "Продолжить": "Вы продолжили своё путешествие."
        }
        outcome = outcomes.get(action, "Ничего не произошло. Попробуйте другое действие.")

        # Пример изменения состояния
        if action == "Исследовать храм":
            gold_found = random.randint(10, 50)
            self.world_state[user_id]["gold"] += gold_found
            outcome += f" Вы нашли {gold_found} золотых."
        elif action == "Сражаться":
            damage = random.randint(5, 15)
            self.players[user_id]["stats"]["health"] -= damage
            outcome += f" Вы потеряли {damage} здоровья."
        elif action == "Убегать":
            gold_lost = random.randint(5, 20)
            self.world_state[user_id]["gold"] = max(0, self.world_state[user_id]["gold"] - gold_lost)
            outcome += f" Вы потеряли {gold_lost} золотых."
        elif action == "Торговать":
            # Пример торговли: добавление предмета в инвентарь
            item = random.choice(["Меч", "Щит", "Зелье здоровья", "Лук"])
            self.players[user_id]["inventory"].append(item)
            outcome += f" Вы получили предмет: {item}."

        # Генерация описания исхода действия с помощью ChatGPT
        detailed_outcome = await self.chat_gpt_client.generate_response(outcome)
        await self.bot.send_message(user_id, detailed_outcome)
        self.current_event[user_id] = None

        # Предлагаем продолжить исследование или завершить
        keyboard = [
            [InlineKeyboardButton("Исследовать мир", callback_data="initiate_event")],
            [InlineKeyboardButton("Показать статистику", callback_data="show_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await self.bot.send_message(
            user_id,
            "Что вы хотите сделать дальше?",
            reply_markup=reply_markup
        )

    async def show_stats(self, user_id):
        if user_id not in self.players:
            await self.bot.send_message(user_id, "Вы ещё не добавились в игру. Используйте кнопку /startgame для начала.")
            return

        player = self.players[user_id]
        stats_message = (
            f"Ваши характеристики:\n"
            f"Имя: {player['name']}\n"
            f"Класс: {player['class']}\n"
            f"Здоровье: {player['stats']['health']}\n"
            f"Сила: {player['stats']['strength']}\n"
            f"Ловкость: {player['stats']['agility']}\n"
            f"Интеллект: {player['stats']['intelligence']}\n"
            f"Харизма: {player['stats']['charisma']}\n"
            f"Общее золото: {self.world_state[user_id]['gold']}\n"
            f"Инвентарь: {', '.join(player['inventory']) if player['inventory'] else 'Пусто'}"
        )
        await self.bot.send_message(user_id, stats_message)

    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Извините, я не понимаю эту команду.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text
        # Здесь можно добавить логику обработки свободного текста, если необходимо
        await update.message.reply_text("Используйте кнопки для взаимодействия с игрой.")

    # Callback Query Handlers
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data

        await query.answer()  # Подтверждаем получение callback-запроса

        if data == "set_class":
            await self.set_class(user_id)
        elif data.startswith("class_"):
            player_class = data.split("_", 1)[1]
            await self.handle_class_selection(user_id, player_class)
        elif data == "initiate_event":
            await self.initiate_event(user_id)
        elif data.startswith("action_"):
            # Извлекаем действие из callback_data
            parts = data.split("_", 2)
            if len(parts) >= 3:
                action = parts[2]
                await self.execute_action(user_id, action)
        elif data == "show_stats":
            await self.show_stats(user_id)
        else:
            await self.bot.send_message(user_id, "Неизвестное действие. Пожалуйста, используйте доступные кнопки.")

    def register_handlers(self, application):
        """Регистрация обработчиков команд и callback-запросов в приложении."""
        application.add_handler(CommandHandler("startgame", self.start_game_command))
        application.add_handler(CallbackQueryHandler(self.handle_callback_query))
        application.add_handler(MessageHandler(filters.COMMAND, self.unknown_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_game_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        await self.add_player(user_id)

