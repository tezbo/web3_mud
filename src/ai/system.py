class AISystem:
    def __init__(self):
        self.npc_memory = {}

    def update_npc_state(self, npc_id, state):
        self.npc_memory[npc_id] = state

    def retrieve_npc_state(self, npc_id):
        return self.npc_memory.get(npc_id, None)

    def process_decision(self, npc_id):
        state = self.retrieve_npc_state(npc_id)
        if state:
            # Implement decision-making logic based on memory/state
            pass
