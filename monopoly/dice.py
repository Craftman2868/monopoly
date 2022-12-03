from random import randint, random
from time import sleep

from typing import Optional


MIN_POWER = 0.05
MAX_ITER = 4


class Dice:
    def __init__(self, a: int = 6, b: int = 1):
        self.power = 0

        self.min, self.max = min(a, b), max(a, b)

        self.value = randint(self.min, self.max)

        self.rolling = False

        self.time = 0

    def roll(self, power: Optional[float] = None, time: Optional[float] = None):
        self.power = power or 1

        self.time = time or 0

        self.rolling = True
    
        self.value += randint(0, self.max)

        self.value %= self.max - self.min

        self.value += self.min

        return self
        
    def __iter__(self):
        return self
    
    def __next__(self):  # sourcery skip: de-morgan, raise-specific-error, remove-redundant-if, while-guard-to-condition
        if not self.rolling:
            raise Exception("Dice not rolling")

        self.power -= 0.03

        if not self.power or self.power < MIN_POWER:
            self.power = 0
            self.rolling = False
            raise StopIteration
        
        old_value = self.value

        tmp_value = self.value

        i = 0
        while int(tmp_value) == old_value and i < MAX_ITER:
            sleep(self.time)

            if not self.power or self.power < MIN_POWER:
                break

            tmp_value += self.power + self.power ** 2

            self.power = self.power - (self.power ** 2 * (random() / 2))
            
            i += 1

        self.value = int(tmp_value)

        if self.value > self.max:
            self.value = self.min

        if not self.power or self.power < MIN_POWER:
            self.rolling = False
            self.power = 0
            raise StopIteration()

        return self.value, self.power
    
class DiceGroup:
    def __init__(self, *dices: Dice):
        self.dices = dices

        if len(self.dices) < 2:
            raise ValueError("At least 2 dice is required for a DiceGroup")
    
    @property
    def sum(self):
        return sum(d.value for d in self.dices)

    @property
    def max(self):
        return sum(d.max for d in self.dices)

    def roll(self, time: Optional[float] = None, *powers: int):
        _powers = [None] * len(self.dices)

        for i, p in enumerate(powers):
            _powers[i] = p
        
        powers = _powers

        del _powers

        for i, d in enumerate(self.dices):
            d.roll(powers[i], time / len(self.dices))

        while any(d.rolling for d in self.dices):
            for i, d in enumerate(self.dices):
                if not d.rolling:
                    continue

                try:
                    v, p = next(d)
                except StopIteration:
                    continue

                yield i, v, p
    
    def __iter__(self):
        return iter(self.dices)
    
    def __getitem__(self, index: int):
        return self.dices.__getitem__(index)

class DicePair(DiceGroup):
    def __init__(self, dice1: Optional[Dice] = None, dice2: Optional[Dice] = None):
        if dice1 is None:
            dice1 = Dice()
        
        if dice2 is None:
            dice2 = Dice()
        
        super().__init__(dice1, dice2)

    @property
    def double(self):
        return self.dices[0].value == self.dices[1].value


if __name__ == "__main__":
    dices = DicePair()

    for i, v, p in dices.roll(0.1):
        print(f"Dice {i}: {v} ({p})")
    
    print("------------\n")

    for i, d in enumerate(dices):
        print(f"Dice {i}: {d.value}")

    print(f"Score: {dices.sum}")

    if dices.double:
        print("Double !")
