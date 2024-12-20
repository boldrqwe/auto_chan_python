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
        # Инициализируем состояние игры
        context.user_data['history'] = ["Игра началась."]
        context.user_data['action_mapping'] = {}
        context.user_data['current_action'] = 'default'  # Устанавливаем первое действие

        characteristics = self.command_handler.get_characteristics()
        # Загрузка промпта для начального состояния
        prompt = self.command_handler.load_prompt("exploration")
        user_id = str(update.effective_user.id)  # Получаем ID пользователя
        chat_response = self.command_handler.fetch_chat_response("start", prompt, context.user_data, user_id)

        if not chat_response:
            await update.message.reply_text(
                "Произошла ошибка при получении ответа от игрового мастера.",
            )
            return

        description, buttons, event_picture = self.command_handler.parse_response(chat_response, context.user_data)
        # Отправляем сообщение с характеристиками, описанием и ASCII-артом
        await update.message.reply_text(
            f"{characteristics}\n\n{description}\n\n{event_picture}",
            reply_markup=buttons
        )

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает нажатия на кнопки (CallbackQuery)."""
        query = update.callback_query
        await query.answer()  # Подтверждаем нажатие кнопки
        action_id = query.data

        user_id = str(update.effective_user.id)  # Получаем ID пользователя для логирования

        # Получаем сопоставление действий из user_data
        action_mapping = context.user_data.get('action_mapping', {})
        action_text = action_mapping.get(action_id)

        if not action_text:
            # Если действие не найдено, отправляем сообщение об ошибке
            await query.edit_message_text("Неизвестное действие. Пожалуйста, попробуйте снова.")
            return

        # Добавляем действие в историю
        context.user_data.setdefault('history', []).append(f"Игрок выбрал: {action_text}")

        # Обработка специальных действий
        if action_text == "Инвентарь":
            inventory = self.command_handler.character["inventory"]
            if inventory:
                inventory_items = "\n".join(
                    [f"- {self.command_handler.item_pool[item_id]['name']}" for item_id in inventory]
                )
            else:
                inventory_items = "Ваш инвентарь пуст."
            await query.edit_message_text(f"Ваш инвентарь:\n{inventory_items}")
            # Логирование события
            self.command_handler.log_event(user_id=user_id, action=action_text, response="Просмотр инвентаря")
            return

        if action_text == "Характеристики":
            characteristics = self.command_handler.get_characteristics()
            await query.edit_message_text(f"{characteristics}")
            # Логирование события
            self.command_handler.log_event(user_id=user_id, action=action_text, response="Просмотр характеристик")
            return

        if action_text == "Продолжить":
            # Определяем следующее действие
            next_action = self.command_handler.get_next_action(context.user_data)
            context.user_data['current_action'] = next_action
            prompt = self.command_handler.load_prompt(next_action)
            chat_response = self.command_handler.fetch_chat_response("Продолжить", prompt, context.user_data, user_id)

            if not chat_response:
                await query.edit_message_text(
                    "Произошла ошибка при получении ответа от игрового мастера.",
                )
                # Логирование ошибки
                self.command_handler.log_event(user_id=user_id, action="Продолжить", response="",
                                               error="Empty chat response")
                return

            description, buttons, event_picture = self.command_handler.parse_response(chat_response, context.user_data)
            await query.edit_message_text(
                f"{self.command_handler.get_characteristics()}\n\n{description}\n\n{event_picture}",
                reply_markup=buttons
            )
            # Логирование события
            self.command_handler.log_event(user_id=user_id, action="Продолжить", response=description)
            return

        # Для остальных действий отправляем действие как пользовательский ввод в ChatGPT
        prompt_key = context.user_data.get('current_action', 'default')
        prompt = self.command_handler.load_prompt(prompt_key)

        chat_response = self.command_handler.fetch_chat_response(action_text, prompt, context.user_data, user_id)

        if not chat_response:
            await query.edit_message_text(
                "Произошла ошибка при получении ответа от игрового мастера.",
            )
            # Логирование ошибки
            self.command_handler.log_event(user_id=user_id, action=action_text, response="",
                                           error="Empty chat response")
            return

        description, buttons, event_picture = self.command_handler.parse_response(chat_response, context.user_data)

        # Отправляем ответ игроку с характеристиками, описанием и ASCII-артом
        await query.edit_message_text(
            f"{self.command_handler.get_characteristics()}\n\n{description}\n\n{event_picture}",
            reply_markup=buttons
        )
        # Логирование события
        self.command_handler.log_event(user_id=user_id, action=action_text, response=description)

        # Обновляем следующее действие
        next_action = self.command_handler.get_next_action(context.user_data)
        context.user_data['current_action'] = next_action

