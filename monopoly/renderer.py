from sys import stdin, stdout, stderr, platform

from .dice      import DicePair
from .player    import Player
from .space     import Space, OwnableSpace

from typing import Optional, List, Tuple, Any


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

    def kbhit():
        ''' Returns True if keyboard character was hit, False otherwise.
        '''

        dr,dw,de = select([stdin], [], [], 0)
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


def divide_chunks(l: list, n: int):
    # https://www.geeksforgeeks.org/break-list-chunks-size-n-python/
    for i in range(0, len(l), n):
        yield l[i:i + n]


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
    
    @property
    def map(self):
        return self.game.map

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
    
    def renderGroup(self, gid: int):
        color = self.map.getGroupColor(gid)

        return COLOR_TO_CODE[color] + self.lang("group", color = self.lang["colors"][color]) + RESET

    # Messages
    
    def playerMessage(self, _player: Player, _message: str, **kwargs):
        self.writeLnFlushPlayer(_player, self.lang(_message, **kwargs))
    
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

    @property
    def cancel_opt(self):
        return ("cancel", self.lang["cancel"])

    def renderMenu(self, player: Player, title: str, items: List[Tuple[Any, str]], zero: Optional[Tuple[str, str]] = None):
        # sourcery skip: assign-if-exp, avoid-builtin-shadow

        if len(items) < 10:
            pages = [items]
        else:
            pages = [*divide_chunks(items, 7)]

        curPage = 0

        while True:
            self.writeLn()
            self.writeLn(f"{title} (page {curPage + 1}/{len(pages)}):")
            if zero:
                self.writeLn(f"    0.\t{zero[1]}")

            page: List[Tuple[Any, str]] = pages[curPage].copy()
            
            pageSize = len(page)

            if len(pages) > 1:
                page.insert(0, ("_previous", self.lang["previous"]))
                page.append(("_next", self.lang["next"]))
                
                pageSize += 2

            for i, (id, text) in enumerate(page):
                self.writeLn(f"    {i + 1}.\t{text}")

            self.writeLnFlush()

            min = 0 if zero else 1

            opt = self.askNumber(f"{player!r}:", min, pageSize)

            if opt == 0:
                return zero[0]

            opt = page[opt - 1][0]

            if opt == "_previous":
                curPage -= 1
            elif opt == "_next":
                curPage += 1
            else:
                return opt
            
            curPage %= len(pages)
    
    def selectPlayerMenu(self, player: Player, title: str):
        # sourcery skip: assign-if-exp, introduce-default-else
        items = [*((p, str(p)) for p in self.game.players)]

        zero = None

        if self.game.debug:
            zero = (self.game.debugPlayer, str(self.game.debugPlayer))

        return self.renderMenu(player, title, items, zero)

    def debugMenu(self):  # sourcery skip: low-code-quality, merge-list-extend
        debugMenuItems = [
            "give",
            "steal",
            "manageProperties",
            "teleportPlayer"
        ]

        debugMenuItems = [*map(lambda it: (it, it), debugMenuItems)]

        zero = ("cancel", self.lang["cancel"])

        while True:
            opt = self.renderMenu(self.game.debugPlayer, ITALIC + "Debug Menu" + RESET, debugMenuItems, zero)

            if opt == "cancel":
                break
            elif opt == "give":
                pl = self.selectPlayerMenu(self.game.debugPlayer, "Give to")

                amount = input("Amount: M").strip()

                try:
                    amount = int(amount)
                except ValueError:
                    self.writeLnFlush("Error during conversion to int")
                    continue

                pl.give(amount)

                pl.render()
            elif opt == "steal":
                pl = self.selectPlayerMenu(self.game.debugPlayer, "Steal to")

                amount = input("Amount: M").strip()

                try:
                    amount = int(amount)
                except ValueError:
                    self.writeLnFlush("Error during conversion to int")
                    continue

                pl.pay(amount)

                pl.render()
            elif opt == "manageProperties":
                items = [*map(lambda g: (g, self.renderGroup(g)), range(8)), ("special", self.lang["specialProperty"])]

                group = self.renderMenu(self.game.debugPlayer, "Group", items, self.cancel_opt)

                if group == "cancel":
                    continue

                if group == "special":
                    items = [*map(lambda s: (s, s.render), (self.map.getSpecialProperties()))]

                    items.extend([(self.map.getRailroads(), "*railroads"), (self.map.getCompanies(), "*companies")])

                    spaces = self.renderMenu(self.game.debugPlayer, "Space", items, self.cancel_opt)
                else:
                    items = [*map(lambda s: (s, s.render), self.map.getGroupTerrains(group))]

                    items.append((self.map.getGroupTerrains(group), "*"))

                    spaces = self.renderMenu(self.game.debugPlayer, "Terrain", items, self.cancel_opt)

                if spaces == "cancel":
                    continue
            
                if not isinstance(spaces, list):
                    spaces = [spaces]

                items = [
                    "setOwner"
                ]

                if any(s.owner for s in spaces):
                    items.append("toggleMortgage")

                if spaces[0].type == "terrain":
                    items.extend((
                        "buildHouse",
                        "removeHouse",
                        "buildHotel",
                        "removeHotel"
                    ))

                items = [*map(lambda it: (it, it), items)]

                action = self.renderMenu(self.game.debugPlayer, "Action", items, self.cancel_opt)

                if action == "cancel":
                    continue

                if action == "setOwner":
                    newOwner = self.selectPlayerMenu(self.game.debugPlayer, "New owner")

                    for space in spaces:
                        newOwner.giveSpace(space)

                elif action == "toggleMortgage":
                    for space in spaces:
                        if space.owner:
                            space.mortgage = not space.mortgage

                elif action == "buildHouse":
                    for space in spaces:
                        assert space.type == "terrain"

                        space.houseCount += 1

                elif action == "removeHouse":
                    for space in spaces:
                        assert space.type == "terrain"

                        space.houseCount -= 1

                elif action == "buildHotel":
                    for space in spaces:
                        assert space.type == "terrain"

                        space.hotelCount += 1

                elif action == "removeHotel":
                    for space in spaces:
                        assert space.type == "terrain"

                        space.hotelCount -= 1
            elif opt == "teleportPlayer":
                player = self.selectPlayerMenu(self.game.debugPlayer, "Player")

                pos = input("Pos: ").strip()

                try:
                    pos = int(pos)
                except ValueError:
                    self.writeLnFlush("Error during conversion to int")
                    continue

                pos %= 39

                player.pos = pos

                player.render()
            else:
                self.playerMessage(self.game.debugPlayer, "notImplemented")

    def playerMenu(self, player: Player, canRollDices: bool, do_render: bool, has_played: bool):
        items = []
        args = []

        if canRollDices:
            items.append("rollDicesJail" if player.inJail else "rollDices")
        else:
            items.append("finish")

        if has_played and isinstance(player.space, OwnableSpace) and player.space.forSale:
            items.append("buy")

        if player.inJail and not has_played:
            items.append("payJail")

            if "jail_card" in player.cards:
                items.append("jailCard")

        if len(player.ownedSpaces) != 0:
            if any((not s.mortgage) for s in player.ownedSpaces):
                items.append("mortgage")

            if any(s.mortgage for s in player.ownedSpaces):
                items.append("liftMortgage")

            if player.ownedGroups:
                items.append("buyHousesOrHotels")

            if any(s.houseCount + s.hotelCount for s in player.ownedSpaces if s.type == "terrain"):
                items.append("saleHousesOrHotels")

        if do_render:
            self.renderPlayer(player)

            self.writeLnFlush()

        if player.inJail:
            self.playerMessage(player, "playerInJail")

        items = [(it, self.lang["menu"](it, player=player)) for it in items]

        zero = ("debug", ITALIC + "debug menu" + RESET) if self.game.debug else None

        opt = self.renderMenu(player, self.lang["menu"]["menu"], items, zero)

        if opt == "mortgage":
            items = [*(s for s in player.ownedSpaces if not s.mortgage)]

            items = [*((sp, self.lang["menu"]("mortgageProp", space=sp)) for sp in items)]

            prop = self.renderMenu(player, self.lang["menu"]["mortgageMenu"], items, self.cancel_opt)

            if prop == "cancel":
                return "pass", args

            args.append(prop)

        elif opt == "liftMortgage":
            items = [*(s for s in player.ownedSpaces if s.mortgage)]

            items = [*((sp, self.lang["menu"]("liftMortgageProp", space=sp)) for sp in items)]

            prop = self.renderMenu(player, self.lang["menu"]["liftMortgageMenu"], items, self.cancel_opt)

            if prop == "cancel":
                return "pass", args

            args.append(prop)

        elif opt == "debug":
            self.debugMenu()

            return "pass", args
        
        elif opt == "buyHousesOrHotels":
            items = [*map(lambda g: (g, self.renderGroup(g)), player.ownedGroups)]
            group = self.renderMenu(player, self.lang["groupWhereBuildHouseOrHotel"], items, self.cancel_opt)

            if group == "cancel":
                return "pass", args

            items = [*map(lambda s: (s, s.render), self.map.getGroupTerrains(group))]
            space = self.renderMenu(player, self.lang["groupWhereBuildHouseOrHotel"], items, self.cancel_opt)

            if space == "cancel":
                return "pass", args

            args.append(space)

            items = [(False, self.lang["house"]), (True, self.lang["hotel"])]
            hotel = self.renderMenu(player, self.lang["whatDoYouWantToBuild"], items, self.cancel_opt)

            if hotel == "cancel":
                return "pass", args
            
            args.append(hotel)

        return opt, args
