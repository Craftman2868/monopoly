# from .player import Player
from .chance import CHANCE_CARDS, COMMUNITY_CHEST_CARDS

# from .map import Map

from typing import Optional, Callable


TAXE_AMOUNTS = [200, 100]
RAILROAD_PRICE = 200
COMPANY_PRICE = 150

RAILROAD_RENTS = [25, 50, 100, 200]

MAX_HOTEL_COUNT = 1
MAX_HOUSE_COUNT = 4

RAILROAD_COUNT = len(RAILROAD_RENTS)
COMPANY_COUNT = 2


SPACE_COUNT = 40


terrain_data = {}

with open("monopoly/assets/map/terrains", "r") as f:
    for l in f:
        l = l.strip()

        if l.startswith("#") or not l:
            continue

        id, *data = l.split()

        terrain_data[id] = data

TERRAIN_COUNT_BY_GROUPS = [2, 3, 3, 3, 3, 3, 3, 2]


class Space:
    def __init__(self, map: "Map", type: str, pos: int):
        self.map: "Map" = map
        self.type: str = type
        self.pos: int = pos

        self.game: "Monopoly" = self.map.game
        self.renderer: "Renderer" = self.game.renderer

    @property
    def name(self):
        return self.map.data[self.type]

    @property
    def render(self):
        return self.renderer.renderSpace(self)

    def on_pass(self, player: "Player", score: Optional[int] = None):
        raise NotImplementedError()

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<{self.__module__}.{self.__class__.__name__} {self!s}>"


class Space_Go(Space):
    def __init__(self, map: "Map", pos: int):
        super().__init__(map, "go", pos)

    def on_pass(self, player: "Player", score: Optional[int] = None):
        return False


class Space_Jail(Space):
    def __init__(self, map: "Map", pos: int):
        super().__init__(map, "jail", pos)

    def on_pass(self, player: "Player", score: Optional[int] = None):
        return False


class Space_FreeParking(Space):
    def __init__(self, map: "Map", pos: int):
        super().__init__(map, "free_parking", pos)

    def on_pass(self, player: "Player", score: Optional[int] = None):
        return False


class Space_GoJail(Space):
    def __init__(self, map: "Map", pos: int):
        super().__init__(map, "go_jail", pos)

    def on_pass(self, player: "Player", score: Optional[int] = None):
        self.renderer.playerMessage(player, "goJail")

        player.goJail()

        return True


class Space_Tax(Space):
    def __init__(self, map: "Map", id: int, pos: int):
        super().__init__(map, "tax", pos)

        if id < 0 or id >= len(TAXE_AMOUNTS):
            raise ValueError()  # TODO

        self.id: int = id

        self.amount: int = TAXE_AMOUNTS[self.id]

    @property
    def name(self):
        return self.map.data[self.type][self.id]

    def on_pass(self, player: "Player", score: Optional[int] = None):
        self.renderer.playerMessage(player, "buyTax", space=self)

        player.pay(self.amount)

        return True


class OwnableSpace(Space):
    def __init__(self, map: "Map", type: str, pos: int):
        super().__init__(map, type, pos)

        self.price: int = NotImplemented

        self.owner: Optional["Player"] = None

        self.mortgage: bool = False

    @property
    def mortgagePrice(self):
        return int(self.price / 2)

    @property
    def removeMortgagePrice(self):
        return int(self.mortgagePrice * (110 / 100))

    @property
    def forSale(self):
        return self.owner is None

    def getRent(self, player: "Player", score: Optional[int] = None):
        raise NotImplementedError()

    def on_pass(self, player: "Player", score: Optional[int] = None):
        # sourcery skip: merge-else-if-into-elif
        if self.owner:
            if player != self.owner and not self.mortgage:
                rent: int = self.getRent(player, score)

                self.game.renderer.playerMessage(
                    player, "buyRent", space=self, rent=rent)

                player.pay(rent, self.owner)

                return True
        else:
            if self.price == NotImplemented:
                raise NotImplementedError("Price not implemented")

            # if player.ask(self.game.lang("askBuy", name = self.name, price = self.price)):
            #     player.pay(self.price)

            #     player.ownedSpaces.append(self)

            #     self.owner: "Player" = player

            #     return True

        return False

    def __str__(self):
        return self.name + (f" ({self.owner!s})" if self.owner else "")


class Space_Terrain(OwnableSpace):
    def __init__(self, map: "Map", group_id: int, id: int, pos: int):
        super().__init__(map, "terrain", pos)

        self.group_id, self.id = group_id, id

        if self.fullId not in terrain_data:
            raise ValueError(f"Terrain data not found for {self.fullId}")

        self.price: int = int(self.data[1])

        self.color: str = self.data[0]

        self.houseCount: int = 0

        self.hotelCount: int = 0

    @property
    def housePrice(self):
        return int(self.data[8])

    hotelPrice = housePrice

    @property
    def fullId(self):
        return f"{self.group_id + 1}:{self.id + 1}"

    @property
    def data(self):
        return terrain_data[self.fullId]

    @property
    def name(self):
        return self.map.data[self.type][self.group_id][self.id]

    def buyHouse(self):
        if not self.owner.hasGroup(self.group_id):
            return False

        if self.houseCount < MAX_HOUSE_COUNT:
            self.owner.pay(self.housePrice)

            self.houseCount += 1

            return True

        return False

    def buyHotel(self):
        if not self.owner.hasGroup(self.group_id):
            return False

        if self.hotelCount < MAX_HOTEL_COUNT and self.houseCount == 4:
            self.owner.pay(self.hotelPrice)

            self.hotelCount += 1

            self.houseCount = 0

            return True

        return False

    def getRent(self, player: "Player", score: Optional[int] = None):
        rents = [*map(int, self.data[2:8])]

        if not self.hotelCount and self.houseCount <= 4:
            rent = rents[self.houseCount]
        elif self.hotelCount:
            rent = rents[5]
        elif self.owner.hasGroup(self.group_id):
            rent = 2 * rents[0]
        else:
            rent = rents[0]

        return rent * player.rentMultiplier


class Space_Railroad(OwnableSpace):
    def __init__(self, map: "Map", id: int, pos: int):
        super().__init__(map, "railroad", pos)

        if id < 0 or id > 4:
            raise ValueError()  # TODO

        self.id: int = id

        self.price: int = RAILROAD_PRICE

    def getRent(self, player: "Player", score: Optional[int] = None):
        railroadCount: int = self.owner.countSpaceType(Space_Railroad)

        assert railroadCount in range(1, 5)

        return RAILROAD_RENTS[railroadCount - 1] * player.rentMultiplier

    @property
    def name(self):
        return self.map.data[self.type][self.id]


class Space_Company(OwnableSpace):
    def __init__(self, map: "Map", id: int, pos: int):
        super().__init__(map, "company", pos)

        if id < 0 or id > 1:
            raise ValueError()  # TODO

        self.id: int = id

        self.price: int = COMPANY_PRICE

    def getRent(self, player: "Player", score: int):
        companyCount: int = self.owner.countSpaceType(Space_Company)

        assert companyCount in {1, 2}

        if player.rentMultiplier != 1:
            return score * player.rentMultiplier
        else:
            return score * 2 if companyCount == 1 else score * 10

    @property
    def name(self):
        return self.map.data[self.type][self.id]


# class Space_Jail  ## TODO

# class Space_GoJail  ## TODO


class Space_Chance(Space):
    def __init__(self, map: "Map", pos: int):
        super().__init__(map, "chance", pos)

    def on_pass(self, player: "Player", score: Optional[int] = None):
        card: int = self.game.drawChanceCard()

        self.game.renderer.playerDrawChanceCard(player, card)

        cardFunc: Callable = CHANCE_CARDS[card]

        cardFunc(player)

        return True


class Space_CommunityChest(Space):
    def __init__(self, map: "Map", pos: int):
        super().__init__(map, "community_chest", pos)

    def on_pass(self, player: "Player", score: Optional[int] = None):
        card: int = self.game.drawCommunityChestCard()

        self.game.renderer.playerDrawCommunityChestCard(player, card)

        cardFunc: Callable = COMMUNITY_CHEST_CARDS[card]

        cardFunc(player)

        return True

# class Space_TEMP(Space):  ############ T#O#D#O
#     def __init__(self, map: "Map", pos: int):
#         super().__init__(map, "TEMP", pos)

#     @property
#     def name(self):
#         return "TEMP"

#     def on_pass(self, player: "Player", score: Optional[int] = None):
#         print("NOT IMPLEMENTED YET")

#         return False
