class NPC:
    def __init__(self, npc_id, name):
        self.id = npc_id
        self.name = name
        self.memory = {}
        self.state = 'neutral'

    def remember(self, key, value):
        self.memory[key] = value

    def forget(self, key):
        if key in self.memory:
            del self.memory[key]

    def set_state(self, new_state):
        self.state = new_state

    def get_memory(self):
        return self.memory

    def get_state(self):
        return self.state