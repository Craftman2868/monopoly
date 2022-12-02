from .player import Player
from .chance import CHANCE_CARDS, COMMUNITY_CHEST_CARDS

# from .map import Map

from typing import Optional


TAXE_AMOUNTS = [200, 100]
RAILROAD_PRICE = 200
COMPANY_PRICE = 150

RAILROAD_RENTS = [25, 50, 100, 200]


class Space:
    def __init__(self, map: "Map", type: str, pos: int):
        self.map = map
        self.type = type
        self.pos = pos

        self.game = map.game
    
    @property
    def name(self):
        return self.map.data[self.type]

    def on_pass(self, player: Player, score: Optional[int] = None):
        raise NotImplementedError()
    
    def __str__(self):
        return self.name

class Space_FreeParking(Space):
    def __init__(self, map: "Map", pos: int):
        super().__init__(map, "free_parking", pos)

    def on_pass(self, player: Player, score: Optional[int] = None):
        return False


class Space_Go(Space):
    def __init__(self, map: "Map", pos: int):
        super().__init__(map, "go", pos)
    
    def on_pass(self, player: Player, score: Optional[int] = None):
        return False


class Space_Taxe(Space):
    def __init__(self, map: "Map", id: int, pos: int):
        super().__init__(map, "taxe", pos)

        if id < 0 or id >= len(TAXE_AMOUNTS):
            raise ValueError()  ## TODO

        self.id = id

        self.amount = TAXE_AMOUNTS[self.id]
    
    @property
    def name(self):
        return self.map.data[self.type][self.id]

    def on_pass(self, player: Player, score: Optional[int] = None):
        self.game.renderer.playerPayTaxe(player, self, self.amount)

        player.pay(self.amount)

        return True


class OwnableSpace(Space):
    def __init__(self, map: "Map", type: str, pos: int):
        super().__init__(map, type, pos)

        self.price = NotImplemented

        self.owner: Optional[Player] = None

    def getRent(self, player: Player, score: Optional[int] = None):
        raise NotImplementedError()
    
    def on_pass(self, player: Player, score: Optional[int] = None):
        if self.owner:
            if player != self.owner:
                rent = self.getRent(player, score)

                self.game.renderer.playerPayRent(player, self, rent, self.owner)

                player.pay(rent, self.owner)

                return True
        else:
            if self.price == NotImplemented:
                raise NotImplementedError("Price not implemented")

            if player.ask(self.game.lang["askBuy"].format(name = self.name, price = self.price)):
                player.pay(self.price)

                player.ownedSpaces.add(self)

                self.owner = player

                return True

        return False

class Space_Terrain(OwnableSpace):
    def __init__(self, map: "Map", group_id: int, id: int, pos: int):
        super().__init__(map, "terrain", pos)

        ## TODO: check group id
        ## TODO: check id

        self.price = 100  ## TODO

        self.group_id, self.id = group_id, id

        self.color = "brown"  ## TODO
    
        self.houseCount = 0
        
        self.hotelCount = 0
    
    def getRent(self, player: Player, score: Optional[int] = None):
        return 10 * player.rentMultiplier  ## TODO

    @property
    def name(self):
        return self.map.data[self.type][self.group_id][self.id]


class Space_Railroad(OwnableSpace):
    def __init__(self, map: "Map", id: int, pos: int):
        super().__init__(map, "railroad", pos)

        if id < 0 or id > 4:
            raise ValueError()  ## TODO

        self.id = id
    
        self.price = RAILROAD_PRICE

    def getRent(self, player: Player, score: Optional[int] = None):
        railroadCount = self.owner.countSpaceType(Space_Railroad)

        assert railroadCount in range(1, 5)

        return RAILROAD_RENTS[railroadCount - 1] * player.rentMultiplier

    @property
    def name(self):
        return self.map.data[self.type][self.id]


class Space_Company(OwnableSpace):
    def __init__(self, map: "Map", id: int, pos: int):
        super().__init__(map, "company", pos)

        if id < 0 or id > 2:
            raise ValueError()  ## TODO

        self.id = id
    
        self.price = COMPANY_PRICE
    
    def getRent(self, player: Player, score: int):
        companyCount = self.owner.countSpaceType(Space_Company)

        assert companyCount in (1, 2)

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
        # print("NOT IMPLEMENTED YET")  ## TODO

        card = self.game.drawChanceCard()

        self.game.renderer.playerDrawChanceCard(player, card)

        cardFunc = CHANCE_CARDS[card]

        cardFunc(player)

        return True

class Space_CommunityChest(Space):
    def __init__(self, map: "Map", pos: int):
        super().__init__(map, "community_chest", pos)

    def on_pass(self, player: "Player", score: Optional[int] = None):
        # print("NOT IMPLEMENTED YET")  ## TODO

        card = self.game.drawCommunityChestCard()

        self.game.renderer.playerDrawCommunityChestCard(player, card)

        cardFunc = COMMUNITY_CHEST_CARDS[card]

        cardFunc(player)

        return True

class Space_TEMP(Space):  ############ TODO
    def __init__(self, map: "Map", pos: int):
        super().__init__(map, "TEMP", pos)
    
    @property
    def name(self):
        return "TEMP"
    
    def on_pass(self, player: Player, score: Optional[int] = None):
        print("NOT IMPLEMENTED YET")

        return False
