from sys import stdin, stdout, stderr

from .dice import DicePair
from .player import Player
from .space import Space, OwnableSpace

from typing import Optional

from msvcrt import getch, kbhit

ESC = "\033"
CSI = ESC + "["


class DiceRenderer:
    def __init__(self, renderer: "Renderer", dices: DicePair, player: Player):
        self.renderer = renderer
        self.dices = dices
        self.player = player

        self.game = renderer.game

        self.eraseLine()
    
    def waitRoll(self):
        self.renderer.writePlayer(self.player)
        self.renderer.waitPress(self.game.lang["pressForRollDices"])
    
    def erase(self):
        self.renderer.write(CSI + "1K")

    def eraseLine(self):
        self.renderer.write(CSI + "2K")

    def render(self):
        self.erase()
        self.renderer.writeFlush(f"\r{self.player!r}: {self.dices[0].value}  {self.dices[1].value}")
    
    def finish(self):
        self.render()

        self.renderer.writeFlush("\r\n\n")
    
    # def renderScore(self):  ## MOVED TO Renderer.renderPlayer
    #     stdout.write(f"\n\nScore: {self.dices.sum}\n")

    #     if self.dices.double:
    #         stdout.write("Double !!\n")


class Renderer:
    def __init__(self, game: "Monopoly", sIn = stdin, sOut = stdout, sErr = stderr):
        self.game = game
        self.sIn = sIn
        self.sOut = sOut
        self.sErr = stderr
    
    # OUT

    def writeOut(self, s: str):  # sourcery skip: remove-unnecessary-cast
        self.sOut.write(str(s))
    
    write = writeOut
    
    def writeLnOut(self, s: str = ""):
        self.writeOut(f"{s}\n")

    writeLn = writeLnOut

    def flushOut(self):
        self.sOut.flush()
    
    flush = flushOut

    def writeFlush(self, s: str):
        self.writeOut(s)

        self.flushOut()

    def writeFlushLn(self, s: str = ""):
        self.writeLn(s)

        self.flushOut()
    
    def writePlayer(self, player: Player, s: str = ""):
        self.write(f"{player!r}: ")

        if s:
            self.write(f"{s}")

    def writeLnPlayer(self, player: Player, s: str = ""):
        self.writePlayer(player, s)

        self.writeLn()

    def writeFlushPlayer(self, player: Player, s: str = ""):
        self.writePlayer(player, s)
        
        self.flush()

    def writeFlushLnPlayer(self, player: Player, s: str = ""):
        self.writePlayer(player, s)

        self.writeFlushLn()
    
    # ERR

    def writeErr(self, s: str):  # sourcery skip: remove-unnecessary-cast
        self.sErr.write(str(s))
    
    def writeLnErr(self, s: str = ""):
        self.writeErr(f"{s}\n")
    
    def flushErr(self):
        self.sErr.flush()

    def writeFlushErr(self, s: str):
        self.writeErr(s)

        self.flushErr()

    def writeFlushLnErr(self, s: str):
        self.writeErr(s)

        self.writeLnErr()

        self.flushErr()

    # IN

    def getch(self):
        ch = getch()

        if ch == b"\003":  ## CTRL + C
            raise KeyboardInterrupt
        
        return ch

    def flushIn(self):
        while kbhit():
            self.getch()

    def renderDices(self, dices: DicePair, player: Player):
        return DiceRenderer(self, dices, player)

    def renderPlayer(self, player: Player, score: Optional[int] = None, double: Optional[bool] = None):
        self.writeLnPlayer(player)
        if score:
            self.writeLn(f"    {self.game.lang['score']}: {score}{'    DOUBLE !!' if double else ''}")
        self.writeLn(f"    {self.game.lang['money']}: M{player.money}")
        self.writeLn(f"    {self.game.lang['space']}: {player.space.name}")

    def renderPlayerQuestion(self, player: Player, question: str, yn: bool = True):
        self.writePlayer(player, f"{question} ")

        if yn:
            self.write("[yn] ")
        
        self.flush()

    def playerPayRent(self, player: Player, space: OwnableSpace, rent: int, owner: Player):
        self.writeFlushLnPlayer(player, self.game.lang["buyRent"].format(space = space, price = rent, owner = owner))

    def playerPayTaxe(self, player: Player, space: OwnableSpace, amount: int):
        self.writeFlushLnPlayer(player, self.game.lang["buyTaxe"].format(space = space, price = amount))

    def playerReceiveSalary(self, player: Player):
        self.writeFlushLnPlayer(player, self.game.lang["salary"])
    
    def playerPlayAgain(self, player: Player):
        self.writeLn("--------------------------------------\n")
        self.writeFlushLnPlayer(player, self.game.lang["playAgain"])

    def playerDrawChanceCard(self, player: Player, card: int):
        self.writeFlushLnPlayer(player, self.game.lang["playerHasToDrawChanceCard"])
        self.writeFlushLnPlayer(player, self.game.lang["playerDrawnCard"].format(card = self.game.lang["chanceCards"][card]))

    def playerDrawCommunityChestCard(self, player: Player, card: int):
        self.writeFlushLnPlayer(player, self.game.lang["playerHasToDrawCommunityChestCard"])
        self.writeFlushLnPlayer(player, self.game.lang["playerDrawnCard"].format(card = self.game.lang["communityChestCards"][card]))
    
    def startPlayerTurn(self, player: Player):
        self.writeFlushLn("=====================[ " + str(player) + " ]=====================")

    def answerYesNo(self):
        answer = b"a"

        self.flushIn()

        while answer.lower() not in b"yYnN":
            answer = self.getch()

        self.writeFlush("\n")

        return answer in b"yN"

    def askPlayerQuestion(self, player: Player, question: str, yn: bool = True):
        self.renderPlayerQuestion(player, question, yn)

        if yn:
            return self.answerYesNo()

        answer = None

        while not answer:
            answer = input().strip()
        
        return answer

    def waitPress(self, prompt: Optional[str] = None):
        if prompt:
            self.writeFlush(prompt)
        
        self.flushIn()

        self.getch()

        return
