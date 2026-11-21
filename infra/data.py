import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from core.characters import Character


class ISerializer(ABC):
    @abstractmethod
    def serialize(self, data: Any) -> str: pass

    @abstractmethod
    def deserialize(self, raw_data: str) -> Any: pass


class JSONDataMapper(ISerializer):
    def serialize(self, data: Any) -> str:
        return json.dumps(data, indent=4, ensure_ascii=False)

    def deserialize(self, raw_data: str) -> Any:
        return json.loads(raw_data)


class FileStorageRepository:
    """Handles JSON persistence for character catalogs, match logs, and lore documents."""

    def __init__(self, storage_dir: str = "storage", serializer: ISerializer = None):
        self._storage_dir = storage_dir
        self._serializer = serializer or JSONDataMapper()
        os.makedirs(self._storage_dir, exist_ok=True)

    def save_characters(self, characters: List[Character], filename: str = "characters.json") -> str:
        path = os.path.join(self._storage_dir, filename)
        payload = [c.to_dict() for c in characters]
        with open(path, "w", encoding="utf-8") as f:
            f.write(self._serializer.serialize(payload))
        return path

    def load_characters(self, filename: str = "characters.json") -> List[Character]:
        path = os.path.join(self._storage_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Saved catalog not found at {path}")
        with open(path, "r", encoding="utf-8") as f:
            raw = self._serializer.deserialize(f.read())
        return [Character.from_dict(item) for item in raw]

    def save_match_result(self, summary: Dict[str, Any], filename: str = "game_results.json") -> str:
        path = os.path.join(self._storage_dir, filename)
        history = []
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                history = self._serializer.deserialize(f.read())
        history.append(summary)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self._serializer.serialize(history))
        return path

    def save_text_document(self, content: str, filename: str) -> str:
        path = os.path.join(self._storage_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path
