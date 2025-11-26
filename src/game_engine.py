from ai.system import AISystem
from models.npc import NPC

class GameEngine:
    def __init__(self):
        self.aisystem = AISystem()
        self.npcs = {}  # Dictionary to manage NPCs

    def add_npc(self, npc):
        self.npcs[npc.npc_id] = npc

    def update_npc(self, npc_id, state):
        if npc_id in self.npcs:
            npc = self.npcs[npc_id]
            npc.set_state(state)
            self.aisystem.update_npc_state(npc_id, state)

    def process_npc_decisions(self):
        for npc_id in self.npcs:
            self.aisystem.process_decision(npc_id)
