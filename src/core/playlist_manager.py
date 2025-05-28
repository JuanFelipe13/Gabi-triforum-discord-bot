import json
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class PlaylistManager:
    """Manages user playlists stored in playlists.json."""
    def __init__(self):
        """Initializes the manager and loads playlists from the file."""
        self.playlists: Dict[str, List[Dict]] = {}
        self.load_playlists()

    def load_playlists(self):
        """Loads playlists from the playlists.json file."""
        try:
            if os.path.exists('playlists.json'):
                with open('playlists.json', 'r', encoding='utf-8') as f:
                    self.playlists = json.load(f)
        except Exception as e:
            logger.error(f"Error cargando playlists: {e}")
            self.playlists = {}

    def save_playlists(self):
        """Saves the current playlists to the playlists.json file."""
        try:
            with open('playlists.json', 'w', encoding='utf-8') as f:
                json.dump(self.playlists, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando playlists: {e}")

    def create_playlist(self, user_id: int, name: str) -> bool:
        """Creates a new empty playlist for a user."""
        key = f"{user_id}_{name}"
        if key in self.playlists:
            return False
        self.playlists[key] = []
        self.save_playlists()
        return True

    def add_to_playlist(self, user_id: int, name: str, song: dict) -> bool:
        """Adds a song dictionary to a user's playlist."""
        key = f"{user_id}_{name}"
        if key not in self.playlists:
            return False
        self.playlists[key].append(song)
        self.save_playlists()
        return True

    def remove_from_playlist(self, user_id: int, name: str, index: int) -> bool:
        """Removes a song from a user's playlist by its 1-based index."""
        key = f"{user_id}_{name}"
        if key not in self.playlists:
            return False
        try:
            self.playlists[key].pop(index - 1)
            self.save_playlists()
            return True
        except IndexError:
            return False

    def get_playlist(self, user_id: int, name: str) -> List[Dict]:
        """Retrieves the list of song dictionaries for a user's playlist."""
        key = f"{user_id}_{name}"
        return self.playlists.get(key, [])

    def get_user_playlists(self, user_id: int) -> List[str]:
        """Retrieves a list of playlist names owned by a user."""
        prefix = f"{user_id}_"
        return [
            name.replace(prefix, '') 
            for name in self.playlists.keys() 
            if name.startswith(prefix)
        ]
