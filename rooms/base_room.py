class BaseRoom:
    def __init__(self, name, description, smells=None, sounds=None, textures=None):
        self.name = name
        self.description = description
        self.smells = smells or []
        self.sounds = sounds or []
        self.textures = textures or []

    def get_full_description(self):
        sensory_details = (', '.join(self.smells) + '. ' if self.smells else '') + 
                          (', '.join(self.sounds) + '. ' if self.sounds else '') + 
                          (', '.join(self.textures) + '. ' if self.textures else '')
        return f'{self.description} {sensory_details}'

