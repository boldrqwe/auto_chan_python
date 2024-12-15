import random
import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)
from service.ChatGPTService import ChatGPTClient


class SceneManager:
    def __init__(self):
        self.chat_gpt_client = ChatGPTClient()
        self.user_actions = {}  # {user_id: [action_list]}

    async def update_scene(self, user_id, context, additional_message):
        """
        Updates the game scene by generating a new description and actions from ChatGPT.
        """
        prompt_context = self.build_context(context)
        user_input = f"{prompt_context}\n{additional_message}"

        try:
            response = await self.chat_gpt_client.generate_response(user_input=user_input)
            description, actions = self.parse_response(response)
            return description, actions
        except Exception as e:
            logger.error(f"Ошибка при обновлении сцены: {e}")
            return "Сцена не описана.", ["Продолжить"]

    def build_context(self, context):
        """
        Builds a textual context for the current state of the game.
        """
        player = context['player']
        gold = context['gold']
        inventory = context['inventory']
        custom_cmd = context.get('custom_command', None)

        custom_part = f"Произвольная команда игрока: {custom_cmd}" if custom_cmd else ""

        return (
            f"Имя игрока: {player['name']}\n"
            f"Класс: {player['class']}\n"
            f"Здоровье: {player['stats']['health']}\n"
            f"Стамина: {player['stats']['stamina']}\n"
            f"Магия: {player['stats']['magic']}\n"
            f"Сила: {player['stats']['strength']}\n"
            f"Ловкость: {player['stats']['agility']}\n"
            f"Интеллект: {player['stats']['intelligence']}\n"
            f"Харизма: {player['stats']['charisma']}\n"
            f"Золото: {gold}\n"
            f"Инвентарь: {', '.join(inventory) if inventory else 'пусто'}\n"
            f"{custom_part}"
        )

    def parse_response(self, response_text):
        """
        Parses the response from ChatGPT into a description and a list of actions.
        """
        description = self.extract_block(response_text, "[DESCRIPTION]", "[DESCRIPTION_END]")
        actions_block = self.extract_block(response_text, "[ACTIONS]", "[ACTIONS_END]")

        description = description.strip() if description else "Сцена не описана."
        actions = self.parse_actions(actions_block)
        return description, actions

    def extract_block(self, text, start_tag, end_tag):
        """
        Extracts a block of text between specified tags.
        """
        start_idx = text.find(start_tag)
        end_idx = text.find(end_tag)
        if start_idx == -1 or end_idx == -1:
            return ""
        return text[start_idx + len(start_tag):end_idx].strip()

    def parse_actions(self, actions_text):
        """
        Parses the actions block into a list of actions.
        """
        if not actions_text:
            return []
        actions = []
        for line in actions_text.split("\n"):
            line = line.strip()
            if line:
                actions.append(line)
        return actions

    async def send_scenario(self, bot, user_id, description, actions, player):
        """
        Sends the current game scenario to the user.
        """
        # Append player stats to the description
        stats = player['stats']
        char_info = (
            f"\n\n**Характеристики:**\n"
            f"Имя: {player['name']}\n"
            f"Класс: {player['class']}\n"
            f"Здоровье: {stats['health']}\n"
            f"Стамина: {stats['stamina']}\n"
            f"Магия: {stats['magic']}"
        )
        description += char_info

        # Use default action if no actions are provided
        if not actions:
            actions = ["Продолжить"]

        # Save actions for the user
        self.user_actions[user_id] = actions

        # Create keyboard buttons for actions
        keyboard = []
        for i, action in enumerate(actions):
            callback_data = f"act_{i}"
            keyboard.append([InlineKeyboardButton(action, callback_data=callback_data)])

        # Send the message with description and buttons
        await bot.send_message(user_id, description, parse_mode="Markdown",
                                reply_markup=InlineKeyboardMarkup(keyboard))

    def get_action_by_index(self, user_id, index):
        """
        Retrieves the action text by index for a specific user.
        """
        actions = self.user_actions.get(user_id, [])
        if 0 <= index < len(actions):
            return actions[index]
        return None
