from npc_ai.ai_system import AISystem
from npc.npc import NPC

class GameEngine:
    def __init__(self):
        self.npc_ai = AISystem()
        self.npcs = {}

    def add_npc(self, npc):
        self.npcs[npc.id] = npc

    def update_npc(self, npc_id, event):
        if npc_id in self.npcs:
            npc = self.npcs[npc_id]
            self.npc_ai.update_npc_memory(npc_id, event)
            decision = self.npc_ai.make_decision(npc_id, npc.get_state())
            # Process decision

    def game_loop(self):
        # Main game loop to process updates
        pass
