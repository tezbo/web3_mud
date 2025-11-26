import random
from enum import Enum

class WeatherState(Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAINING = "raining"
    STORMING = "storming"

class WeatherSystem:
    """
    Manages the dynamic weather system for the game world.
    """
    
    def __init__(self):
        self.current_state = WeatherState.CLEAR
        self.timer = 0
        self.duration = random.randint(10, 30) # ticks until next change
        
        self.descriptions = {
            WeatherState.CLEAR: [
                "The sky is clear and blue.",
                "Sunlight bathes the land in warmth.",
                "A gentle breeze stirs the air under a cloudless sky."
            ],
            WeatherState.CLOUDY: [
                "Grey clouds hang low in the sky.",
                "The sun is hidden behind a veil of white clouds.",
                "It looks like it might rain soon."
            ],
            WeatherState.RAINING: [
                "Rain falls steadily from the grey sky.",
                "Puddles form on the ground as rain patters down.",
                "A cold rain soaks everything in sight."
            ],
            WeatherState.STORMING: [
                "Thunder rumbles in the distance as lightning flashes.",
                "A fierce storm rages, wind howling through the area.",
                "Heavy rain lashes down, driven by strong winds."
            ]
        }
        
        # Transitions: Current -> [Possible Next States]
        self.transitions = {
            WeatherState.CLEAR: [WeatherState.CLEAR, WeatherState.CLOUDY],
            WeatherState.CLOUDY: [WeatherState.CLEAR, WeatherState.CLOUDY, WeatherState.RAINING],
            WeatherState.RAINING: [WeatherState.CLOUDY, WeatherState.RAINING, WeatherState.STORMING],
            WeatherState.STORMING: [WeatherState.RAINING, WeatherState.STORMING]
        }

    def update(self):
        """
        Update the weather system. Should be called every game tick.
        """
        self.timer += 1
        if self.timer >= self.duration:
            self._change_weather()
            self.timer = 0
            self.duration = random.randint(20, 50) # Reset duration

    def _change_weather(self):
        """
        Transition to a new weather state.
        """
        possible_next = self.transitions.get(self.current_state, [WeatherState.CLEAR])
        self.current_state = random.choice(possible_next)
        # In a real system, we might broadcast this change to all players

    def get_description(self) -> str:
        """
        Get a description of the current weather.
        """
        options = self.descriptions.get(self.current_state, ["The weather is nondescript."])
        return f"[WEATHER] {random.choice(options)}"

    def get_state(self) -> str:
        return self.current_state.value
