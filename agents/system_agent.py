# agents/system_agent.py
"""
SystemAgent – a lightweight autonomous agent that performs core engine modifications
required for high‑quality MUD features (weather line, exits formatting, ambient chatter,
weather‑impact on descriptions, and color‑tag fixes). It runs a simple task loop
independent of content‑generation agents.
"""

from agents.agent_framework import AutonomousAgent


class SystemAgent(AutonomousAgent):
    def __init__(self):
        super().__init__(
            name="System Agent",
            role="Engine Maintenance",
            capabilities=["modify_code", "apply_system_updates"]
        )
        # Define a list of callable tasks that will be executed sequentially.
        self.system_tasks = [
            self.add_weather_line_and_exits_format,
            # self.hook_ambient_weather_chatter,  # Deprecated: Ambiance should be simulation-driven
            self.apply_weather_effects_to_descriptions,
            self.fix_color_tag_rendering,
        ]
        self.current_task_index = 0

    # ---------------------------------------------------------------------
    # Task 1: Insert weather line and re‑format exits in room display.
    # ---------------------------------------------------------------------
    def add_weather_line_and_exits_format(self):
        """Edit `game/models/room.py` to add a dark‑yellow weather line before exits
        and change the exits line to the required wording wrapped in [EXITS] tags.
        """
        from pathlib import Path
        file_path = Path(__file__).parents[1] / "game" / "models" / "room.py"
        content = file_path.read_text()
        # Insert weather line after description block (we already added a placeholder
        # in a previous edit). Ensure we use the [WEATHER] tag for frontend styling.
        new_content = []
        for line in content.splitlines():
            new_content.append(line)
            if line.strip().startswith('output = f"""<div class=\'room-description\''):
                # Insert weather line after description div
                new_content.append("        <div class='room-weather'>[WEATHER]{weather_desc}[/WEATHER]</div>")
            if line.strip().startswith("<div class='room-exits'"):
                # Replace the old exits formatting with the new wording.
                # The placeholder will be filled later by the runtime description.
                new_content.append("        <div class='room-exits'>[EXITS]{exits_str}[/EXITS]</div>")
        file_path.write_text("\n".join(new_content))
        self.log("[System] Updated room display with weather and exits formatting.")

    # ---------------------------------------------------------------------
    # Task 2: Hook ambient weather chatter.
    # ---------------------------------------------------------------------
    def hook_ambient_weather_chatter(self):
        """Ensure ambient system broadcasts weather‑based messages.
        If `game_systems/ambient.py` exists, we import and add a call to
        `AmbientSystem.broadcast_weather()`; otherwise we patch `game_engine.py`
        where ambient messages are processed.
        """
        from pathlib import Path
        ambient_path = Path(__file__).parents[1] / "game" / "systems" / "ambient.py"
        if ambient_path.exists():
            content = ambient_path.read_text()
            if "broadcast_weather" not in content:
                # Append a simple helper at the end of the file.
                content += """

def broadcast_weather():
    from game_engine import get_weather_message
    msg = get_weather_message()
    if msg:
        from game.world.manager import WorldManager
        from game_engine import broadcast_to_room
        wm = WorldManager.get_instance()
        for room_id in wm.active_rooms:
            broadcast_to_room(room_id, msg)
"""
                ambient_path.write_text(content)
                self.log("[System] Added broadcast_weather to ambient system.")
        else:
            self.log("[System] ambient system already has broadcast_weather.")
        # Ensure the ambient polling loop calls this function – patch `app.py`.
        app_path = Path(__file__).parents[1] / "app.py"
        app_content = app_path.read_text()
        if "broadcast_weather()" not in app_content:
            # Insert call after ambient polling start.
            marker = "current_tick = get_current_game_tick()"
            if marker in app_content:
                app_content = app_content.replace(marker, f"{marker}\n    from game.systems.ambient import broadcast_weather\n    broadcast_weather()")
                app_path.write_text(app_content)
                self.log("[System] Hooked ambient weather chatter into app polling.")
        else:
            self.log("[System] Ambient polling already calls broadcast_weather.")
        return

    # ---------------------------------------------------------------------
    # Task 3: Apply weather effects to player/NPC descriptions.
    # ---------------------------------------------------------------------
    def apply_weather_effects_to_descriptions(self):
        """Update description helpers in `game_engine.py` to add graduated phrases.
        We look for the `_format_player_look` and `_format_other_player_look`
        functions and inject a small snippet that checks `weather_status` and
        appends a line like "He looks positively drenched!" when appropriate.
        """
        from pathlib import Path
        engine_path = Path(__file__).parents[1] / "game_engine.py"
        content = engine_path.read_text().splitlines()
        new_lines = []
        for i, line in enumerate(content):
            new_lines.append(line)
            # Insert after the opening of the description list in player look.
            if line.strip().startswith("lines = [\"You look at yourself.\"]"):
                insert = (
                    "    # Weather impact – add graduated description if outdoors\n"
                    "    if game.get('weather_status') and game.get('outdoor'):\n"
                    "        ws = game['weather_status']\n"
                    "        wet = ws.get('wetness', 0)\n"
                    "        if wet >= 5:\n"
                    "            lines.append('He looks positively drenched!')\n"
                )
                new_lines.extend(insert.split('\n'))
            # Same for other player look.
            if line.strip().startswith("lines = [f\"You look at {target_username}.\"]"):
                insert = (
                    "    # Weather impact for other players\n"
                    "    if target_game.get('weather_status') and target_game.get('outdoor'):\n"
                    "        ws = target_game['weather_status']\n"
                    "        wet = ws.get('wetness', 0)\n"
                    "        if wet >= 5:\n"
                    "            lines.append(f\"{pronoun_cap} looks positively drenched!\")\n"
                )
                new_lines.extend(insert.split('\n'))
        engine_path.write_text("\n".join(new_lines))
        self.log("[System] Added weather‑impact description snippets.")

    # ---------------------------------------------------------------------
    # Task 4: Fix color‑tag rendering in the frontend.
    # ---------------------------------------------------------------------
    def fix_color_tag_rendering(self):
        """Update `templates/index.html` processing to replace [WEATHER] and [EXITS]
        tags with styled spans using the dark‑yellow and dark‑green colors.
        """
        from pathlib import Path
        tmpl_path = Path(__file__).parents[1] / "templates" / "index.html"
        content = tmpl_path.read_text().splitlines()
        new_content = []
        for line in content:
            # Replace existing generic tag handling with explicit WEATHER and EXITS.
            if "processed = processed.replace(/\\\\[WEATHER\\\\]/" in line:
                new_content.append(
                    "        processed = processed.replace(/\\\\[WEATHER\\\\](.*?)\\\\[\\\\/WEATHER\\\\]/g, (match, content) => {"
                )
                new_content.append(
                    "          return `<span style=\"color: ${getColorForType('weather')}; font-weight: 500;\">${content}</span>`;"
                )
                new_content.append("        });")
                continue
            if "processed = processed.replace(/\\\\[EXITS\\\\]/" in line:
                new_content.append(
                    "        processed = processed.replace(/\\\\[EXITS\\\\](.*?)\\\\[\\\\/EXITS\\\\]/g, (match, content) => {"
                )
                new_content.append(
                    "          return `<span style=\"color: ${getColorForType('exits')}; font-weight: 500;\">${content}</span>`;"
                )
                new_content.append("        });")
                continue
            new_content.append(line)
        tmpl_path.write_text("\n".join(new_content))
        self.log("[System] Fixed frontend color‑tag rendering for WEATHER and EXITS.")

    # ---------------------------------------------------------------------
    # Execution loop – runs each system task once, then pauses.
    # ---------------------------------------------------------------------
    def run_loop(self):
        while self.current_task_index < len(self.system_tasks):
            task = self.system_tasks[self.current_task_index]
            try:
                task()
            except Exception as e:
                self.log(f"[System] Error in task {task.__name__}: {e}")
            self.current_task_index += 1
            # Small pause to avoid hogging CPU.
            import time
            time.sleep(0.5)
        self.log("[System] All system tasks completed.")

if __name__ == "__main__":
    agent = SystemAgent()
    agent.run_loop()
