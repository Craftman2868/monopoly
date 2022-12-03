from .player    import Player
from .dice      import DicePair
from .renderer  import Renderer
from .map       import Map
from .space     import OwnableSpace
from .lang      import loadLang
from .chance    import CHANCE_CARDS, COMMUNITY_CHEST_CARDS
from .cardStack import CardStack


class Monopoly:
    def __init__(self, *, playerCount: int = 4, lang: str = "english", map: str = "USA"):
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

        do_render = True

        has_played = False

        while True:
            action, args = player.menu(play_again, do_render, has_played)

            do_render = True

            assert action in ("mortgage", "liftMortgage", "buy", "rollDices", "rollDicesJail", "payJail", "jailCard", "finish")

            if action == "mortgage":
                assert len(args) == 1

                space = args[0]

                if space == "cancel":
                    continue

                assert isinstance(space, OwnableSpace)

                assert space.mortgage == False

                space.mortgage = True

                self.renderer.playerMessage(player, "playerMortgageProp", space = space)

                player.give(space.mortgagePrice)

                # self.renderer.playerMessage(player, "notImplemented")  ## TODO

            if action == "liftMortgage":
                assert len(args) == 1

                space = args[0]

                if space == "cancel":
                    continue

                assert isinstance(space, OwnableSpace)

                assert space.mortgage == True

                space.mortgage = False

                self.renderer.playerMessage(player, "playerLiftMortgageProp", space = space)

                player.pay(space.liftMortgagePrice)

                # self.renderer.playerMessage(player, "notImplemented")  ## TODO
            if action == "rollDices":
                assert not player.inJail

                score, double = self.rollDices(player)

                if double:
                    double_count += 1

                play_again = double

                do_render = player.play(score, double)

                if double_count == 3:
                    self.renderer.playerMessage(player, "playerGoJailDouble")

                    player.goJail()

                if not player.inJail and play_again:
                    self.renderer.playerPlayAgain(player)

                has_played = True
            elif action == "rollDicesJail":
                assert player.inJail
                
                if player.jailTurnCount >= 3:
                    self.renderer.playerMessage(player, "maxJailTurn")

                    player.pay(50)

                    score, double = self.rollDices(player)

                    player.getOutJail(score, double)

                    if double:
                        double_count += 1

                    play_again = double

                score, double = self.rollDices(player)

                if double:
                    player.getOutJail(score, double)
                else:
                    player.jailTurnCount += 1

                play_again = False
                has_played = True
            elif action == "payJail":
                assert player.inJail

                player.pay(50)

                score, double = self.rollDices(player)

                player.getOutJail(score, double)

                if double:
                    double_count += 1

                play_again = double
            
            elif action == "jail_card":
                assert player.inJail

                score, double = self.rollDices(player)

                player.getOutJail(score, double)

                if double:
                    double_count += 1

                play_again = double
            
            elif action == "buy":
                if player.ask(self.lang["askBuy"].format(space = player.space)):
                    player.pay(player.space.price)

                    player.ownedSpaces.add(player.space)

                    player.space.owner: Player = player

            elif action == "finish":
                break
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
