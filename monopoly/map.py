from .space import (
    Space,
    Space_Go, Space_Jail, Space_FreeParking, Space_GoJail,
    Space_Taxe,
    Space_Terrain, Space_Railroad, Space_Company,
    Space_Chance, Space_CommunityChest,

    TERRAIN_COUNT_BY_GROUPS, RAILROAD_COUNT, COMPANY_COUNT, SPACE_COUNT
)
# from .monopoly import Monopoly

import json

from typing import Dict, Any

DEFAULT_MAP = "USA"

MAP_LIST = ["France", "USA"]


with open("monopoly/assets/map/map", "r") as f:
    mapData = [s.strip() for s in f.read().split("\n") if s.strip() != "" and not s.strip().startswith("#")]


def loadSpace(map: "Map", s: str, pos: int):  # sourcery skip: avoid-builtin-shadow, extract-duplicate-method, inline-immediately-returned-variable
    type, *args = s.split(" ")

    if type == "go":
        return Space_Go(map, pos)

    if type == "jail":
        return Space_Jail(map, pos)

    if type == "free_parking":
        return Space_FreeParking(map, pos)

    if type == "go_jail":
        return Space_GoJail(map, pos)

    if type == "taxe":
        if not args:
            raise ValueError()  ## TODO

        id = args[0]

        id = int(id) - 1  ## TODO check

        return Space_Taxe(map, id, pos)

    if type == "terrain":
        if not args:
            raise ValueError()  ## TODO
        
        gid, id = args[0].split(":")  ## TODO check

        gid, id = int(gid) - 1, int(id) - 1  ## TODO check
    
        return Space_Terrain(map, gid, id, pos)

    if type == "railroad":
        if not args:
            raise ValueError()  ## TODO
    
        id = args[0]

        id = int(id) - 1  ## TODO check
    
        return Space_Railroad(map, id, pos)

    if type == "company":
        if not args:
            raise ValueError()  ## TODO
    
        id = args[0]

        id = int(id) - 1  ## TODO check
    
        return Space_Company(map, id, pos)

    if type == "chance":
        return Space_Chance(map, pos)

    if type == "community_chest":
        return Space_CommunityChest(map, pos)

    raise ValueError(f"'{type}' space type not found !")


def loadSpaces(map: "Map"):
    return [loadSpace(map, s, i) for i, s in enumerate(mapData)]


class Map:
    def __init__(self, game: "Monopoly", name: str, data: Dict[str, Any]):
        self.name = name
        self.data = data
        self.game = game

        self.terrains = data.get("terrains", {})

        self.spaces = loadSpaces(self)
    
    def getSpace(self, pos: int):
        return self.spaces[pos % SPACE_COUNT]

    def getGroupColor(self, gid: int):
        return self._getTerrain(gid, 0).color
    
    def getGroupTerrains(self, gid: int):
        return [*(self._getTerrain(gid, id) for id in range(TERRAIN_COUNT_BY_GROUPS[gid]))]

    def _getTerrain(self, gid: int, id: int):
        for s in self.spaces:
            if isinstance(s, Space_Terrain) and s.group_id == gid and s.id == id:
                return s

    def getTerrain(self, gid: int, id: int):
        return self._getTerrain(gid - 1, id - 1)

    def _getRailroad(self, id: int):
        for s in self.spaces:
            if isinstance(s, Space_Railroad) and s.id == id:
                return s

    def getRailroad(self, id: int):
        return self._getRailroad(id - 1)

    def _getCompany(self, id: int):
        for s in self.spaces:
            if isinstance(s, Space_Company) and s.id == id:
                return s

    def getCompany(self, id: int):
        return self._getCompany(id - 1)
    
    def getRailroads(self):
        return [*(self._getRailroad(r) for r in range(RAILROAD_COUNT))]
    
    def getCompanies(self):
        return [*(self._getCompany(c) for c in range(COMPANY_COUNT))]
    
    def getSpecialProperties(self):
        return self.getRailroads() + self.getCompanies()

    @classmethod
    def load(cls, game: "Monopoly", name: str):  # sourcery skip: raise-from-previous-error
        try:
            with open(f"monopoly/assets/map/{name}.json", "r", encoding="utf8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Map file '{name}' not found")

        return cls(game, name, data)
