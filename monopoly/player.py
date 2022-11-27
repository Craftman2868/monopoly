# from .monopoly import monopoly


class Player:
    def __init__(self, game: "Monopoly", money: int = 1500):
        self.game = game
        self.money = money
