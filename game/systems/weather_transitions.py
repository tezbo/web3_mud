"""
Weather Transition System - Realistic gradual weather changes.

Provides sensible weather transitions that feel natural:
- Gradual intensity changes (heavy → moderate → light → none)
- Realistic type transitions (e.g., rain → overcast → clear)
- Transition probabilities based on season and current weather
"""

import random
from typing import Dict, Tuple, Optional, List


# Realistic weather transition paths
# Format: {current_type: [(target_type, probability), ...]}
# These define what weather types can transition to what, and how likely each transition is
WEATHER_TRANSITION_PATHS = {
    "clear": [
        ("overcast", 0.3),
        ("windy", 0.2),
        ("rain", 0.05),  # Can occasionally rain directly (uncommon but possible)
        ("clear", 0.45),  # Can stay clear
    ],
    "overcast": [
        ("clear", 0.3),
        ("rain", 0.4),
        ("windy", 0.1),
        ("overcast", 0.2),  # Can stay overcast
    ],
    "rain": [
        ("overcast", 0.3),  # Rain often leads to overcast clouds
        ("storm", 0.2),     # Can intensify to storm
        ("clear", 0.1),     # Can clear quickly (uncommon)
        ("rain", 0.4),      # Can continue raining
    ],
    "storm": [
        ("rain", 0.5),      # Storms typically weaken to rain
        ("overcast", 0.3),  # Then to overcast
        ("storm", 0.2),     # Can continue as storm
    ],
    "windy": [
        ("clear", 0.4),
        ("overcast", 0.3),
        ("rain", 0.2),
        ("windy", 0.1),     # Can continue windy
    ],
    "snow": [
        ("sleet", 0.2),     # Snow can turn to sleet
        ("overcast", 0.3),  # Then to overcast
        ("clear", 0.1),     # Can clear
        ("snow", 0.4),      # Can continue snowing
    ],
    "sleet": [
        ("snow", 0.2),      # Can turn back to snow
        ("rain", 0.3),      # Or turn to rain
        ("overcast", 0.3),
        ("sleet", 0.2),
    ],
    "heatwave": [
        ("clear", 0.5),     # Heatwaves typically clear
        ("windy", 0.3),     # Or become windy
        ("heatwave", 0.2),  # Can persist
    ],
}

# Intensity transitions - gradual changes
# Format: {current_intensity: [(target_intensity, probability), ...]}
INTENSITY_TRANSITIONS = {
    "heavy": [
        ("moderate", 0.5),  # Heavy typically weakens to moderate
        ("heavy", 0.5),     # Can stay heavy
    ],
    "moderate": [
        ("heavy", 0.2),     # Can intensify
        ("light", 0.4),     # Often weakens to light
        ("moderate", 0.4),  # Can stay moderate
    ],
    "light": [
        ("moderate", 0.2),  # Can intensify slightly
        ("none", 0.5),      # Often weakens to none
        ("light", 0.3),     # Can stay light
    ],
    "none": [
        ("light", 0.4),     # Can start light
        ("none", 0.6),      # Often stays none
    ],
}


def get_weather_transition_message(
    old_type: str,
    old_intensity: str,
    new_type: str,
    new_intensity: str,
    time_of_day: str
) -> Optional[str]:
    """
    Generate a descriptive message when weather transitions from one state to another.
    
    Examples:
    - "The rain starts to slow, but the clouds don't show any sign of dissipating." (heavy rain → light rain)
    - "The rain stops, but heavy clouds remain overhead." (light rain → overcast)
    - "The sky begins to clear, patches of blue appearing through the clouds." (overcast → clear)
    
    Args:
        old_type: Previous weather type
        old_intensity: Previous intensity
        new_type: New weather type
        new_intensity: New intensity
        time_of_day: Current time of day
    
    Returns:
        Optional transition message, or None if no transition message needed
    """
    # No message if nothing changed
    if old_type == new_type and old_intensity == new_intensity:
        return None
    
    messages = []
    
    # Type transitions
    if old_type != new_type:
        if old_type == "rain" and new_type == "overcast":
            messages = [
                "The rain starts to slow, but the clouds don't show any sign of dissipating.",
                "The rain stops, but heavy clouds remain overhead, blocking out the sky.",
                "The rain ceases, leaving behind a grey, overcast sky.",
            ]
        elif old_type == "rain" and new_type == "clear":
            if time_of_day == "night":
                messages = [
                    "The rain stops and the clouds begin to break up, revealing the stars above.",
                    "The rain ceases and the night sky begins to clear.",
                    "The rain stops, and slowly but surely, the clouds begin to dissipate, revealing the night sky.",
                ]
            else:
                messages = [
                    "The rain stops and the clouds begin to break up, revealing patches of blue sky.",
                    "The rain ceases and the sky begins to clear.",
                    "The rain stops, and slowly but surely, the clouds begin to dissipate.",
                ]
        elif old_type == "rain" and new_type == "storm":
            messages = [
                "The rain intensifies dramatically, becoming a full-blown storm.",
                "The rain grows heavier, the wind picking up as a storm develops.",
                "The rain escalates into a fierce storm, with wind and thunder.",
            ]
        elif old_type == "storm" and new_type == "rain":
            messages = [
                "The storm weakens, but the rain continues steadily.",
                "The storm passes, leaving behind steady rain.",
                "The worst of the storm has passed, though rain continues to fall.",
            ]
        elif old_type == "storm" and new_type == "overcast":
            messages = [
                "The storm subsides, leaving behind heavy, grey clouds.",
                "The storm passes, but the sky remains heavily overcast.",
                "The storm weakens and passes, though clouds still cover the sky.",
            ]
        elif old_type == "overcast" and new_type == "rain":
            messages = [
                "The clouds darken and rain begins to fall.",
                "The overcast sky finally releases its burden, and rain starts to fall.",
                "Rain begins to fall from the heavy clouds overhead.",
            ]
        elif old_type == "overcast" and new_type == "clear":
            if time_of_day == "night":
                messages = [
                    "The clouds begin to break up, stars appearing overhead.",
                    "The overcast sky starts to clear, revealing the dark night sky.",
                    "The clouds slowly dissipate, allowing the stars to shine through.",
                ]
            else:
                messages = [
                    "The clouds begin to break up, patches of blue sky appearing overhead.",
                    "The overcast sky starts to clear, revealing glimpses of blue.",
                    "The clouds slowly dissipate, allowing the sky to clear.",
                ]
        elif old_type == "clear" and new_type == "overcast":
            if time_of_day == "night":
                messages = [
                    "Clouds begin to gather, slowly covering the stars.",
                    "The clear night sky starts to cloud over, hiding the moon and stars.",
                    "Clouds drift in, gradually obscuring the night sky.",
                ]
            else:
                messages = [
                    "Clouds begin to gather, slowly covering the clear sky.",
                    "The clear sky starts to cloud over, grey clouds moving in.",
                    "Clouds drift in, gradually obscuring the clear sky.",
                ]
        elif old_type == "clear" and new_type == "rain":
            if time_of_day == "night":
                messages = [
                    "Clouds gather quickly in the darkness and rain begins to fall.",
                    "The clear night sky darkens with clouds, and rain starts.",
                    "The weather turns quickly as clouds move in and rain begins.",
                ]
            else:
                messages = [
                    "Clouds gather quickly and rain begins to fall.",
                    "The clear sky darkens with clouds, and rain starts.",
                    "The weather turns quickly as clouds move in and rain begins.",
                ]
        elif old_type == "snow" and new_type == "sleet":
            messages = [
                "The snow turns wetter, becoming sleet.",
                "The snow begins to mix with rain, turning to sleet.",
                "The snow changes to sleet as the temperature rises slightly.",
            ]
        elif old_type == "sleet" and new_type == "rain":
            messages = [
                "The sleet turns to rain as the temperature continues to rise.",
                "The icy sleet becomes pure rain.",
                "The sleet melts into steady rain.",
            ]
        elif old_type == "sleet" and new_type == "snow":
            messages = [
                "The sleet turns back to snow as the temperature drops.",
                "The sleet freezes, becoming snow once more.",
                "The sleet solidifies into snow.",
            ]
        elif old_type == "windy" and new_type == "clear":
            messages = [
                "The wind dies down and the sky clears.",
                "The wind calms and the weather clears.",
                "The wind settles, leaving behind clear skies.",
            ]
        elif old_type == "clear" and new_type == "windy":
            messages = [
                "A breeze picks up, gradually strengthening into wind.",
                "The calm air begins to stir, developing into wind.",
                "Wind begins to blow, picking up speed.",
            ]
        elif old_type == "heatwave" and new_type == "clear":
            messages = [
                "The intense heat finally breaks, leaving behind clear, cooler weather.",
                "The heatwave ends, replaced by clear skies and more bearable temperatures.",
                "The oppressive heat subsides, the weather clearing.",
            ]
    
    # Intensity transitions (same type, different intensity)
    elif old_intensity != new_intensity and old_type == new_type:
        if old_type == "rain":
            if old_intensity == "heavy" and new_intensity == "moderate":
                messages = [
                    "The heavy rain starts to ease, becoming more moderate.",
                    "The torrential downpour begins to slow to a steady rain.",
                    "The heavy rain weakens slightly, settling into a steady pace.",
                ]
            elif old_intensity == "moderate" and new_intensity == "light":
                messages = [
                    "The rain starts to lighten, becoming more of a drizzle.",
                    "The steady rain begins to slow, becoming lighter.",
                    "The rain weakens, becoming a light drizzle.",
                ]
            elif old_intensity == "light" and new_intensity == "none":
                messages = [
                    "The light rain finally stops, though clouds remain.",
                    "The drizzle ceases, though the sky remains cloudy.",
                    "The light rain stops, leaving behind wet ground and grey skies.",
                ]
            elif old_intensity == "moderate" and new_intensity == "heavy":
                messages = [
                    "The rain intensifies, becoming heavy and driving.",
                    "The steady rain grows heavier, turning into a downpour.",
                    "The rain picks up, becoming heavy and torrential.",
                ]
            elif old_intensity == "light" and new_intensity == "moderate":
                messages = [
                    "The light rain grows steadier and heavier.",
                    "The drizzle intensifies into steady rain.",
                    "The light rain strengthens, becoming more persistent.",
                ]
        elif old_type == "storm":
            if old_intensity == "heavy" and new_intensity == "moderate":
                messages = [
                    "The fierce storm begins to weaken, though it's still intense.",
                    "The worst of the storm passes, though it continues.",
                    "The storm's fury begins to subside slightly.",
                ]
            elif old_intensity == "moderate" and new_intensity == "heavy":
                messages = [
                    "The storm intensifies, reaching its full fury.",
                    "The storm grows fiercer, wind and rain reaching peak intensity.",
                    "The storm reaches its peak, a true tempest.",
                ]
        elif old_type == "snow":
            if old_intensity == "heavy" and new_intensity == "moderate":
                messages = [
                    "The heavy snow begins to ease, though it continues steadily.",
                    "The blizzard conditions start to improve slightly.",
                    "The heavy snowfall begins to moderate.",
                ]
            elif old_intensity == "moderate" and new_intensity == "light":
                messages = [
                    "The steady snow begins to lighten, becoming more gentle.",
                    "The snowfall starts to slow, becoming lighter.",
                    "The snow weakens, becoming a gentle flurry.",
                ]
            elif old_intensity == "light" and new_intensity == "none":
                messages = [
                    "The light snow finally stops, leaving behind a white blanket.",
                    "The snow stops falling, though white covers everything.",
                    "The gentle snowfall ceases.",
                ]
        elif old_type == "windy":
            if old_intensity == "heavy" and new_intensity == "moderate":
                messages = [
                    "The fierce wind begins to die down, though it's still strong.",
                    "The gale-force winds start to weaken.",
                    "The strong wind begins to moderate slightly.",
                ]
            elif old_intensity == "moderate" and new_intensity == "light":
                messages = [
                    "The brisk wind begins to calm, becoming more of a breeze.",
                    "The wind starts to die down, becoming gentler.",
                    "The wind weakens, becoming a light breeze.",
                ]
            elif old_intensity == "light" and new_intensity == "none":
                messages = [
                    "The wind finally dies down, leaving the air still.",
                    "The breeze stops, the air becoming calm.",
                    "The wind settles, leaving behind peaceful stillness.",
                ]
        elif old_type == "overcast":
            if old_intensity == "moderate" and new_intensity == "light":
                messages = [
                    "The heavy clouds begin to thin slightly, though the sky remains grey.",
                    "The cloud cover starts to break up a little, becoming lighter.",
                    "The clouds begin to thin, though the sky remains overcast.",
                ]
    
    # If we have messages for this transition, pick one
    if messages:
        return random.choice(messages)
    
    # Fallback: Generic transition message if we don't have a specific one
    return None


def get_realistic_weather_transition(
    current_type: str,
    current_intensity: str,
    season: str,
    locked: bool = False
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Get a realistic weather transition based on current weather.
    
    Weather transitions work in two stages:
    1. First, intensity gradually changes (heavy → moderate → light → none)
    2. Then, when intensity reaches "none" or after some time, type can change
    
    Args:
        current_type: Current weather type (e.g., "rain", "clear")
        current_intensity: Current intensity (e.g., "heavy", "light")
        season: Current season ("spring", "summer", "autumn", "winter")
        locked: Whether weather is manually locked (if True, no transitions)
    
    Returns:
        Tuple of (new_type, new_intensity, transition_message) or (None, None, None) if no change
    """
    if locked:
        return None, None, None
    
    # Stage 1: Check for intensity transition (more likely)
    # Weather typically changes intensity before changing type
    if random.random() < 0.7:  # 70% chance to change intensity first
        if current_intensity in INTENSITY_TRANSITIONS:
            transitions = INTENSITY_TRANSITIONS[current_intensity]
            rand = random.random()
            cumulative = 0
            
            for target_intensity, prob in transitions:
                cumulative += prob
                if rand <= cumulative:
                    if target_intensity != current_intensity:
                        # Generate transition message
                        from game_engine import get_time_of_day
                        time_of_day = get_time_of_day()
                        message = get_weather_transition_message(
                            current_type, current_intensity,
                            current_type, target_intensity,
                            time_of_day
                        )
                        return current_type, target_intensity, message
                    break
    
    # Stage 2: Check for type transition (less likely, only if intensity is low or after time)
    # Type transitions are more likely when intensity is "none" or "light"
    type_change_probability = 0.2  # Base 20% chance
    
    if current_intensity == "none":
        type_change_probability = 0.5  # More likely when clear/calm
    elif current_intensity == "light":
        type_change_probability = 0.3  # Somewhat likely when light
    elif current_intensity in ["moderate", "heavy"]:
        type_change_probability = 0.1  # Less likely when active
    
    if random.random() < type_change_probability:
        if current_type in WEATHER_TRANSITION_PATHS:
            transitions = WEATHER_TRANSITION_PATHS[current_type]
            
            # Adjust probabilities based on season
            season_adjusted_transitions = adjust_transitions_for_season(
                transitions, current_type, season
            )
            
            rand = random.random()
            cumulative = 0
            
            for target_type, prob in season_adjusted_transitions:
                cumulative += prob
                if rand <= cumulative:
                    if target_type != current_type:
                        # When type changes, pick appropriate intensity
                        new_intensity = get_initial_intensity_for_type(target_type)
                        # Generate transition message
                        from game_engine import get_time_of_day
                        time_of_day = get_time_of_day()
                        message = get_weather_transition_message(
                            current_type, current_intensity,
                            target_type, new_intensity,
                            time_of_day
                        )
                        return target_type, new_intensity, message
                    break
    
    return None, None, None


def adjust_transitions_for_season(
    transitions: List[Tuple[str, float]],
    current_type: str,
    season: str
) -> List[Tuple[str, float]]:
    """
    Adjust transition probabilities based on season.
    
    E.g., in winter, snow/rain transitions are more likely than in summer.
    """
    adjusted = []
    
    for target_type, base_prob in transitions:
        prob = base_prob
        
        # Season-specific adjustments
        if season == "winter":
            if target_type in ["snow", "sleet"]:
                prob *= 1.5  # More likely in winter
            elif target_type == "heatwave":
                prob *= 0.1  # Much less likely in winter
        elif season == "summer":
            if target_type in ["heatwave", "clear"]:
                prob *= 1.3  # More likely in summer
            elif target_type in ["snow", "sleet"]:
                prob *= 0.1  # Very unlikely in summer
        elif season == "spring":
            if target_type == "rain":
                prob *= 1.4  # More likely in spring
        elif season == "autumn":
            if target_type in ["windy", "rain"]:
                prob *= 1.3  # More likely in autumn
        
        # Cap probability at 1.0
        prob = min(prob, 1.0)
        adjusted.append((target_type, prob))
    
    # Normalize probabilities so they sum to 1.0
    total = sum(prob for _, prob in adjusted)
    if total > 0:
        adjusted = [(t, p / total) for t, p in adjusted]
    
    return adjusted


def get_initial_intensity_for_type(weather_type: str) -> str:
    """
    Get a sensible initial intensity for a weather type.
    
    When weather type changes, what intensity should it start at?
    """
    if weather_type in ["rain", "snow", "sleet"]:
        # Precipitation typically starts light
        return random.choice(["light", "moderate"])  # 50/50 chance
    elif weather_type == "storm":
        # Storms typically start moderate or heavy
        return random.choices(["moderate", "heavy"], weights=[0.3, 0.7])[0]
    elif weather_type == "windy":
        # Wind typically starts light or moderate
        return random.choices(["light", "moderate"], weights=[0.6, 0.4])[0]
    elif weather_type == "heatwave":
        # Heatwaves typically start moderate
        return "moderate"
    elif weather_type == "overcast":
        # Overcast typically starts light
        return "light"
    else:  # clear
        return "none"
