import json
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class PlaylistManager:
    def __init__(self):
        self.playlists: Dict[str, List[Dict]] = {}
        self.load_playlists()

    def load_playlists(self):
        try:
            if os.path.exists('playlists.json'):
                with open('playlists.json', 'r', encoding='utf-8') as f:
                    self.playlists = json.load(f)
        except Exception as e:
            logger.error(f"Error cargando playlists: {e}")
            self.playlists = {}

    def save_playlists(self):
        try:
            with open('playlists.json', 'w', encoding='utf-8') as f:
                json.dump(self.playlists, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando playlists: {e}")

    def create_playlist(self, user_id: int, name: str) -> bool:
        key = f"{user_id}_{name}"
        if key in self.playlists:
            return False
        self.playlists[key] = []
        self.save_playlists()
        return True

    def add_to_playlist(self, user_id: int, name: str, song: dict) -> bool:
        key = f"{user_id}_{name}"
        if key not in self.playlists:
            return False
        self.playlists[key].append(song)
        self.save_playlists()
        return True

    def remove_from_playlist(self, user_id: int, name: str, index: int) -> bool:
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
        key = f"{user_id}_{name}"
        return self.playlists.get(key, [])

    def get_user_playlists(self, user_id: int) -> List[str]:
        prefix = f"{user_id}_"
        return [
            name.replace(prefix, '') 
            for name in self.playlists.keys() 
            if name.startswith(prefix)
        ]
