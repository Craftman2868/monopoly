from typing import Iterable, Any

from random import shuffle


class CardStack:
    def __init__(self, cards: Iterable[Any]):
        self.cards = [*cards]
        self.cursor = 0
    
    def mix(self):
        shuffle(self.cards)
        self.cursor = 0

    def draw(self):
        card = self.cards[self.cursor]

        self.cursor += 1

        self.cursor %= len(self.cards) - 1

        return card
