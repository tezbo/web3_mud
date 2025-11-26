class NPC:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.state = {}

    def update_state(self, key, value):
        self.state[key] = value

    def get_state(self):
        return self.state

    def interact(self, player):
        # Interaction logic with player
        pass
