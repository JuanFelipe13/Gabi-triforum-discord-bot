# Project Documentation

## 1. Overview

This Discord bot provides music playback, playlist management (via `playlists.json`), and Twitter/X video embedding. It includes a supplementary Flask web interface for music search, basic playlist interaction, and weather display.

## 2. Project Structure

```
├── src/
│   ├── core/
│   │   ├── __init__.py           # Core package init
│   │   ├── bot.py                # Main Bot class
│   │   ├── constants.py          # Constants (URLs, yt-dlp/ffmpeg options)
│   │   ├── music_player.py       # Guild-specific music playback & queue
│   │   ├── playlist_manager.py   # Playlist loading/saving (playlists.json)
│   │   └── state.py              # Global store for active MusicPlayer instances
│   ├── commands/
│   │   ├── __init__.py           # Commands package init & cog setup
│   │   ├── music.py              # Music playback commands
│   │   ├── playlist.py           # Playlist management commands
│   │   ├── twitter.py            # Twitter integration command & listener
│   │   └── utils.py              # Command utility functions
│   ├── web/
│   │   ├── __init__.py           # Web package init
│   │   ├── app.py                # Flask web application & API
│   │   └── templates/
│   │       ├── index.html        # Main web UI page
│   │       └── weather.html      # Weather web UI page
│   ├── __init__.py               # Src package init
│   └── core.py                 # Deprecated bot file
├── .env                        # Environment variables (DISCORD_TOKEN)
├── config.json                 # Optional configuration (prefix)
├── playlists.json              # Saved user playlists
├── requirements.txt            # Python dependencies
└── documentation.md            # This documentation
```

## 3. Core Components (`src/core`)

*   **`bot.py`:** Defines `MusicBot`. Handles connection, configuration, prefix logic, event processing (e.g., `on_voice_state_update`), and extension loading.
*   **`constants.py`:** Defines shared constants like `URL_REGEX`, `YTDLP_OPTIONS`, `FFMPEG_OPTIONS`.
*   **`music_player.py`:** Defines `MusicPlayer`. Manages per-guild audio queue, stream extraction (`yt-dlp`), playback (`FFmpegOpusAudio`), and state.
*   **`playlist_manager.py`:** Defines `PlaylistManager`. Handles CRUD operations for user playlists stored in `playlists.json`.
*   **`state.py`:** Provides the global `players` dictionary mapping guild IDs to `MusicPlayer` instances.

## 4. Commands (`src/commands`)

Implemented as `discord.py` Cogs loaded via `src.commands.__init__.py`.

*   **`music.py`:** Contains `MusicCommands` (e.g., `!play`, `!skip`, `!queue`, `!stop`, `!leave`, `!remove`).
*   **`playlist.py`:** Contains `PlaylistCommands` (e.g., `!createlist`, `!addtolist`, `!showlist`, `!playlist`, `!mylists`).
*   **`twitter.py`:** Contains `TwitterCommands` (`!twitter on/off`) and the `on_message` listener for auto-posting videos from links.
*   **`utils.py`:** Shared functions for commands, including `get_player`, `handle_search`, `handle_url`.

## 5. Web Interface (`src/web`)

A Flask application defined in `app.py`.

*   **`app.py`:** Creates the Flask app, defines routes (`/`, `/weather`), and API endpoints (`/api/status`, `/api/playlists`, `/api/search`, `/api/playlist/add`, `/api/weather`). Includes Swagger UI setup (`/swagger`). Launched via `init_web`.
*   **`templates/`:** Contains `index.html` (main UI) and `weather.html`.

## 6. Usage

### Setup

1.  **Install Dependencies:** `pip install -r requirements.txt`. Requires Python and FFmpeg (in system PATH).
2.  **Configure Token:** Create `.env` file with `DISCORD_TOKEN=YOUR_BOT_TOKEN`.
3.  **(Optional) Configure Prefix:** Modify `config.json` to change the default command prefix (`!`).
4.  **Run:** Execute the bot's main entry point script.

### Discord Commands

*(Assumes `!` prefix)*

**Music:**

*   `!play [query/URL]`: Play/add song/playlist or search; resumes if paused/stopped.
*   `!stop`: Pause playback.
*   `!resume`: Resume playback.
*   `!skip`: Skip current track.
*   `!queue` / `!q`: Display queue.
*   `!remove <index>`: Remove track by index.
*   `!next <index>`: Move track by index to front.
*   `!playnow [query/URL]`: Play immediately, queueing current track after.
*   `!shuffle`: Shuffle queue.
*   `!clean`: Clear queue and stop playback.
*   `!leave`: Disconnect bot.

**Playlists:**

*   `!createlist <name>`: Create playlist.
*   `!addtolist <name> <query/URL>`: Add song to playlist.
*   `!removefromlist <name> <index>`: Remove song from playlist by index.
*   `!showlist <name>`: Display playlist contents.
*   `!playlist <name>`: Add playlist to queue.
*   `!mylists`: List user's playlists.

**Twitter:**

*   `!twitter on/off`: Toggle auto-video posting for the channel.
*   `!twitter`: Check current status for the channel.
    *(Posts videos from `twitter.com`/`x.com` links if enabled)*

### Web Interface

1.  **Access:** Navigate to the host/port specified during bot startup (default `http://127.0.0.1:8000`).
2.  **Features:**
    *   **Search (`/`):** Find YouTube tracks via `/api/search`.
    *   **Playlists (`/`):** View playlists (`/api/playlists`), add songs from search (`/api/playlist/add`).
    *   **Weather (`/weather`):** Check weather via `/api/weather`.
    *   **API Docs (`/swagger`):** View API specification.