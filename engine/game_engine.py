from characters.npc import NPC

class GameEngine:
    def __init__(self):
        self.npcs = []

    def add_npc(self, npc):
        self.npcs.append(npc)

    def update_npcs(self, game_state):
        for npc in self.npcs:
            decision = npc.make_decision(game_state)
            self.process_npc_decision(npc, decision)

    def process_npc_decision(self, npc, decision):
        print(f'{npc.name} decides to {decision}')

    def run_game_loop(self):
        while True:
            # Simulate game state update
            game_state = {'threat_level': 3, 'resources': []}
            self.update_npcs(game_state)