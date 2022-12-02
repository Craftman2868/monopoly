from monopoly import Monopoly


def main():
    game = Monopoly(lang="french", map="France")

    game.run()

if __name__ == "__main__":
    main()
