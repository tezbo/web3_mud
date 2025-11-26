class NPC:
    def __init__(self, npc_id, name):
        self.npc_id = npc_id
        self.name = name
        self.state = None

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state
