# Tiny Web MUD

A text-based Multi-User Dungeon (MUD) game built with Flask, featuring AI-powered NPCs, an economy system, and multiplayer support.

## Features

- **Multiplayer Support**: Multiple players can explore the world simultaneously
- **AI-Powered NPCs**: NPCs use OpenAI's API for dynamic, contextual dialogue
- **Economy System**: Currency, merchants, pricing, and loot mechanics
- **Reputation System**: Build relationships with NPCs that affect interactions
- **Persistent World**: Shared room state and NPC locations across all players
- **Admin Dashboard**: Monitor AI usage and manage user token budgets

## Local Development

### Prerequisites

- Python 3.12 or higher
- OpenAI API key (optional, for AI NPCs)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/tezbo/web3_mud.git
cd web3_mud
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file (optional, for local development):
```bash
FLASK_SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
```

5. Run the application:
```bash
python3 app.py
```

6. Access the game at `http://localhost:5000`

## Deploy to Render.com

### Prerequisites

- GitHub account: https://github.com/tezbo
- Render.com account

### Steps

#### 1. Push code to GitHub

```bash
cd ~/Documents/code/web3_mud
git init
git add .
git commit -m "Initial Tiny Web MUD"
git branch -M main
git remote add origin https://github.com/tezbo/web3_mud.git
git push -u origin main
```

**Note**: When pushing, GitHub will prompt for credentials:
- **Username**: Your GitHub username (`tezbo`)
- **Password**: Use a [Personal Access Token](https://github.com/settings/tokens) (not your GitHub password)
  - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
  - Generate a new token with `repo` scope
  - Use this token as your password when prompted

#### 2. Deploy on Render

1. Go to [Render.com](https://render.com) and sign in
2. Click **New** → **Web Service**
3. Connect to GitHub and select the `tezbo/web3_mud` repository
4. Configure the service:
   - **Name**: `web3-mud` (or your preferred name)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app`
5. Add environment variables:
   - `FLASK_SECRET_KEY`: Generate a secure random string (e.g., use `openssl rand -hex 32`)
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `OPENAI_MODEL`: `gpt-4o-mini` (or your preferred model)
6. Click **Create Web Service**

### Important Notes

- **State Persistence**: The game uses `mud_state.json` for persisting room state, NPC state, and active player games. 
- **Database**: User accounts and game states are stored in SQLite (`users.db`). 
- **Render Deployment**: By default, data is **NOT persisted** between redeployments. To persist data:
  1. Add a Persistent Disk to your Render service (Settings → Add Disk)
  2. Set the `PERSISTENT_DISK_PATH` environment variable to the mount path (e.g., `/persistent`)
  3. The database and state files will be stored on the persistent disk and survive redeployments
- **Multi-Instance Scaling**: The current persistence mechanism (local JSON file) is **not suitable for multi-instance deployments**. For production scaling, consider using Redis or a database for shared state.

### Deployment Behavior

**Zero-Downtime Deployments**:
- Render supports zero-downtime deployments, but **only for services without persistent disks**
- If you're using `PERSISTENT_DISK_PATH`, each deployment will have brief downtime (typically 5-30 seconds)
- The old instance stops, then the new instance starts with the updated code
- For zero-downtime deployments, consider:
  - Using Render's PostgreSQL database instead of SQLite + persistent disk
  - Using external storage (S3, etc.) instead of persistent disk
  - Accepting brief downtime (deployments are usually very quick)

**Frequent Deployments**:
- Render automatically deploys on every push to the connected branch (usually `main`)
- Each deployment takes 1-3 minutes (build + start time)
- For rapid development with 50-100 commits:
  - Brief downtime is usually acceptable (5-30 seconds per deploy)
  - Consider batching commits or using a staging environment for testing
  - The persistent disk ensures data survives redeployments

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `FLASK_SECRET_KEY` | Secret key for Flask sessions | Yes (production) | `dev-secret-change-me` |
| `OPENAI_API_KEY` | OpenAI API key for AI NPCs | No | - |
| `OPENAI_MODEL` | OpenAI model to use | No | `gpt-4o-mini` |
| `ADMIN_USERS` | Comma-separated list of admin usernames | No | `admin,tezbo` |
| `AI_MAX_REQUESTS_PER_HOUR` | Rate limit for AI requests per user | No | `60` |
| `PORT` | Port to run the server on | No | `5000` |
| `IN_GAME_HOUR_DURATION` | Real-world hours per in-game hour | No | `1.0` |
| `IN_GAME_DAY_DURATION` | Real-world hours per in-game day | No | `2.0` |

## Making a User Admin

There are two ways to make a user an admin:

1. **Environment Variable** (Recommended): Add `ADMIN_USERS=tezbo` to your Render environment variables. This works immediately without database changes.

2. **Database Update**: Use the provided script:
   ```bash
   python3 promote_admin.py tezbo
   ```
   On Render, you can run this via Render Shell (SSH into your service).

## Project Structure

```
web3_mud/
├── app.py                 # Flask application and routes
├── game_engine.py         # Core game logic and command handling
├── ai_client.py          # OpenAI integration for NPC dialogue
├── npc.py                # NPC definitions and management
├── economy/               # Economy system (currency, pricing, merchants)
├── prompts/              # AI prompt templates
├── templates/            # HTML templates
├── utils/                # Utility functions
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Commands

- `look` / `l` - View current location
- `go <direction>` - Move (north, south, east, west)
- `take <item>` - Pick up an item
- `drop <item>` - Drop an item
- `inventory` / `i` - View your inventory
- `talk <npc>` - Talk to an NPC
- `say <message>` - Speak to everyone in the room
- `buy <item>` - Purchase from a merchant
- `list` - See what's for sale
- `who` - List active players
- `time` - Check in-game time
- `help` - Show help message

## License

This project is for personal use and educational purposes.

