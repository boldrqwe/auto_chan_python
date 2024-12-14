import random
from collections import defaultdict


class RPGGame:
    def __init__(self, bot):
        self.bot = bot  # Telegram Bot instance
        self.players = {}  # {user_id: {"name": str, "class": str, "stats": dict}}
        self.team_votes = defaultdict(list)  # {action: [user_id, user_id, ...]}
        self.current_event = None  # Stores the current event or scenario
        self.world_state = {"gold": 0, "resources": {}}  # Shared team state

    async def start_game(self, user_id):
        self.world_state = {"gold": 0, "resources": {}}
        self.players = {}
        self.current_event = None
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
            await self.bot.send_message(user_id, "Сначала начните игру с помощью команды /start")
            return

        self.players[user_id]["class"] = player_class
        await self.bot.send_message(user_id, f"Класс успешно установлен: {player_class}")

    async def initiate_event(self, user_id):
        events = [
            "Вы нашли заброшенный храм. Что будете делать?",
            "Вы встретили банду гоблинов. Будете сражаться или убегать?",
            "Перед вами торговец. Хотите поторговать?",
        ]
        self.current_event = random.choice(events)
        self.team_votes.clear()
        await self.bot.send_message(user_id, self.current_event)
        await self.bot.send_message(user_id, "Выберите действие: /vote <действие>")

    def register_vote(self, user_id, action):
        # Удаляем предыдущие голоса пользователя
        for key in self.team_votes:
            if user_id in self.team_votes[key]:
                self.team_votes[key].remove(user_id)

        self.team_votes[action].append(user_id)
        return f"Голос за '{action}' успешно зарегистрирован!"

    async def calculate_votes(self, user_id):
        if not self.team_votes:
            await self.bot.send_message(user_id, "Вы не проголосовали!")
            return

        # Подсчёт голосов
        votes_count = {action: len(voters) for action, voters in self.team_votes.items()}
        most_voted = max(votes_count, key=votes_count.get)

        await self.bot.send_message(user_id, f"Вы выбрали действие: '{most_voted}'")
        await self.execute_action(user_id, most_voted)

    async def execute_action(self, user_id, action):
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
            self.world_state["gold"] += random.randint(10, 50)
        elif action == "сражаться":
            if user_id in self.players:
                self.players[user_id]["stats"]["health"] -= random.randint(5, 15)

        await self.bot.send_message(user_id, outcome)
        self.current_event = None

    async def show_stats(self, user_id):
        if user_id not in self.players:
            await self.bot.send_message(user_id, "Вы ещё не начали игру. Используйте /start для начала.")
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
                         f"Общее золото: {self.world_state['gold']}")
        await self.bot.send_message(user_id, stats_message)