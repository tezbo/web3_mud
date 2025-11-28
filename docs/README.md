📚 Aethermoor Documentation Index

For Human Developers & AI Agents Working on web3_mud

Welcome to the documentation hub for Aethermoor, the fantasy MUD built with a modern LPC-inspired architecture, Python systems, JSON templates, Redis-backed state, AI-enhanced NPCs, and a strong immersion-first design philosophy.

This index shows exactly where to start, what to read next, and which documents govern which decisions.

Whether you’re a new contributor, a returning AI agent, or a lore-keeper joining the project for the first time—start here.

⸻

🌟 1. Essential Reading (Start Here)

These documents define what Aethermoor is, how it works, and how to work within this codebase.

⸻

1.1 Agent Foundation & Rules (READ FIRST)

AGENT_FOUNDATION_AND_RULES.md
The canonical guide for all AI agents and new human contributors.

Covers:
	•	Vision (Aethermoor, the Three Realms, Hollowvale, Threadsinging)
	•	Architecture (JSON → Python → Redis)
	•	World/content standards
	•	Rules for safe contributions
	•	Refactor boundaries and prohibited operations
	•	State management philosophy
	•	Testing rules
	•	Required behaviour for multi-agent coordination

This is your contract and operating manual.

⸻

1.2 Lore Primer (World Canon)

LORE_PRIMER.md
Defines the world itself:
	•	History, cosmology, Threadsinging
	•	The Sundering
	•	Cultures of the Three Realms
	•	Tone, materials, aesthetic boundaries
	•	Hollowvale as the first playable region of Aethermoor

All world content must reference this.

⸻

🔧 2. Architecture & Systems Overview

These documents explain how the engine works, where new code belongs, and how state flows.

⸻

2.1 High-Level Architecture

ARCHITECTURE.md
Master blueprint of the entire system:
	•	Module philosophy
	•	“Modern LPC” rationale
	•	Roles of JSON, Python, and Redis
	•	Vision for entity system (Room/NPC/Item classes)
	•	StateStore / TemplateRegistry future design

If you’re designing a new system, start here.

⸻

2.2 Engine Overview

ENGINE_OVERVIEW.md
Detailed breakdown of:
	•	Request/response loop
	•	How Socket.IO & app.py serve players
	•	Command parsing
	•	Room loading
	•	Event propagation
	•	How game_engine.py is being dismantled
	•	Where each subsystem currently lives

If modifying gameplay behaviour, read this.

⸻

2.3 World State & Persistence

WORLD_STATE_AND_PERSISTENCE.md
Explains:
	•	JSON world templates
	•	Runtime entity creation
	•	Dynamic state in game/state.py
	•	Redis-backed StateStore (future)
	•	Render Redis instance (production infra)
	•	DevOps duties for monitoring/maintaining services

Critical for work on state, world loading, persistence and infra.

⸻

2.4 NPC System

NPC_SYSTEM.md
Documents:
	•	NPC template structure
	•	Runtime NPC state
	•	AI vs Non-AI NPC paths
	•	ai_client.py and OpenAI integration
	•	Behaviour flow & reaction hooks
	•	Spawn rules

Required reading for writing or modifying NPCs.

⸻

🎭 3. Experience & Immersion Design

These documents shape how Aethermoor feels, not just how it runs.

⸻

3.1 Development Roadmap

ROADMAP.md
Defines:
	•	Phased development
	•	Feature sets & priorities
	•	Implementation milestones
	•	Hollowvale as the first major region

Aligns engine work with worldbuilding.

⸻

3.2 Immersion-First Roadmap

IMMERSION_ROADMAP.md
Our sensory design guide:
	•	Weather, seasons, day/night
	•	Ambient events & room feel
	•	NPC chatter patterns
	•	Sunrise/sunset hooks
	•	Long-term immersion goals

All world/narrative content should follow these principles.

⸻

🧩 4. Refactors, Workflows & Code Quality

⸻

4.1 Refactor Plan

REFACTOR_PLAN.md
Defines the dismantling of game_engine.py into:
	•	Modular subsystems
	•	Models
	•	Navigation
	•	Combat
	•	Inventory (complete)
	•	NPC movement/behaviour
	•	Command registry

This document defines the allowed path for structural changes.

⸻

4.2 WebSocket Client Example

WEBSOCKET_CLIENT_EXAMPLE.md
Example code showing how to connect to the server via Socket.IO.

Includes:
	•	Login and command flow
	•	Event structure
	•	Production endpoint guidance
	•	Contract expectations between client and app.py

Useful for testers, UI tools, and integration checks.

⸻

🧭 5. Recommended Reading Order (AI Agent Checklist)

Whenever an AI agent starts a task:
	1.	AGENT_FOUNDATION_AND_RULES.md
	2.	LORE_PRIMER.md
	3.	ARCHITECTURE.md
	4.	ENGINE_OVERVIEW.md
	5.	WORLD_STATE_AND_PERSISTENCE.md
	6.	Relevant subsystem docs (NPC_SYSTEM.md, inventory, combat, command registry, etc.)
	7.	The specific JSON templates involved (world/rooms/, world/npcs/, etc.)

⸻

🚀 6. Expectations for All Contributors

All contributions—AI or human—must:
	•	Respect Aethermoor’s lore
	•	Follow architecture patterns (JSON → Python → Redis)
	•	Avoid creating monoliths
	•	Avoid destructive operations without explicit approval
	•	Use the dedicated test character (Agent / agent)
	•	Explain your reasoning before generating major code
	•	Ask when in doubt

⸻

🐉 7. Welcome to the Aethermoor Codebase

With this structure, agents and humans work:
	•	Safely
	•	Predictably
	•	Consistently
	•	Immersively
	•	And with a unified vision

Our goal: build the most immersive, AI-driven text-based MUD ever created — a world that feels alive in every moment.

⸻
