"""
Quest Manager
Handles quest registration, assignment, and event processing.
"""
from typing import Dict, List, Optional, Any
from game.models.quest import Quest, QuestTemplate
from game.models.player import Player

class QuestManager:
    _instance = None
    
    def __init__(self):
        self.templates: Dict[str, QuestTemplate] = {}
        
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
        
    def register_template(self, template: QuestTemplate):
        """Register a quest definition."""
        self.templates[template.id] = template
        
    def get_template(self, quest_id: str) -> Optional[QuestTemplate]:
        return self.templates.get(quest_id)
        
    def initialize_quests(self):
        """Initialize default quests."""
        # Lost Package quest
        lost_package_template = QuestTemplate(
            id="lost_package",
            name="Lost Package",
            description="Mara has misplaced a small package in the stock room behind her tavern. She needs someone to help her find it and bring it back.",
            giver_id="npc:innkeeper",
            difficulty="Easy",
            category="Errand",
            timed=False,
            time_limit_minutes=None,
            actors=["innkeeper"],
            stages=[
                {
                    "id": "talk_to_mara",
                    "description": "Talk to Mara and offer to help her find the lost package.",
                    "objectives": [
                        {
                            "id": "talk_to_mara_obj",
                            "type": "talk_to_npc",
                            "npc_id": "innkeeper"
                        },
                        {
                            "id": "say_help_obj",
                            "type": "say_to_npc",
                            "npc_id": "innkeeper",
                            "keywords": ["help", "what's wrong", "can I help", "assist", "package"]
                        }
                    ]
                },
                {
                    "id": "find_package",
                    "description": "Find the lost package in the stock room behind the tavern.",
                    "objectives": [
                        {
                            "id": "go_to_stock_room",
                            "type": "go_to_room",
                            "room_id": "tavern"  # The package is in the tavern (back room could be added later)
                        },
                        {
                            "id": "obtain_package",
                            "type": "obtain_item",
                            "item_id": "lost_package"
                        }
                    ]
                },
                {
                    "id": "return_package",
                    "description": "Return the package to Mara at the tavern.",
                    "objectives": [
                        {
                            "id": "deliver_to_mara",
                            "type": "deliver_item",
                            "item_id": "lost_package",
                            "npc_id": "innkeeper",
                            "room_id": "tavern"
                        }
                    ]
                }
            ],
            rewards={
                "currency": {"amount": 5, "currency_type": "silver"},
                "reputation": [
                    {"target": "npc:innkeeper", "amount": 5, "reason": "Helped recover her package"}
                ],
                "items": [
                    {
                        "item_id": "mara_lucky_charm",
                        "quantity": 1,
                        "quest_item": True
                    }
                ]
            },
            offer_sources=[
                {
                    "type": "npc_dialogue",
                    "npc_id": "innkeeper",
                    "trigger": {
                        "kind": "say_contains",
                        "keywords": ["help", "what's wrong", "can I help", "package", "lost"]
                    },
                    "offer_text": "Mara looks up, clearly relieved. 'Oh, thank goodness. I've lost a small parcel somewhere in the stock room. Could you help me find it?'"
                }
            ],
            failure_reputation=None,
            shared=False,
            max_players=1,
            newbie_priority=True,
            max_per_player=None
        )
        self.register_template(lost_package_template)
        
        # Mara's Lost Item quest
        mara_lost_item_template = QuestTemplate(
            id="mara_lost_item",
            name="Mara's Lost Kitchen Knife",
            description="Mara the innkeeper has lost her favorite kitchen knife somewhere in town. She needs someone to help her find it because she can't leave the tavern with customers to serve.",
            giver_id="npc:innkeeper",
            difficulty="Easy",
            category="Errand",
            timed=False,
            time_limit_minutes=None,
            actors=["innkeeper"],
            stages=[
                {
                    "id": "offer_help",
                    "description": "Ask Mara what's wrong and offer to help find her lost item.",
                    "objectives": [
                        {
                            "id": "talk_to_mara",
                            "type": "talk_to_npc",
                            "npc_id": "innkeeper"
                        },
                        {
                            "id": "offer_help_obj",
                            "type": "say_to_npc",
                            "npc_id": "innkeeper",
                            "keywords": ["help", "what's wrong", "what have you lost", "how can i help", "can i help", "what happened"]
                        }
                    ]
                },
                {
                    "id": "find_knife",
                    "description": "Search around town to find Mara's lost kitchen knife.",
                    "objectives": [
                        {
                            "id": "obtain_knife",
                            "type": "obtain_item",
                            "item_id": "mara_kitchen_knife"
                        }
                    ]
                },
                {
                    "id": "return_knife",
                    "description": "Return the kitchen knife to Mara at the tavern.",
                    "objectives": [
                        {
                            "id": "deliver_knife",
                            "type": "deliver_item",
                            "item_id": "mara_kitchen_knife",
                            "npc_id": "innkeeper",
                            "room_id": "tavern"
                        }
                    ]
                }
            ],
            rewards={
                "currency": {"amount": 3, "currency_type": "silver"},
                "reputation": [
                    {"target": "npc:innkeeper", "amount": 8, "reason": "Helped recover her kitchen knife"}
                ],
                "items": [
                    {
                        "item_id": "mara_kitchen_knife",
                        "quantity": 1,
                        "quest_item": False
                    }
                ]
            },
            offer_sources=[
                {
                    "type": "npc_dialogue",
                    "npc_id": "innkeeper",
                    "trigger": {
                        "kind": "say_contains",
                        "keywords": ["help", "what's wrong", "what have you lost", "how can i help", "can i help", "what happened", "lost"]
                    },
                    "offer_text": "Mara looks up with relief. 'Oh, thank you! I've lost my favorite kitchen knife somewhere in town. I've been searching everywhere, but I can't leave the tavern with all these customers to tend to. Could you help me find it? I was out doing errands earlier - it could be anywhere around the town square or market lane. Please, I'll make it worth your while!'"
                }
            ],
            failure_reputation=None,
            shared=False,
            max_players=1,
            newbie_priority=True,
            max_per_player=1
        )
        self.register_template(mara_lost_item_template)

    def start_quest(self, player: Player, quest_id: str) -> tuple[bool, str]:
        """
        Start a quest for a player.
        Returns (success, message).
        """
        template = self.get_template(quest_id)
        if not template:
            return False, "Quest not found."
            
        # Check if already active
        if quest_id in player.quests:
            return False, f"You are already working on '{template.name}'."
            
        # Check if already completed (and not repeatable)
        if quest_id in player.completed_quests:
            # TODO: Check repeatable flag
            return False, f"You have already completed '{template.name}'."
            
        # Create instance
        quest = Quest(template, player.username)
        player.quests[quest_id] = quest
        
        # Trigger any start logic (spawning items, etc)
        self._on_quest_start(quest)
        
        return True, f"You accept the quest: {template.name}.\n{template.description}"

    def handle_event(self, player: Player, event: Dict[str, Any], game_state: Dict[str, Any]):
        """
        Dispatch an event to all of the player's active quests.
        """
        for quest in player.quests.values():
            if quest.status == "active":
                changed = quest.update(event, game_state)
                if changed:
                    # Notify player of update
                    # This requires a way to send message to player. 
                    # For now we might just rely on the return value or side effects.
                    pass
                    
                # Check for completion
                if quest.current_stage_index >= len(quest.template.stages):
                    # Auto-complete if no final interaction needed?
                    # Usually we wait for a "complete_quest" trigger or talk to NPC
                    pass

    def _on_quest_start(self, quest: Quest):
        """Handle side effects of starting a quest (e.g. spawning items)."""
        # This logic was previously hardcoded in start_quest.
        # Ideally this should be data-driven in the template.
        pass
