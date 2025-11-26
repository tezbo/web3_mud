class AISystem:
    def __init__(self):
        self.npc_memory = {}

    def remember(self, npc_id, information):
        if npc_id not in self.npc_memory:
            self.npc_memory[npc_id] = []
        self.npc_memory[npc_id].append(information)

    def recall(self, npc_id):
        return self.npc_memory.get(npc_id, [])

    def make_decision(self, npc_id, context):
        # Implement decision-making logic based on memory and context
        pass

    def update_npc_state(self, npc_id, new_state):
        # Logic for updating NPC state
        pass