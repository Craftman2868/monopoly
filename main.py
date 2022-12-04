from monopoly import Monopoly
from monopoly import LANG_LIST, DEFAULT_LANG, MAP_LIST, DEFAULT_MAP

from argparse import ArgumentParser

DEFAULT_PLAYER_COUNT = 4


"""
TODO:
    - échange
    - enregistrer partie
    - maisons / hotels
"""


def main():
    parser = ArgumentParser(__file__, description="Monopoly Game")

    parser.add_argument("--lang", "-l", choices=LANG_LIST, default=DEFAULT_LANG, help="the language of the game")
    parser.add_argument("--map", "-m", choices=MAP_LIST, default=DEFAULT_MAP, help="the map of the game")
    parser.add_argument("--player-count", "-p", type=int, dest="pc", metavar="Player Count", default=DEFAULT_PLAYER_COUNT, help="the number of player")
    parser.add_argument("--no-name", "-n", action="store_true", dest="nn", help="if specified, don't ask player name (use default names, ex: Player 1)")
    parser.add_argument("--debug", "-d", action="store_true", help="debug mode")

    args = parser.parse_args()

    game = Monopoly(playerCount=args.pc, lang=args.lang, map=args.map, debug=args.debug)

    if not args.nn:
        for pl in game.players:
            name = input(game.lang("nameOf", player = pl) + ": ").strip()
            
            pl.name = name or None

    game.run()

if __name__ == "__main__":
    main()
