class AISystem:
    def __init__(self):
        self.memory = {}

    def update_npc_memory(self, npc_id, event):
        if npc_id not in self.memory:
            self.memory[npc_id] = []
        self.memory[npc_id].append(event)

    def recall_memory(self, npc_id):
        return self.memory.get(npc_id, [])

    def make_decision(self, npc_id, context):
        # Implement decision making based on memory and context
        decisions = []  # Stub for decision logic
        return decisions
