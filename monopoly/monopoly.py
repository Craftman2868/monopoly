from .player import Player
from .dice import DicePair
from .renderer import Renderer
from .map import Map
from .lang import loadLang
from .chance import CHANCE_CARDS, COMMUNITY_CHEST_CARDS
from .cardStack import CardStack


"""
TODO:
    - Terrains
    - Prison
    - Maisons / Hôtels
"""


class Monopoly:
    def __init__(self, *, playerCount: int = 4, lang: str = "french", map: str = "France"):
        self.playerCount = playerCount

        self.lang = loadLang(lang)
        self.map = Map.load(self, map)

        self.players = [Player(self, i) for i in range(playerCount)]
    
        self.running = False

        self.dices = DicePair()

        self.renderer = Renderer(self)

        self.chanceCardStack = CardStack(range(len(CHANCE_CARDS)))
        self.communityChestCardStack = CardStack(range(len(COMMUNITY_CHEST_CARDS)))

        self.chanceCardStack.mix()
        self.communityChestCardStack.mix()
    
    def drawChanceCard(self):
        return self.chanceCardStack.draw()

    def drawCommunityChestCard(self):
        return self.communityChestCardStack.draw()

    def rollDices(self, player: Player):
        dr = self.renderer.renderDices(self.dices, player)

        dr.waitRoll()

        for d, v, p in self.dices.roll(0.1):
            dr.render()
        
        dr.finish()

        # dr.renderScore()

        return self.dices.sum, self.dices.double

    def turn(self, player: Player):
        play_again = True

        double_count = 0

        while play_again:
            play_again = False
            score, double = self.rollDices(player)

            if double:
                play_again = True
                double_count += 1
            
            if double_count == 3:
                player.goJail()

            player.play(score, double)

            if play_again:
                self.renderer.playerPlayAgain(player)

    def run(self):
        self.running = True

        while self.running:
            for p in self.players:
                if p.dead:
                    continue

                self.renderer.startPlayerTurn(p)
                
                self.turn(p)

                # return  ## TEMP
