import urllib.request
import json
import random
from typing import Dict, Any, List


class GenshinHttpClient:
    """HTTP client with automatic offline fallback for character data."""

    BASE_URL = "https://genshin.jmp.blue"

    def _fetch_json(self, endpoint: str) -> Any:
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception:
            return self._get_local_fallback(endpoint)

    def fetch_character_list(self) -> List[str]:
        return self._fetch_json("characters")

    def fetch_character_details(self, char_id: str) -> Dict[str, Any]:
        return self._fetch_json(f"characters/{char_id.lower()}")

    @staticmethod
    def generate_stats_by_rarity(rarity: int) -> Dict[str, int]:
        if rarity == 5:
            return {"hp": random.randint(110, 160), "armor": random.randint(12, 20), "attack": random.randint(18, 26)}
        return {"hp": random.randint(80, 110), "armor": random.randint(6, 12), "attack": random.randint(10, 17)}

    def _get_local_fallback(self, endpoint: str) -> Any:
        if endpoint == "characters":
            return ["albedo", "diluc", "kaeya"]

        if "characters/albedo" in endpoint:
            return {
                "name": "Albedo",
                "rarity": 5,
                "weapon": "Sword",
                "description": "Chief Alchemist of the Knights of Favonius.",
                "skillTalents": [
                    {"name": "Favonius Bladework", "description": "Perform up to 5 rapid strikes."},
                    {"name": "Abiogenesis: Solar Isotoma", "description": "Deals AoE Geo damage."}
                ]
            }
        elif "characters/diluc" in endpoint:
            return {
                "name": "Diluc",
                "rarity": 5,
                "weapon": "Claymore",
                "description": "The uncrowned king of Mondstadt.",
                "skillTalents": [
                    {"name": "Searing Onslaught", "description": "Performs a forward slash dealing Pyro damage."}
                ]
            }
        elif "characters/" in endpoint:
            name = endpoint.split("/")[-1].capitalize()
            return {
                "name": name,
                "rarity": 4,
                "weapon": "Sword",
                "description": f"Adventurer {name} synced from fallback catalog.",
                "skillTalents": [{"name": "Basic Strike", "description": "Deals direct combat damage."}]
            }
        return {}
