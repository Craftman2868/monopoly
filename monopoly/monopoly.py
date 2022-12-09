from .player    import Player, DebugPlayer
from .dice      import DicePair
from .renderer  import Renderer
from .map       import Map
from .space     import OwnableSpace, Space_Terrain
from .lang      import loadLang
from .chance    import CHANCE_CARDS, COMMUNITY_CHEST_CARDS
from .cardStack import CardStack

from typing import Optional


class Monopoly:
    def __init__(self, *, playerCount: int = 4, lang: str = "english", map: str = "USA", debug: bool = False):
        self.debug = debug

        self.debugPlayer: Optional[Player] = None

        self.playerCount = playerCount

        self.lang = loadLang(lang)

        self.renderer = Renderer(self)

        self.map = Map.load(self, map)

        self.players = [Player(self, i) for i in range(playerCount)]
    
        self.running = False

        self.dices = DicePair()

        self.chanceCardStack = CardStack(range(len(CHANCE_CARDS)))
        self.communityChestCardStack = CardStack(range(len(COMMUNITY_CHEST_CARDS)))

        self.chanceCardStack.mix()
        self.communityChestCardStack.mix()

        if self.debug:
            self.debugPlayer = DebugPlayer(self)
    
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
        vars = {
            "play_again": True,
            "double_count": 0,
            "do_render": True,
            "has_played": False
        }

        running = True

        while running:
            action, args = player.menu(vars["play_again"], vars["do_render"], vars["has_played"])

            vars["do_render"] = True

            running = player.doAction(action, args, vars)

        # play_again = True

        # while play_again:
        #     play_again = False
        #     score, double = self.rollDices(player)

        #     if double:
        #         play_again = True
        #         double_count += 1

        #     player.play(score, double)

        #     if play_again:
        #         self.renderer.playerPlayAgain(player)

    def run(self):
        self.running = True

        while self.running:
            for p in self.players:
                if p.dead:
                    continue

                self.renderer.startPlayerTurn(p)
                
                self.turn(p)

                self.renderer.writeLnFlush()
