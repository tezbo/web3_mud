"""
Weather Messages System - Periodic weather-related messages for outdoor rooms.

Provides dynamic, contextual weather messages that appear every 30-60 seconds
in outdoor rooms, making the world feel alive and responsive to weather conditions.
"""

import random
from typing import Dict, List, Optional, Tuple


# Weather messages organized by type, intensity, and time of day
# These are periodic messages that appear in outdoor rooms every 30-60 seconds
WEATHER_MESSAGES: Dict[str, Dict[str, Dict[str, List[str]]]] = {
    "rain": {
        "light": {
            "dawn": [
                "A gentle morning rain patters softly against the ground.",
                "Light raindrops fall steadily, creating small puddles.",
                "The morning rain is refreshing and cool.",
            ],
            "day": [
                "Light rain continues to fall, making the ground slick.",
                "A steady drizzle soaks everything slowly.",
                "Raindrops tap rhythmically against leaves and cobblestones.",
                "The light rain creates a soothing, rhythmic sound.",
            ],
            "dusk": [
                "Evening rain falls gently as daylight fades.",
                "The rain seems to pick up slightly as evening approaches.",
                "Light rain continues into the evening, making everything glisten.",
            ],
            "night": [
                "Light rain falls steadily through the night.",
                "The sound of raindrops is amplified in the quiet darkness.",
                "Rain continues to fall, each drop catching the faint light.",
            ],
        },
        "moderate": {
            "dawn": [
                "The morning rain falls steadily, darkening the ground.",
                "Rain comes down in steady sheets as dawn breaks.",
                "Morning rain soaks everything, creating small streams.",
            ],
            "day": [
                "Rain falls steadily, soaking everything and creating small streams.",
                "The steady rain makes visibility slightly reduced.",
                "Water runs off surfaces in rivulets as the rain continues.",
                "The rain has been falling long enough that everything is thoroughly wet.",
            ],
            "dusk": [
                "Evening rain falls steadily, making the fading light seem dimmer.",
                "The rain shows no signs of letting up as evening arrives.",
                "Steady rain continues into the evening hours.",
            ],
            "night": [
                "Rain falls steadily through the darkness, creating a constant sound.",
                "The steady rain makes the night feel colder and wetter.",
                "Rain continues unabated, its sound a constant backdrop to the night.",
            ],
        },
        "heavy": {
            "dawn": [
                "Heavy rain pounds down, making visibility poor in the morning gloom.",
                "The morning rain is torrential, creating rushing streams.",
                "Heavy rain lashes down as dawn struggles through the clouds.",
            ],
            "day": [
                "Heavy rain pounds down in sheets, making it hard to see far.",
                "The rain is coming down so hard it's almost horizontal.",
                "Torrential rain creates rushing streams and deep puddles.",
                "Visibility is severely reduced by the heavy downpour.",
            ],
            "dusk": [
                "The heavy rain makes evening feel darker and more oppressive.",
                "Torrential rain continues into evening, showing no sign of stopping.",
                "Heavy rain lashes down as darkness deepens.",
            ],
            "night": [
                "Heavy rain crashes down in the darkness, making it hard to see.",
                "The torrential rain creates a wall of water in the night.",
                "Rain pounds down with such force it seems to shake the ground.",
            ],
        },
    },
    "storm": {
        "moderate": {
            "dawn": [
                "Thunder rumbles overhead as the storm continues into morning.",
                "Lightning flashes, briefly illuminating the stormy dawn.",
                "The morning storm shows no signs of weakening.",
            ],
            "day": [
                "Thunder booms overhead, followed by the crash of rain.",
                "Lightning flashes across the sky, followed seconds later by thunder.",
                "The storm rages, with wind and rain combining in a fierce display.",
                "Heavy winds drive the rain almost horizontally.",
            ],
            "dusk": [
                "The evening storm intensifies as darkness approaches.",
                "Lightning illuminates the darkening sky in dramatic flashes.",
                "Thunder rolls as evening falls, making the storm feel more ominous.",
            ],
            "night": [
                "Lightning flashes in the darkness, briefly illuminating everything in stark white.",
                "Thunder crashes overhead, so loud it seems to shake the ground.",
                "The night storm rages with wind, rain, and lightning.",
                "Lightning strikes nearby, followed immediately by deafening thunder.",
            ],
        },
        "heavy": {
            "dawn": [
                "A fierce storm rages, thunder and lightning dominating the morning.",
                "The storm is at its peak, making dawn seem like midnight.",
                "Lightning strikes repeatedly as the morning storm reaches its height.",
            ],
            "day": [
                "The storm reaches its peak, with thunder, lightning, and driving rain.",
                "Lightning strikes close by, the thunder almost instantaneous.",
                "The storm rages with incredible ferocity, wind whipping everything.",
                "Visibility is near zero in the driving rain and wind.",
            ],
            "dusk": [
                "The evening storm reaches its peak, a true tempest.",
                "Lightning illuminates the sky in constant flashes as evening falls.",
                "The storm shows no mercy, reaching its full fury.",
            ],
            "night": [
                "The storm reaches its peak, a true force of nature unleashed.",
                "Lightning strikes so frequently the sky seems to be on fire.",
                "The storm's fury is at its height, an awesome and terrifying display.",
                "Thunder crashes continuously, one roll blending into the next.",
            ],
        },
    },
    "overcast": {
        "light": {
            "dawn": [
                "Heavy grey clouds block out much of the morning light.",
                "The overcast sky makes dawn seem muted and grey.",
                "Clouds hang low and heavy as morning breaks.",
            ],
            "day": [
                "Grey clouds cover the sky, blocking out the sun.",
                "The overcast sky creates a muted, somber atmosphere.",
                "Heavy clouds make the day seem darker than it should be.",
            ],
            "dusk": [
                "The overcast sky makes evening come early and dark.",
                "Grey clouds block out what little evening light remains.",
                "The heavy cloud cover deepens the approaching darkness.",
            ],
            "night": [
                "The overcast sky blocks out stars and moon alike.",
                "Heavy clouds make the night even darker than usual.",
                "No light pierces through the thick cloud cover.",
            ],
        },
        "moderate": {
            "dawn": [
                "Thick, heavy clouds block almost all morning light.",
                "The cloud cover is so thick dawn barely registers.",
                "Grey clouds hang oppressively low as morning arrives.",
            ],
            "day": [
                "The sky is a uniform grey, with no break in the clouds.",
                "Heavy cloud cover makes the day feel dim and dreary.",
                "The overcast sky blocks all sunlight, creating a gloomy atmosphere.",
            ],
            "dusk": [
                "The heavy cloud cover makes evening darkness come quickly.",
                "Grey clouds block out any trace of evening light.",
                "The oppressive cloud cover deepens the darkness.",
            ],
            "night": [
                "The cloud cover is so thick it seems to press down on the land.",
                "No stars, no moon—just the oppressive darkness of heavy clouds.",
                "The overcast sky makes the night feel closed in and dark.",
            ],
        },
    },
    "snow": {
        "light": {
            "dawn": [
                "Light snow falls steadily in the morning, covering everything in white.",
                "Gentle snowflakes drift down as dawn breaks.",
                "Morning snow makes everything quiet and peaceful.",
            ],
            "day": [
                "Light snow continues to fall, adding to the white blanket on the ground.",
                "Snowflakes drift down steadily, creating a peaceful scene.",
                "The gentle snowfall makes everything quiet and still.",
            ],
            "dusk": [
                "Evening snow continues to fall, making the world quieter.",
                "Light snow drifts down as evening approaches.",
                "The gentle snowfall deepens as daylight fades.",
            ],
            "night": [
                "Light snow falls through the night, visible in the darkness.",
                "Snowflakes drift down, barely visible in the night.",
                "The gentle snowfall makes the night quieter and still.",
            ],
        },
        "moderate": {
            "dawn": [
                "Steady snow falls as morning arrives, accumulating quickly.",
                "The morning snow is coming down thick enough to reduce visibility.",
                "Snow falls in steady flakes, blanketing everything in white.",
            ],
            "day": [
                "Steady snow continues to fall, reducing visibility.",
                "The snow is accumulating, creating a deep white blanket.",
                "Snow falls thick enough to muffle sounds and obscure distant objects.",
            ],
            "dusk": [
                "Evening snow continues steadily, making everything white.",
                "The snowfall shows no sign of stopping as evening arrives.",
                "Steady snow deepens as daylight fades.",
            ],
            "night": [
                "Steady snow falls through the darkness, accumulating quickly.",
                "The snow continues unabated, making the night quieter.",
                "Snow falls thick enough to reduce visibility even in the night.",
            ],
        },
        "heavy": {
            "dawn": [
                "Heavy snow falls in thick flakes, making morning visibility near zero.",
                "The morning blizzard reduces visibility to mere feet.",
                "Snow falls so thick it's difficult to see through the morning gloom.",
            ],
            "day": [
                "Heavy snow falls in thick sheets, creating near-whiteout conditions.",
                "The snowfall is so heavy visibility is severely reduced.",
                "A blizzard rages, with wind and snow combining in a fierce display.",
            ],
            "dusk": [
                "The heavy snowfall makes evening darkness come early.",
                "Evening brings no relief from the heavy snow.",
                "The blizzard continues unabated as darkness approaches.",
            ],
            "night": [
                "Heavy snow falls in the darkness, creating a near-whiteout.",
                "The blizzard makes the night dangerous and disorienting.",
                "Snow falls so thick it's hard to see your hand in front of your face.",
            ],
        },
    },
    "windy": {
        "light": {
            "dawn": [
                "A gentle morning breeze stirs the air.",
                "Light winds make the morning air feel fresh.",
                "A soft breeze rustles through as dawn breaks.",
            ],
            "day": [
                "A gentle breeze blows, rustling leaves and making the day pleasant.",
                "Light winds keep the air fresh and moving.",
                "A soft breeze tugs at your clothes gently.",
            ],
            "dusk": [
                "Evening breezes pick up slightly as the day ends.",
                "Light winds make the evening air feel cooler.",
                "A gentle breeze stirs as evening approaches.",
            ],
            "night": [
                "A light night breeze whispers past.",
                "Gentle winds make the night air feel fresh.",
                "A soft breeze rustles through the darkness.",
            ],
        },
        "moderate": {
            "dawn": [
                "Brisk morning winds make everything sway and move.",
                "The morning wind is strong enough to pull at your clothes.",
                "Wind whips through as dawn breaks.",
            ],
            "day": [
                "Brisk winds blow steadily, making leaves dance and branches sway.",
                "The wind is strong enough to make it hard to keep your footing.",
                "Steady winds create a constant rustling and movement around you.",
            ],
            "dusk": [
                "Evening winds pick up, making everything restless.",
                "Brisk winds make the evening feel cooler and more active.",
                "The wind seems to strengthen as evening approaches.",
            ],
            "night": [
                "Brisk winds blow through the night, making everything restless.",
                "The night wind is strong enough to make structures creak.",
                "Steady winds create an eerie, restless atmosphere in the darkness.",
            ],
        },
        "heavy": {
            "dawn": [
                "Strong morning winds howl through, making it hard to stand steady.",
                "The morning wind is fierce, whipping everything around.",
                "Gale-force winds make dawn feel chaotic and dangerous.",
            ],
            "day": [
                "Strong winds howl through, making it difficult to keep your footing.",
                "Gale-force winds whip debris and dust through the air.",
                "The wind is so strong it's hard to move against it.",
                "Fierce winds make everything sway and creak dangerously.",
            ],
            "dusk": [
                "Evening winds reach gale force, making the approach of night dangerous.",
                "The wind is so strong it's hard to hear anything else.",
                "Gale-force winds continue into evening, showing no sign of weakening.",
            ],
            "night": [
                "Strong winds howl through the night like angry spirits.",
                "Gale-force winds make the darkness feel dangerous and chaotic.",
                "The wind is so fierce it seems to shake the very ground.",
                "Fierce winds create an eerie, howling sound in the darkness.",
            ],
        },
    },
    "clear": {
        "none": {
            "dawn": [
                "The morning air is clear and fresh.",
                "Dawn breaks with perfect clarity, no clouds in sight.",
                "The morning sky is a brilliant, cloudless blue.",
            ],
            "day": [
                "The sky is perfectly clear, with not a cloud in sight.",
                "Brilliant sunlight shines from a cloudless sky.",
                "The clear sky stretches endlessly overhead.",
                "Perfect visibility extends as far as the eye can see.",
            ],
            "dusk": [
                "The evening sky is perfectly clear, promising a beautiful night.",
                "Clear skies stretch overhead as evening approaches.",
                "Not a cloud mars the beautiful evening sky.",
            ],
            "night": [
                "The night sky is perfectly clear, stars visible in abundance.",
                "Clear skies allow the stars and moon to shine brightly.",
                "Perfect visibility under the clear night sky.",
            ],
        },
    },
    "sleet": {
        "light": {
            "dawn": [
                "Light sleet falls, mixing with morning rain.",
                "Icy pellets mix with rain in the morning gloom.",
                "The morning brings a mix of rain and sleet.",
            ],
            "day": [
                "Light sleet falls, making the ground treacherous.",
                "Icy pellets tap against surfaces, mixing with rain.",
                "Sleet continues to fall, creating slick, dangerous surfaces.",
            ],
            "dusk": [
                "Evening sleet continues, making everything icy and dangerous.",
                "Light sleet falls as evening approaches, mixing with rain.",
                "Icy conditions worsen as evening arrives.",
            ],
            "night": [
                "Light sleet falls through the night, creating dangerous conditions.",
                "Icy pellets continue to fall, making the darkness more treacherous.",
                "Sleet makes the night colder and more dangerous.",
            ],
        },
        "moderate": {
            "dawn": [
                "Steady sleet falls, making the morning treacherous.",
                "Icy pellets come down steadily as dawn breaks.",
                "The morning sleet is making everything dangerously slick.",
            ],
            "day": [
                "Steady sleet falls, creating treacherous, icy conditions.",
                "Icy pellets come down thick enough to obscure vision.",
                "The sleet is making everything slick and dangerous.",
            ],
            "dusk": [
                "Evening sleet continues steadily, worsening conditions.",
                "The sleet shows no sign of stopping as evening arrives.",
                "Steady sleet makes evening treacherous and cold.",
            ],
            "night": [
                "Steady sleet falls through the night, creating dangerous conditions.",
                "Icy pellets continue unabated, making the night treacherous.",
                "The sleet makes navigation in the darkness extremely dangerous.",
            ],
        },
        "heavy": {
            "dawn": [
                "Heavy sleet pounds down, making morning visibility near zero.",
                "The morning sleet is coming down so thick it's almost whiteout conditions.",
                "Icy pellets fall with such force they sting when they hit.",
            ],
            "day": [
                "Heavy sleet falls in sheets, creating whiteout conditions.",
                "The sleet is so thick visibility is severely reduced.",
                "Icy pellets pound down with incredible force.",
            ],
            "dusk": [
                "The heavy sleet makes evening darkness come early and dangerous.",
                "Evening brings no relief from the torrent of icy pellets.",
                "Heavy sleet continues unabated as darkness approaches.",
            ],
            "night": [
                "Heavy sleet creates a wall of ice in the darkness.",
                "The sleet is so thick it's nearly impossible to see.",
                "Icy pellets fall with such force the night feels like an assault.",
            ],
        },
    },
    "heatwave": {
        "moderate": {
            "dawn": [
                "The morning heat is already oppressive.",
                "Even at dawn, the heat is intense and uncomfortable.",
                "Morning brings no relief from the heatwave.",
            ],
            "day": [
                "The heat is intense, making the air shimmer with heat haze.",
                "Even standing still, the heat is overwhelming.",
                "The heatwave makes everything feel slow and heavy.",
                "Heat radiates from every surface, making the day oppressive.",
            ],
            "dusk": [
                "Evening brings little relief from the intense heat.",
                "The heatwave continues into evening, making it uncomfortable.",
                "Heat still radiates from the ground as evening approaches.",
            ],
            "night": [
                "The night heat is still intense, offering little relief.",
                "Even in darkness, the heatwave makes everything uncomfortable.",
                "Heat radiates from the ground, making the night oppressive.",
            ],
        },
        "heavy": {
            "dawn": [
                "The morning heat is so intense it's already hard to breathe.",
                "Even at dawn, the heatwave is at its peak.",
                "Morning brings no relief from the sweltering heat.",
            ],
            "day": [
                "The heat is so intense it feels like an oven.",
                "Breathing is difficult in the oppressive, heavy heat.",
                "The heatwave has reached dangerous levels.",
                "Heat shimmers in the air, making distant objects waver.",
            ],
            "dusk": [
                "Evening brings no relief—the heatwave continues at full intensity.",
                "The heat is still dangerous even as darkness approaches.",
                "Evening heat continues to radiate from every surface.",
            ],
            "night": [
                "The night heat is still dangerously intense.",
                "Even in darkness, breathing is difficult in the oppressive heat.",
                "The heatwave shows no signs of breaking, even at night.",
            ],
        },
    },
}


def get_weather_message(
    weather_type: str,
    weather_intensity: str,
    time_of_day: str
) -> Optional[str]:
    """
    Get a random weather message for the current conditions.
    
    Args:
        weather_type: Weather type (e.g., "rain", "clear", "storm")
        weather_intensity: Weather intensity (e.g., "light", "moderate", "heavy")
        time_of_day: Time of day ("dawn", "day", "dusk", "night")
    
    Returns:
        Optional message string, or None if no message available
    """
    # DEBUG: Log stack trace to find who is calling this
    # Basic validation
    if weather_type not in WEATHER_MESSAGES:
        return None
    
    intensity_dict = WEATHER_MESSAGES[weather_type]
    
    # Get messages for this intensity
    if weather_intensity not in intensity_dict:
        # Fall back to "none" for clear weather, or return None
        if weather_type == "clear" and "none" in intensity_dict:
            intensity_dict = {"none": intensity_dict["none"]}
        else:
            return None
    
    time_dict = intensity_dict.get(weather_intensity)
    if not time_dict:
        return None
    
    # Get messages for this time of day
    if time_of_day not in time_dict:
        return None
    
    messages = time_dict[time_of_day]
    if not messages:
        return None
    
    return random.choice(messages)


def should_show_weather_message(
    weather_type: str,
    weather_intensity: str
) -> bool:
    """
    Determine if a weather message should be shown.
    
    Some weather conditions are more notable than others.
    We show messages more frequently for active weather to make the world feel alive.
    
    Args:
        weather_type: Current weather type
        weather_intensity: Current intensity
    
    Returns:
        bool: True if a weather message should be shown
    """
    # Always show messages for active/notable weather
    if weather_type != "clear":
        return True
    
    # For clear weather, show messages more frequently (30% chance) to keep world feeling alive
    # This prevents spam but still gives feedback
    if weather_type == "clear" and weather_intensity == "none":
        return random.random() < 0.3
    
    return True

