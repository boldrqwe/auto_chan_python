import os
import logging
from collections import defaultdict
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from service.ChatGPTService import ChatGPTClient

logger = logging.getLogger(__name__)

class RPGGame:
    def __init__(self, bot):
        self.bot = bot
        self.players = {}  # {user_id: {...}}
        self.world_state = defaultdict(lambda: {"gold": 0, "resources": {}})
        self.chat_gpt_client = ChatGPTClient(api_key=os.environ.get("OPENAI_API_KEY"), prompt_file="prompt.md")
        self.user_custom_command = {}

    async def start_game(self):
        logger.info("Игра инициализирована!")

    async def add_player(self, user_id, player_name):
        if user_id in self.players:
            await self.bot.send_message(user_id, "Вы уже добавлены в игру.")
            return

        self.players[user_id] = {
            "name": player_name,
            "class": "Новичок",
            "stats": {
                "strength": 5,
                "agility": 5,
                "intelligence": 5,
                "charisma": 5,
                "health": 100,
                "stamina": 50,
                "magic": 10
            },
            "inventory": []
        }
        self.world_state[user_id] = {"gold": 0, "resources": {}}
        self.user_custom_command[user_id] = None

        await self.update_scene(user_id, "Игрок только что начал игру, он выбрал имя.")

    async def update_scene(self, user_id, additional_message: str):
        prompt_context = self.build_context(user_id)
        user_input = prompt_context + "\n" + additional_message
        response = await self.chat_gpt_client.generate_response(user_input=user_input)
        description, actions = self.parse_response(response)
        await self.send_scenario(user_id, description, actions)

    def build_context(self, user_id):
        if user_id not in self.players:
            return "Игрок ещё не существует."
        player = self.players[user_id]
        gold = self.world_state[user_id]["gold"]
        inv = player["inventory"]
        stats = player["stats"]
        custom_cmd = self.user_custom_command.get(user_id, None)
        custom_part = f"Произвольная команда игрока: {custom_cmd}" if custom_cmd else ""

        return (
            f"Имя игрока: {player['name']}\n"
            f"Класс: {player['class']}\n"
            f"Здоровье: {stats['health']}\n"
            f"Стамина: {stats['stamina']}\n"
            f"Магия: {stats['magic']}\n"
            f"Сила: {stats['strength']}\n"
            f"Ловкость: {stats['agility']}\n"
            f"Интеллект: {stats['intelligence']}\n"
            f"Харизма: {stats['charisma']}\n"
            f"Золото: {gold}\n"
            f"Инвентарь: {', '.join(inv) if inv else 'пусто'}\n"
            f"{custom_part}"
        )

    def parse_response(self, response_text: str):
        desc_block = self.extract_block(response_text, "[DESCRIPTION]", "[DESCRIPTION_END]")
        actions_block = self.extract_block(response_text, "[ACTIONS]", "[ACTIONS_END]")

        description = desc_block.strip() if desc_block else "Сцена не описана."
        actions = self.parse_actions(actions_block)
        return description, actions

    def extract_block(self, text: str, start_tag: str, end_tag: str):
        start_idx = text.find(start_tag)
        end_idx = text.find(end_tag)
        if start_idx == -1 or end_idx == -1:
            return ""
        return text[start_idx+len(start_tag):end_idx].strip()

    def parse_actions(self, actions_text: str):
        if not actions_text:
            return []
        actions = []
        for line in actions_text.split("\n"):
            line = line.strip()
            if line:
                actions.append(line)
        return actions

    async def send_scenario(self, user_id, description: str, actions: list):
        if not actions:
            actions = ["Продолжить"]
        keyboard = [[InlineKeyboardButton(a, callback_data=f"choice_{a}")] for a in actions]
        await self.bot.send_message(user_id, description, reply_markup=InlineKeyboardMarkup(keyboard))

    async def process_choice(self, user_id, choice: str):
        logger.info(f"Пользователь {user_id} выбрал действие: {choice}")

        lower_choice = choice.lower()

        if lower_choice.startswith("действие"):
            # Произвольная команда
            self.user_custom_command[user_id] = None
            await self.bot.send_message(user_id, "Введите произвольную команду:")
            return
        elif lower_choice == "инвентарь":
            # Показываем инвентарь сразу или обновляем сцену
            # Здесь можно просто вывести текущее содержимое инвентаря:
            inv = self.players[user_id]["inventory"]
            inv_text = "Инвентарь пуст." if not inv else "Инвентарь: " + ", ".join(inv)
            # Можно напрямую отправить сообщение или снова обратиться к ChatGPT для красивого описания
            await self.update_scene(user_id, f"Игрок просматривает инвентарь: {inv_text}")
            return
        elif lower_choice == "характеристики":
            # Аналогично для характеристик
            player = self.players[user_id]
            stats = player["stats"]
            char_text = (
                f"Имя: {player['name']}\n"
                f"Класс: {player['class']}\n"
                f"Здоровье: {stats['health']}\n"
                f"Стамина: {stats['stamina']}\n"
                f"Магия: {stats['magic']}\n"
                f"Сила: {stats['strength']}\n"
                f"Ловкость: {stats['agility']}\n"
                f"Интеллект: {stats['intelligence']}\n"
                f"Харизма: {stats['charisma']}"
            )
            await self.update_scene(user_id, f"Игрок просматривает характеристики:\n{char_text}")
            return
        else:
            # Для всех остальных вариантов просто обновляем сцену через ChatGPT
            await self.update_scene(user_id, f"Игрок выбрал действие: {choice}. Опиши, что происходит дальше.")

    async def handle_custom_command(self, user_id, text):
        self.user_custom_command[user_id] = text
        await self.update_scene(user_id, f"Игрок ввёл произвольную команду: {text}. Учти это при развитии сюжета.")

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data
        await query.answer()

        if data.startswith("choice_"):
            choice = data[len("choice_"):].strip()
            await self.process_choice(user_id, choice)

    async def start_game_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        await self.bot.send_message(user_id, "Введите имя вашего персонажа:")

    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Неизвестная команда. Используйте /startgame для начала.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text.strip()

        if user_id not in self.players:
            # Ввод имени игрока
            await self.add_player(user_id, text)
            return

        # Если ждём произвольную команду
        if user_id in self.players and self.user_custom_command.get(user_id, "not_set") is None:
            await self.handle_custom_command(user_id, text)
        else:
            await update.message.reply_text("Используйте кнопки для взаимодействия или /startgame для начала.")

    def register_handlers(self, application):
        application.add_handler(CommandHandler("startgame", self.start_game_command))
        application.add_handler(CallbackQueryHandler(self.handle_callback_query))
        application.add_handler(MessageHandler(filters.COMMAND, self.unknown_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))


