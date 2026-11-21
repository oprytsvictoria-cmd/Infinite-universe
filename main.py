from infra.display import StandardConsoleDisplay
from infra.data import FileStorageRepository
from cli.presenter import TextPresenter, GamePresenter
from cli.commands import CatalogInterpreter, GameInterpreter, TextInterpreter
from core.characters import GameEngine


def main():
    display = StandardConsoleDisplay()
    storage = FileStorageRepository("storage")
    text_presenter = TextPresenter(display)
    game_presenter = GamePresenter(display)

    engine = GameEngine()
    engine.setup_demo()

    while True:
        display.show_message("\n==========================================")
        display.show_message("   RPG CATALOG, GAME & LORE CLI SYSTEM    ")
        display.show_message("==========================================")
        display.show_message("1. Topic 1: Character Catalog (View, Sync, Create, Save)")
        display.show_message("2. Topic 2: Text-Based Combat Game (Select, Battle, Save)")
        display.show_message("3. Topic 3: Structured Text & Lore Editor")
        display.show_message("0. Exit Application")

        choice = display.read_input("Select mode (0-3): ").strip()

        if choice == "1":
            CatalogInterpreter(display, game_presenter, engine, storage).run()
        elif choice == "2":
            GameInterpreter(display, game_presenter, engine, storage).run()
        elif choice == "3":
            TextInterpreter(display, text_presenter, storage).run()
        elif choice == "0":
            display.show_message("Goodbye!")
            break
        else:
            display.show_error("Invalid option. Enter 0, 1, 2, or 3.")


if __name__ == "__main__":
    main()
