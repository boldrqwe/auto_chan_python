import random
from collections import defaultdict


class RPGGame:
    def __init__(self, bot):
        self.bot = bot  # Telegram Bot instance
        self.players = {}  # {user_id: {"name": str, "class": str, "stats": dict}}
        self.current_event = {}  # {user_id: event}
        self.world_state = defaultdict(lambda: {"gold": 0, "resources": {}})  # Per-user state

    async def start_game(self):
        # Placeholder for initialization logic when game starts
        return "Игра инициализирована! Используйте команды для взаимодействия."

    async def add_player(self, user_id):
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
        await self.bot.send_message(user_id, "Игра началась! Вы - единственный игрок. Выберите класс и начните исследование мира! Используйте /setclass <класс> для выбора класса.")

    async def set_class(self, user_id, player_class):
        if user_id not in self.players:
            await self.bot.send_message(user_id, "Сначала добавьтесь в игру с помощью команды /addplayer")
            return

        self.players[user_id]["class"] = player_class
        await self.bot.send_message(user_id, f"Класс успешно установлен: {player_class}")

    async def initiate_event(self, user_id):
        events = [
            "Вы нашли заброшенный храм. Что будете делать?",
            "Вы встретили банду гоблинов. Будете сражаться или убегать?",
            "Перед вами торговец. Хотите поторговать?",
        ]
        self.current_event[user_id] = random.choice(events)
        await self.bot.send_message(user_id, self.current_event[user_id])
        await self.bot.send_message(user_id, "Выберите действие: /action <действие>")

    async def execute_action(self, user_id, action):
        if user_id not in self.players:
            await self.bot.send_message(user_id, "Сначала добавьтесь в игру с помощью команды /addplayer")
            return

        # Пример реализации действий
        outcomes = {
            "исследовать": "Вы нашли сундук с золотом!",
            "сражаться": "Вы победили врагов, но потеряли часть здоровья.",
            "убежать": "Вы успешно убежали, но потеряли немного золота.",
            "торговать": "Вы обменяли часть ресурсов на полезные предметы.",
        }
        outcome = outcomes.get(action, "Ничего не произошло.")

        # Пример изменения состояния
        if action == "исследовать":
            self.world_state[user_id]["gold"] += random.randint(10, 50)
        elif action == "сражаться":
            self.players[user_id]["stats"]["health"] -= random.randint(5, 15)

        await self.bot.send_message(user_id, outcome)
        self.current_event[user_id] = None

    async def show_stats(self, user_id):
        if user_id not in self.players:
            await self.bot.send_message(user_id, "Вы ещё не добавились в игру. Используйте /addplayer для начала.")
            return

        player = self.players[user_id]
        stats_message = (f"Ваши характеристики:\n"
                         f"Имя: {player['name']}\n"
                         f"Класс: {player['class']}\n"
                         f"Здоровье: {player['stats']['health']}\n"
                         f"Сила: {player['stats']['strength']}\n"
                         f"Ловкость: {player['stats']['agility']}\n"
                         f"Интеллект: {player['stats']['intelligence']}\n"
                         f"Харизма: {player['stats']['charisma']}\n"
                         f"Общее золото: {self.world_state[user_id]['gold']}")
        await self.bot.send_message(user_id, stats_message)
