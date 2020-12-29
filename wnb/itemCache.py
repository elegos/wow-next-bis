from dataclasses import dataclass, field
from os.path import dirname, realpath, sep, exists
from sys import argv
from typing import Optional

import json


def getCacheFilePath(path: Optional[str]) -> str:
    if path is not None and path != '':
        return path

    return f'{dirname(realpath(argv[0]))}{sep}.wnb.itemCache.json'


@dataclass
class ItemCache:
    cacheLocation: str = field(default='')

    def loadCache(self) -> 'ItemCache':
        if hasattr(self, '_cache'):
            return self

        path = getCacheFilePath(self.cacheLocation)
        if not exists(path):
            self._cache = {}

            return self

        with open(path) as f:
            self._cache = json.load(f)

        return self

    def writeCache(self):
        if not hasattr(self, '_cache'):
            return

        with open(getCacheFilePath(self.cacheLocation), 'w') as f:
            json.dump(self._cache, f)

    def setItem(self, id: int, data: dict) -> 'ItemCache':
        if not hasattr(self, '_cache'):
            self._cache = {}

        self._cache[id] = data

        return self

    def getItem(self, id: int) -> Optional[dict]:
        if not hasattr(self, '_cache'):
            self._cache = {}

        return self._cache[f'{id}'] if f'{id}' in self._cache else None


_itemCache = None


def getItemCache(cacheLocation: str = '') -> ItemCache:
    global _itemCache
    if _itemCache is None:
        _itemCache = ItemCache(cacheLocation)

    return _itemCache
