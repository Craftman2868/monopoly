from sys import stdin, stdout, stderr, platform

from .dice      import DicePair
from .player    import Player
from .space     import Space, OwnableSpace

from typing import Optional, List, Tuple


if platform == "win32":
    from msvcrt import getch, kbhit
else:
    import tty
    import termios
    from select import select

    def getch():
        fd = stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def kbhit(self):
        ''' Returns True if keyboard character was hit, False otherwise.
        '''

        dr,dw,de = select([sys.stdin], [], [], 0)
        return dr != []

ESC = "\033"
CSI = ESC + "["

BOLD = CSI + "1m"
ITALIC = CSI + "3m"

rgb_to_code = lambda r, g, b: f"{CSI}38;2;{r};{g};{b}m"


COLOR_TO_CODE = {
    "brown":        rgb_to_code(167, 103, 48 ),
    "light_blue":   rgb_to_code(170, 204, 255),
    "pink":         rgb_to_code(238, 68,  221),
    "orange":       rgb_to_code(255, 102, 0  ),
    "red":          rgb_to_code(255, 0,   0  ),
    "yellow":       rgb_to_code(255, 255, 0  ),
    "green":        rgb_to_code(0,   200, 0  ),
    "blue":         rgb_to_code(51,  51,  255),

    "native_yellow":  CSI + "33m",
    "bright_white": CSI + "97m",
}

RESET = CSI + "0m"

COLOR_TERRAINS = True


class DiceRenderer:
    def __init__(self, renderer: "Renderer", dices: DicePair, player: Player):
        self.renderer = renderer
        self.dices = dices
        self.player = player

        self.game = renderer.game

        self.lang = self.game.lang

        self.eraseLine()
    
    def waitRoll(self):
        self.renderer.writePlayer(self.player)
        self.renderer.waitPress(self.lang["pressForRollDices"])
    
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
        self.lang = self.game.lang
        self.sIn = sIn
        self.sOut = sOut
        self.sErr = stderr
    
    # -------- IO --------
    
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

    def writeLnFlush(self, s: str = ""):
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

    def writeLnFlushPlayer(self, player: Player, s: str = ""):
        self.writePlayer(player, s)

        self.writeLnFlush()
    
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

    def writeLnFlushErr(self, s: str):
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
        
    # -------- render --------

    def renderDices(self, dices: DicePair, player: Player):
        return DiceRenderer(self, dices, player)

    def renderPlayer(self, player: Player, score: Optional[int] = None, double: Optional[bool] = None):
        self.writeLnPlayer(player)
        if score:
            self.writeLn(f"    {self.lang['score']}: {score}{'    DOUBLE !!' if double else ''}")
        self.writeLn(f"    {self.lang['money']}: M{player.money}")
        self.write(f"    {self.lang['space']}: {player.space.render}")
        if player.space.type == "jail" and not player.inJail:
            self.write(f" ({self.lang['visitOnly']})")
        
        self.writeLnFlush()
    
    def renderSpace(self, space: Space):  # sourcery skip: assign-if-exp, switch
        if space.type == "railroad":
            return BOLD + str(space) + RESET

        if space.type == "company":
            assert space.id in {0, 1}

            if space.id == 0:
                return COLOR_TO_CODE["native_yellow"] + str(space) + RESET
            else:
                return COLOR_TO_CODE["bright_white"] + str(space) + RESET

        if space.type == "terrain":
            assert space.color in COLOR_TO_CODE

            return COLOR_TO_CODE[space.color] + str(space) + RESET

        return str(space)

    # Messages
    
    def playerMessage(self, _player: Player, _message: str, **kwargs):
        self.writeLnFlushPlayer(_player, self.lang[_message].format(**kwargs))
    
    def playerPlayAgain(self, player: Player):
        self.writeLn("--------------------------------------\n")
        self.playerMessage(player, "playAgain")

    def playerDrawChanceCard(self, player: Player, card: int):
        self.playerMessage(player, "playerHasToDrawChanceCard")
        self.playerMessage(player, "playerDrawnCard", card = self.lang["chanceCards"][card])

    def playerDrawCommunityChestCard(self, player: Player, card: int):
        self.playerMessage(player, "playerHasToDrawCommunityChestCard")
        self.playerMessage(player, "playerDrawnCard", card = self.lang["communityChestCards"][card])
    
    def startPlayerTurn(self, player: Player):
        self.writeLnFlush("=====================[ " + str(player) + " ]=====================")

    # Questions

    def renderPlayerQuestion(self, player: Player, question: str, yn: bool = True):
        self.writePlayer(player, f"{question} ")

        if yn:
            self.write("[yn] ")
        
        self.flush()

    def answerYesNo(self):
        answer = b"\x00"

        while answer.lower() not in b"yYnN":
            self.flushIn()

            answer = self.getch()

        self.writeLnFlush(answer.decode())

        return answer in b"yY"
    
    def askNumber(self, question: str, min: int, max: int):
        assert min >= 0
        assert max < 10
        
        answer = b"\x00"

        self.writeFlush(f"{question} [{min}-{max}] ")

        while not (answer.isdigit() and int(answer) >= min and int(answer) <= max):
            self.flushIn()

            answer = self.getch()

        answer = int(answer)

        self.writeLnFlush(str(answer))

        return answer

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

    
    # Menu

    def renderMenu(self, player: Player, title: str, items: List[Tuple[str, str]]):
        self.writeLnFlush(f"{title} :")

        for i, (id, text) in enumerate(items):
            self.writeLnFlush(f"    {i + 1}.\t{text}")

        self.writeLnFlush()

        assert len(items) < 10  ## TODO (not supported yet)

        opt = self.askNumber(f"{player!r}:", 1, len(items))

        opt = items[opt - 1][0]

        return opt

    def playerMenu(self, player: Player, canRollDices: bool, do_render: bool, has_played: bool):
        # sourcery skip: extract-duplicate-method, merge-repeated-ifs
        items = []
        args = []

        if canRollDices:
            items.append("rollDicesJail" if player.inJail else "rollDices")
        else:
            items.append("finish")

        if has_played and isinstance(player.space, OwnableSpace) and player.space.forSale:
            items.append("buy")

        if len(player.ownedSpaces) != 0:
            if any((not s.mortgage) for s in player.ownedSpaces):
                items.append("mortgage")

            if any(s.mortgage for s in player.ownedSpaces):
                items.append("liftMortgage")

        if player.inJail and not has_played:
            items.append("payJail")

            if "jail_card" in player.cards:
                items.append("jailCard")

        if do_render:
            self.renderPlayer(player)

            self.writeLnFlush()

        if player.inJail:
            self.playerMessage(player, "playerInJail")

        items = [(it, self.lang["menu"][it].format(player=player)) for it in items]

        opt = self.renderMenu(player, self.lang["menu"]["menu"], items)

        if opt == "mortgage":
            items = [*(s for s in player.ownedSpaces if not s.mortgage)]

            items = [*((sp, self.lang["menu"]["mortgageProp"].format(space=sp)) for sp in items), ("cancel", self.lang["cancel"])]

            prop = self.renderMenu(player, self.lang["menu"]["mortgageMenu"], items)

            args.append(prop)
        elif opt == "liftMortgage":
            items = [*(s for s in player.ownedSpaces if s.mortgage)]

            items = [*((sp, self.lang["menu"]["liftMortgageProp"].format(space=sp)) for sp in items), ("cancel", self.lang["cancel"])]

            prop = self.renderMenu(player, self.lang["menu"]["liftMortgageMenu"], items)

            args.append(prop)

        return opt, args
