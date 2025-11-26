import random

class AISystem:
    def __init__(self):
        self.memory = {}

    def remember(self, key, value):
        self.memory[key] = value

    def recall(self, key):
        return self.memory.get(key, None)

    def make_decision(self, context):
        # Basic decision-making based on context
        actions = ['explore', 'interact', 'rest']
        if context['threat_level'] > 5:
            return 'flee'
        return random.choice(actions)

    def update(self, npc, game_state):
        context = self.analyze_game_state(game_state)
        decision = self.make_decision(context)
        return decision

    def analyze_game_state(self, game_state):
        return {
            'threat_level': game_state.get('threat_level', 0),
            'resources': game_state.get('resources', []),
        }