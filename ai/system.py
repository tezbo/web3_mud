class AISystem:
    def __init__(self):
        self.npc_states = {}

    def update_state(self, npc_id, state):
        self.npc_states[npc_id] = state

    def get_state(self, npc_id):
        return self.npc_states.get(npc_id, None)

    def process_npc_behavior(self, npc):
        # Process NPC behavior based on their current state
        if npc.id in self.npc_states:
            state = self.npc_states[npc.id]
            # Implement behavior based on state
            return self.decide_action_based_on_state(state)
        return None

    def decide_action_based_on_state(self, state):
        # Define NPC actions based on memory/state
        if state == 'aggressive':
            return 'attack'
        elif state == 'friendly':
            return 'greet'
        elif state == 'interested':
            return 'explore'
        return 'idle'