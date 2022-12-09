# from .monopoly import monopoly
from .space import TERRAIN_COUNT_BY_GROUPS, Space, OwnableSpace, SPACE_COUNT

from typing import Optional, List


class Player:
    def __init__(self, game: "Monopoly", id: int, *, name: Optional[str] = None, money: int = 1500, pos: int = 0):
        self.id = id
        self.game = game
        self.money = money
        self.dead = False
        self.pos = pos

        self.map = self.game.map

        self.ownedSpaces: List[Space] = []

        self.rentMultiplier = 1

        self.inJail = False
        self.jailTurnCount = 0

        self.cards = []

        self.name = name

    @property
    def renderer(self):
        return self.game.renderer
    
    @property
    def space(self):
        return self.game.map.getSpace(self.pos)
    
    @property
    def ownedGroups(self):
        return [*(gid for gid in range(8) if self.hasGroup(gid))]
    
    def giveSpace(self, space: OwnableSpace):
        assert isinstance(space, OwnableSpace)

        self.ownedSpaces.append(space)

        space.owner = self
    
    def countHouses(self):
        return sum(s.houseCount for s in self.ownedSpaces if s.type == "terrain")

    def countHotels(self):
        return sum(s.hotelCount for s in self.ownedSpaces if s.type == "terrain")
    
    def hasGroup(self, gid: int):
        if gid < 0 or gid >= len(TERRAIN_COUNT_BY_GROUPS):
            return False

        terrainCount = sum(s.type == "terrain" and s.group_id == gid for s in self.ownedSpaces)

        assert terrainCount <= TERRAIN_COUNT_BY_GROUPS[gid]

        return terrainCount == TERRAIN_COUNT_BY_GROUPS[gid]

    def multiplyRent(self, multiplier: int):
        self.rentMultiplier = multiplier

    def countSpaceType(self, spaceType: type):
        return sum(isinstance(s, spaceType) for s in self.ownedSpaces)

    def ask(self, question: str, yn: bool = True):
        return self.renderer.askPlayerQuestion(self, question, yn)
    
    def render(self, score: Optional[int] = None, double: Optional[bool] = None):
        self.renderer.renderPlayer(self, score, double)
    
    def play(self, score: int, double: bool):
        do_render = False

        self.advance(score)

        self.render(score, double)

        space = None

        while self.space != space:
            space = self.space

            if self.do_space(score):
                do_render = True

        self.rentMultiplier = 1

        if self.money < 0:
            self.dead = True

            raise NotImplementedError("Player dead")
        
        return do_render

    def receiveSalary(self):
        self.renderer.playerMessage(self, "salary")

        self.give(200)

    def goto(self, pos: int):
        if pos < self.pos:
            self.receiveSalary()

        self.pos = pos

    def gotoTerrain(self, gid: int, id: int):
        print(self.map.getTerrain(gid, id))
        self.goto(self.map.getTerrain(gid, id).pos)

    def gotoRailroad(self, id: int):
        self.goto(self.map.getRailroad(id).pos)
    
    def getNearest(self, type: str):
        pos = self.pos + 1

        while pos != self.pos:
            s = self.map.getSpace(pos)

            if s.type == type:
                return s

            pos += 1
    
    def gotoNearest(self, type: str):
        if s := self.getNearest(type):
            self.goto(s.pos)

    def gotoTerrain(self, gid: int, id: int):
        self.goto(self.map.getTerrain(gid, id).pos)
    
    def advance(self, score: int):  # sourcery skip: class-extract-method
        self.pos += score

        if self.pos >= SPACE_COUNT or self.pos < 0:
            print(self.pos)
            self.pos %= SPACE_COUNT
            print(self.pos)

            self.receiveSalary()
        
    def moveBack(self, score: int):
        self.advance(-score)

    def do_space(self, score: int):
        return self.space.on_pass(self, score)

    def give(self, amount: int):
        self.money += amount
    
    def pay(self, amount: int, to: Optional["Player"] = None):
        self.money -= amount

        ## TODO: check enough money

        if self.money < 0:
            self.dead = True

            raise NotImplementedError("Player dead")

        if to:
            to.give(amount)
    
    def giveCard(self, card: str):
        self.cards.append(card)

    def menu(self, canRollDices: bool = True, do_render: bool = True, has_played: bool = True):
        return self.renderer.playerMenu(self, canRollDices, do_render, has_played)

    def goJail(self):
        self.inJail = True

        self.pos = 10  # JAIL
    
    def getOutJail(self, score: int, double: int):
        self.inJail = False
        self.jailTurnCount = 0

        return self.play(score, double)

    def menuMortgage(self, space: Space):
        assert space.mortgage == False

        space.mortgage = True

        self.renderer.playerMessage(self, "playerMortgageProp", space = space)

        self.give(space.mortgagePrice)
    
    def menuLiftMortgage(self, space: Space):
        assert space.mortgage == True

        space.mortgage = False

        self.renderer.playerMessage(self, "playerLiftMortgageProp", space = space)

        self.give(space.liftMortgagePrice)
    
    def buySpace(self):
        assert isinstance(self.space, OwnableSpace)

        if self.ask(self.lang("askBuy", space = self.space)):
            self.pay(self.space.price)

            self.ownedSpaces.append(self.space)

            self.ownedSpaces.sort(key = lambda s: s.pos if s.type == "terrain" else 99 + len(s.type) + s.id)

            self.space.owner: Player = self

    def __repr__(self):
        return self.name or self.game.lang("player", id = self.id + 1)


class DebugPlayer(Player):
    def __init__(self, game: "Monopoly"):
        super().__init__(game, -1, name="\033[3mDEBUG PLAYER\033[0m")
