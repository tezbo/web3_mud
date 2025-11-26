class AISystem:
    def __init__(self):
        self.npc_memory = {}

    def remember(self, npc_id, key, value):
        if npc_id not in self.npc_memory:
            self.npc_memory[npc_id] = {}
        self.npc_memory[npc_id][key] = value

    def recall(self, npc_id, key):
        return self.npc_memory.get(npc_id, {}).get(key, None)

    def act(self, npc):
        # Placeholder for NPC actions based on AI
        if npc.state == 'aggressive':
            return self.attack(npc)
        elif npc.state == 'friendly':
            return self.greet(npc)

    def attack(self, npc):
        # Logic for attacking
        return f'{npc.name} attacks!'

    def greet(self, npc):
        # Logic for greeting
        return f'{npc.name} says hello!'