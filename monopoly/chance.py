CHANCE_CARDS = [
    lambda player: player.gotoTerrain(8, 2),
    lambda player: player.goto(0),
    lambda player: player.gotoTerrain(5, 3),
    lambda player: player.gotoTerrain(3, 1),
    lambda player: (player.multiplyRent(2), player.gotoNearest("railroad")),
    lambda player: (player.multiplyRent(2), player.gotoNearest("railroad")),
    lambda player: (player.multiplyRent(10), player.gotoNearest("company")),
    lambda player: player.give(50),
    lambda player: None,  ## Get out jail
    lambda player: player.moveBack(3),
    lambda player: player.goJail(),
    lambda player: player.pay(25 * player.countHouses() + 100 * player.countHotels()),
    lambda player: player.pay(15),
    lambda player: player.gotoRailroad(1),
    lambda player: player.pay(player.game.playerCount * 50),
    lambda player: player.give(150),
]

COMMUNITY_CHEST_CARDS = [
    lambda player: player.goto(0),
    lambda player: player.give(200),
    lambda player: player.pay(50),
    lambda player: player.give(50),
    lambda player: None,  ## Get out jail
    lambda player: player.goJail(),
    lambda player: player.give(100),
    lambda player: player.give(20),
    lambda player: player.give(player.game.playerCount * 10),
    lambda player: player.give(100),
    lambda player: player.pay(100),
    lambda player: player.pay(50),
    lambda player: player.give(25),
    lambda player: player.pay(40 * player.countHouses() + 115 * player.countHotels()),
    lambda player: player.give(10),
    lambda player: player.give(100),
]
