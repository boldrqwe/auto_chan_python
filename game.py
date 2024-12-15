import logging

from game_service.player_manager import PlayerManager
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters

from game_service.scene_manager import SceneManager

logger = logging.getLogger(__name__)


class RPGGame:
    def __init__(self, bot):
        self.bot = bot
        self.players = PlayerManager()
        self.scene_manager = SceneManager()
        self.user_actions = {}  # {user_id: [action_list]}

    async def update_scene(self, user_id, additional_message: str):
        if not self.players.exists(user_id):
            await self.bot.send_message(user_id, "Вы не начали игру. Используйте /startgame.")
            return

        prompt_context = self.players.build_context(user_id)
        user_input = prompt_context + "\n" + additional_message
        description, actions = await self.scene_manager.generate_scene(user_input)
        await self.send_scenario(user_id, description, actions)

    async def add_player(self, user_id, player_name):
        if self.players.exists(user_id):
            await self.bot.send_message(user_id, "Вы уже добавлены в игру.")
            return

        self.players.add_player(user_id, player_name)
        await self.update_scene(user_id, "Игрок только что начал игру, он выбрал имя.")

    async def send_scenario(self, user_id, description: str, actions: list):
        if not actions:
            actions = ["Продолжить"]

        self.user_actions[user_id] = actions
        keyboard = [[InlineKeyboardButton(action, callback_data=f"act_{i}")] for i, action in enumerate(actions)]
        await self.bot.send_message(user_id, description, parse_mode="Markdown",
                                    reply_markup=InlineKeyboardMarkup(keyboard))

    async def process_choice(self, user_id, choice: str):
        logger.info(f"Пользователь {user_id} выбрал действие: {choice}")

        if choice.lower().startswith("действие"):
            await self.bot.send_message(user_id, "Введите произвольную команду:")
        elif choice.lower() == "инвентарь":
            inventory = self.players.get_inventory(user_id)
            await self.update_scene(user_id, f"Игрок просматривает инвентарь: {inventory}")
        elif choice.lower() == "характеристики":
            stats = self.players.get_stats(user_id)
            await self.update_scene(user_id, f"Игрок просматривает характеристики:\n{stats}")
        else:
            await self.update_scene(user_id, f"Игрок выбрал действие: {choice}. Опиши, что происходит дальше.")

    async def handle_callback_query(self, update: Update, context):
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data
        await query.answer()

        if data.startswith("act_"):
            idx = int(data[len("act_"):])
            actions = self.user_actions.get(user_id, [])
            if idx < len(actions):
                await self.process_choice(user_id, actions[idx])
            else:
                await self.bot.send_message(user_id, "Некорректный выбор.")

    async def start_game_command(self, update: Update, context):
        user_id = update.effective_user.id
        await self.bot.send_message(user_id, "Введите имя вашего персонажа:")

    async def handle_message(self, update: Update, context):
        user_id = update.effective_user.id
        text = update.message.text.strip()

        if not self.players.exists(user_id):
            await self.add_player(user_id, text)
        else:
            await self.bot.send_message(user_id, "Используйте кнопки для взаимодействия или /startgame для начала.")

    async def unknown_command(self, update: Update, context):
        await update.message.reply_text("Неизвестная команда. Используйте /startgame для начала.")

    def register_handlers(self, application):
        application.add_handler(CommandHandler("startgame", self.start_game_command))
        application.add_handler(CallbackQueryHandler(self.handle_callback_query))
        application.add_handler(MessageHandler(filters.COMMAND, self.unknown_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
