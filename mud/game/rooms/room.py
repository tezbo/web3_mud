class Room:
    def __init__(self, name, description, smells=None, sounds=None, textures=None):
        self.name = name
        self.description = description
        self.smells = smells if smells else []
        self.sounds = sounds if sounds else []
        self.textures = textures if textures else []

    def get_full_description(self):
        return f'{self.description}\n' + self.get_sensory_details() + '\n'

    def get_sensory_details(self):
        sensory_details = []
        if self.smells:
            sensory_details.append('You smell ' + ', '.join(self.smells) + '.')
        if self.sounds:
            sensory_details.append('You hear ' + ', '.join(self.sounds) + '.')
        if self.textures:
            sensory_details.append('You feel ' + ', '.join(self.textures) + '.')
        return ' '.join(sensory_details)