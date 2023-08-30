# from .monopoly import monopoly
from .space import TERRAIN_COUNT_BY_GROUPS, Space, OwnableSpace, Space_Terrain, SPACE_COUNT

from typing import Optional, List, Any, Dict


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
        return [gid for gid in range(8) if self.hasGroup(gid)]

    def message(self, _message: str, **kwargs: object):
        return self.renderer.playerMessage(self, _message, **kwargs)

    def giveSpace(self, space: OwnableSpace):
        assert isinstance(space, OwnableSpace)

        if space not in self.ownedSpaces:
            self.ownedSpaces.append(space)

        space.owner = self

    def countHouses(self):
        return sum(s.houseCount for s in self.ownedSpaces if s.type == "terrain")

    def countHotels(self):
        return sum(s.hotelCount for s in self.ownedSpaces if s.type == "terrain")

    def hasGroup(self, gid: int):
        if gid < 0 or gid >= len(TERRAIN_COUNT_BY_GROUPS):
            return False

        terrainCount = sum(s.type == "terrain" and s.group_id ==
                           gid for s in self.ownedSpaces)

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
        self.message("salary")

        self.give(200)

    def goto(self, pos: int):
        if pos < self.pos:
            self.receiveSalary()

        self.pos = pos

    def gotoTerrain(self, gid: int, id: int):
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
            self.pos %= SPACE_COUNT

            self.receiveSalary()

    def moveBack(self, score: int):
        self.advance(-score)

    def do_space(self, score: int):
        return self.space.on_pass(self, score)

    def give(self, amount: int):
        self.money += amount

    def pay(self, amount: int, to: Optional["Player"] = None):
        self.money -= amount

        # TODO: check enough money

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

        self.message("playerMortgageProp", space=space)

        self.give(space.mortgagePrice)

    def menuRemoveMortgage(self, space: Space):
        assert space.mortgage == True

        space.mortgage = False

        self.message("playerRemoveMortgageProp", space=space)

        self.give(space.removeMortgagePrice)

    def buySpace(self):
        assert isinstance(self.space, OwnableSpace)

        if self.ask(self.lang("askBuy", space=self.space)):
            self.pay(self.space.price)

            self.ownedSpaces.append(self.space)

            self.ownedSpaces.sort(
                key=lambda s: s.pos if s.type == "terrain" else 99 + len(s.type) + s.id)

            self.space.owner: Player = self

    def doAction(self, action: str, args: List[Any], vars: Dict[str, Any]):
        assert action in {"mortgage", "removeMortgage", "buy", "rollDices", "rollDicesJail",
                          "payJail", "jailCard", "finish", "pass", "buyHousesOrHotels", "saleHousesOrHotels"}

        if action == "buy":
            if self.ask(self.renderer.lang("askBuy", space=self.space)):
                self.pay(self.space.price)

                self.ownedSpaces.append(self.space)

                self.ownedSpaces.sort(
                    key=lambda s: s.pos if s.type == "terrain" else 99 + len(s.type) + s.id)

                self.space.owner: Player = self

        elif action == "buyHousesOrHotels":
            self.menuBuyHousesOrHotels(args)
        elif action == "saleHousesOrHotels":
            self.message("notImplemented")

        elif action == "jail_card":
            assert self.inJail

            score, double = self.game.rollDices(self)

            self.getOutJail(score, double)

            if double:
                vars["double_count"] += 1

            vars["play_again"] = double

        elif action == "mortgage":
            space = self.menuArgsGetSpace(args, vars)
            self.menuMortgage(space)

        elif action == "payJail":
            self.menuPayJail(vars)
        elif action == "removeMortgage":
            space = self.menuArgsGetSpace(args, vars)
            self.menuRemoveMortgage(space)

        elif action == "rollDices":
            self.menuRollDices(vars)
        elif action == "rollDicesJail":
            self.menuRollDicesJail(vars)

        elif action == "finish":
            return False

        return True

    def menuRollDicesJail(self, vars: Dict[str, Any]):
        assert self.inJail

        score, double = self.game.rollDices(self)

        if double:
            self.getOutJail(score, double)
        else:
            self.jailTurnCount += 1

        vars["play_again"] = False
        vars["has_played"] = True

    def menuRollDices(self, vars: Dict[str, Any]):
        assert not self.inJail

        score, double = self.game.rollDices(self)

        if double:
            vars["double_count"] += 1

        vars["play_again"] = double

        vars["do_render"] = self.play(score, double)

        if vars["double_count"] == 3:
            self.message("playerGoJailDouble")

            self.goJail()

        if self.inJail:
            vars["play_again"] = False

        if vars["play_again"]:
            self.renderer.playerPlayAgain(self)

        vars["has_played"] = True

    def menuPayJail(self, vars: Dict[str, Any]):
        assert self.inJail

        self.pay(50)

        self.message("hadPaidJail")

        score, double = self.game.rollDices(self)

        self.getOutJail(score, double)

        if double:
            vars["double_count"] += 1

        vars["play_again"] = double

    def menuBuyHousesOrHotels(self, args):
        assert len(args) == 2

        space, hotel = args[0], args[1]

        assert isinstance(space, Space_Terrain)
        assert isinstance(hotel, bool)

        success = space.buyHotel() if hotel else space.buyHouse()

        if success:
            if hotel:
                self.message("buyHotelSuccess", space=space)
            else:
                self.message("buyHouseSuccess", space=space)
        else:
            if hotel:
                self.message("buyHotelFail", space=space)
            else:
                self.message("buyHouseFail", space=space)

    def menuArgsGetSpace(self, args):
        assert len(args) == 1

        result = args[0]

        assert isinstance(result, OwnableSpace)

        return result

    def __repr__(self):
        return self.name or self.game.lang("player", id=self.id + 1)


class DebugPlayer(Player):
    def __init__(self, game: "Monopoly"):
        super().__init__(game, -1, name="\033[3mDEBUG PLAYER\033[0m")
