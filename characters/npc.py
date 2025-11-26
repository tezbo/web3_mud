from ai.aisystem import AISystem

class NPC:
    def __init__(self, name):
        self.name = name
        self.state = None
        self.ai_system = AISystem()

    def update_state(self, new_state):
        self.state = new_state
        self.ai_system.remember('last_state', new_state)

    def make_decision(self, game_state):
        return self.ai_system.update(self, game_state)

    def __repr__(self):
        return f'NPC(name={self.name}, state={self.state})'