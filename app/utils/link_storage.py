import uuid
from typing import Dict

# Простое in-memory хранилище ссылок (id -> url)
class LinkStorage:
    def __init__(self):
        self._storage: Dict[str, str] = {}

    def add(self, url: str) -> str:
        link_id = str(uuid.uuid4())[:8]  # короткий id
        self._storage[link_id] = url
        return link_id

    def get(self, link_id: str) -> str:
        return self._storage.get(link_id)

    def remove(self, link_id: str):
        self._storage.pop(link_id, None)

link_storage = LinkStorage()
