class NPC:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.state = {}

    def set_state(self, key, value):
        self.state[key] = value

    def get_state(self, key):
        return self.state.get(key)

    def interact(self, player):
        # Implement interaction logic
        pass