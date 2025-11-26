"""
Quest Model
Defines the structure for Quests and Quest Templates.
"""
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field
import time

if TYPE_CHECKING:
    from game.models.player import Player

@dataclass
class QuestTemplate:
    """Defines a quest template (global definition)."""
    id: str
    name: str
    description: str
    giver_id: str
    difficulty: str
    category: str
    timed: bool
    time_limit_minutes: Optional[int]
    actors: List[str]
    stages: List[Dict]
    rewards: Dict
    offer_sources: List[Dict]
    failure_reputation: Optional[Dict] = None
    shared: bool = True
    max_players: Optional[int] = None
    newbie_priority: bool = False
    max_per_player: Optional[int] = None
    reputation_requirement: Optional[Dict[str, int]] = None
    level_range: Optional[tuple] = None

class Quest:
    """
    Represents an active quest instance for a player.
    """
    def __init__(self, template: QuestTemplate, player_username: str):
        self.template = template
        self.player_username = player_username
        self.status = "active"  # active, completed, failed
        self.started_at = time.time()
        self.completed_at: Optional[float] = None
        self.current_stage_index = 0
        self.objectives_state: Dict[int, Dict[str, bool]] = {} # stage_index -> {obj_id -> completed}
        self.notes: List[str] = [f"Quest started: {template.name}"]
        
        # Initialize first stage note
        if template.stages:
            first_stage = template.stages[0]
            self.notes.append(f"Objective: {first_stage.get('description', 'Begin your quest.')}")

    @property
    def id(self) -> str:
        return self.template.id

    @property
    def name(self) -> str:
        return self.template.name

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for legacy compatibility/persistence."""
        return {
            "id": self.id,
            "template_id": self.template.id,
            "status": self.status,
            "giver_id": self.template.giver_id,
            "started_at_tick": int(self.started_at), # Approximation
            "current_stage_index": self.current_stage_index,
            "objectives_state": self.objectives_state,
            "notes": self.notes,
            "difficulty": self.template.difficulty
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], template: QuestTemplate) -> 'Quest':
        """Load from dictionary."""
        quest = cls(template, data.get("username", "unknown")) # Username might need to be passed in
        quest.status = data.get("status", "active")
        quest.current_stage_index = data.get("current_stage_index", 0)
        quest.objectives_state = data.get("objectives_state", {})
        quest.notes = data.get("notes", [])
        return quest

    def update(self, event: Dict[str, Any], game_state: Dict[str, Any]) -> bool:
        """
        Process an event and update quest progress.
        Returns True if quest state changed (e.g. stage completed).
        """
        if self.status != "active":
            return False

        if self.current_stage_index >= len(self.template.stages):
            return False

        current_stage = self.template.stages[self.current_stage_index]
        objectives = current_stage.get("objectives", [])
        
        # Ensure state dict exists for this stage
        if self.current_stage_index not in self.objectives_state:
            self.objectives_state[self.current_stage_index] = {}

        stage_completed = True
        state_changed = False

        for objective in objectives:
            obj_id = objective.get("id", "")
            
            # Skip if already completed
            if self.objectives_state[self.current_stage_index].get(obj_id, False):
                continue

            # Check if event satisfies objective
            if self._check_objective(objective, event, game_state):
                self.objectives_state[self.current_stage_index][obj_id] = True
                self.notes.append(f"Completed: {objective.get('description', 'Objective')}")
                state_changed = True
            else:
                stage_completed = False

        if stage_completed:
            self.current_stage_index += 1
            state_changed = True
            if self.current_stage_index < len(self.template.stages):
                next_stage = self.template.stages[self.current_stage_index]
                self.notes.append(f"New Objective: {next_stage.get('description', 'Continue quest.')}")
            else:
                # All stages done, ready to complete
                # Note: Actual completion might require returning to NPC
                pass

        return state_changed

    def _check_objective(self, objective: Dict, event: Dict, game_state: Dict) -> bool:
        """Check if a single objective is met by the event."""
        obj_type = objective.get("type")
        event_type = event.get("type")

        if obj_type == "go_to_room" and event_type == "enter_room":
            return event.get("room_id") == objective.get("room_id")
            
        elif obj_type == "talk_to_npc" and event_type == "talk_to_npc":
            return event.get("npc_id") == objective.get("npc_id")
            
        elif obj_type == "say_to_npc" and event_type == "say_to_npc":
            if event.get("npc_id") != objective.get("npc_id"):
                return False
            keywords = objective.get("keywords", [])
            text = event.get("text", "").lower()
            if not keywords:
                return True
            return any(k.lower() in text for k in keywords)
            
        elif obj_type == "obtain_item":
            if event_type == "take_item":
                return event.get("item_id") == objective.get("item_id")
            # Also check inventory check (passive)
            # This requires access to player inventory which might be in game_state
            # For now, we rely on the event triggering it
            
        elif obj_type == "deliver_item":
            if event_type == "give_item":
                return (event.get("item_id") == objective.get("item_id") and 
                        event.get("npc_id") == objective.get("npc_id"))
        
        return False
