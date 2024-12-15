from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from game_service.rpg_command_handler import RPGGameCommandHandler


class RPGGameBot:
    """Класс для интеграции Telegram-бота с игрой."""
    def __init__(self):
        self.command_handler = RPGGameCommandHandler()

    def register_handlers(self, application: Application):
        """Регистрируем хэндлеры."""
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CallbackQueryHandler(self.handle_callback_query))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду /start."""
        characteristics = self.command_handler.get_characteristics()
        # Загрузка промпта для начального состояния
        prompt = self.command_handler.load_prompt("default")
        chat_response = self.command_handler.fetch_chat_response("start", prompt)

        description, buttons, event_picture = self.command_handler.parse_response(chat_response)
        # Отправляем сообщение с характеристиками, описанием и ASCII-артом
        await update.message.reply_text(f"{characteristics}\n\n{description}\n\n{event_picture}", reply_markup=buttons)

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает нажатия на кнопки (CallbackQuery)."""
        query = update.callback_query
        await query.answer()  # Подтверждаем нажатие кнопки
        player_message = query.data

        # Маппинг действий на промпты
        action_prompts = {
            "Атаковать": "combat",
            "Торговать": "trading",
            "Получить скиллы": "gain_skills",
            "Положить в инвентарь": "add_to_inventory",
        }

        # Если пользователь выбрал "Посмотреть характеристики" или "Инвентарь"
        if player_message == "Посмотреть характеристики":
            characteristics = self.command_handler.get_characteristics()
            await query.edit_message_text(f"{characteristics}")
            return

        if player_message == "Инвентарь":
            inventory = self.command_handler.character["inventory"]
            if inventory:
                inventory_items = "\n".join(
                    [f"- {self.command_handler.item_pool[item_id]['name']}" for item_id in inventory]
                )
            else:
                inventory_items = "Ваш инвентарь пуст."
            await query.edit_message_text(f"Ваш инвентарь:\n{inventory_items}")
            return

        # Для остальных действий загружаем промпт и идём в ChatGPT
        prompt_key = action_prompts.get(player_message, "default")
        prompt = self.command_handler.load_prompt(prompt_key)

        chat_response = self.command_handler.fetch_chat_response(player_message, prompt)
        description, buttons, event_picture = self.command_handler.parse_response(chat_response)

        # Отправляем ответ игроку с характеристиками, описанием и ASCII-артом
        await query.edit_message_text(f"{self.command_handler.get_characteristics()}\n\n{description}\n\n{event_picture}",
                                      reply_markup=buttons)
