from .player import player


class Monopoly:
    def __init__(self, *, playerCount: int = 4, map: str = "France"):
        self.playerCount = playerCount

        self.players = []

        self.map = Map.load()
