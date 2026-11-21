from abc import ABC, abstractmethod
from typing import Dict, List
from core.text import (
    DocumentBuilder, Heading, Paragraph, Image, DocumentHistory,
    MarkdownExportVisitor, PlainTextExportVisitor
)
from core.characters import (
    GameEngine, Warrior, Mage,
    MeleeAttackStrategy, ShieldSlamStrategy, PyroblastAttackStrategy
)
from infra.remote import GenshinHttpClient
from infra.data import FileStorageRepository


# ==============================================================================
# COMMAND PATTERN
# Purpose: Encapsulates each user CLI action as a standalone Command object.
# ==============================================================================
class Command(ABC):
    @abstractmethod
    def execute(self, args: List[str]) -> None: pass

    @abstractmethod
    def get_help(self) -> str: pass


# ==============================================================================
# TEMPLATE METHOD PATTERN
# Purpose: Defines the invariant CLI REPL lifecycle in Interpreter.run() while
# deferring mode-specific initialization to subclasses via show_welcome().
# ==============================================================================
class Interpreter(ABC):
    def __init__(self, display):
        self._commands: Dict[str, Command] = {}
        self._running = True
        self.display = display

    def register_command(self, name: str, command: Command):
        self._commands[name] = command

    def run(self):
        self.show_welcome()
        self.show_help()
        while self._running:
            try:
                line = self.display.read_input("> ")
                if not line:
                    continue
                parts = line.split()
                cmd_name = parts[0].lower()
                cmd_args = parts[1:]

                if cmd_name in ["exit", "quit", "back"]:
                    self._running = False
                    self.display.show_message("Exiting mode...")
                    break
                elif cmd_name == "help":
                    self.show_help()
                elif cmd_name in self._commands:
                    self._commands[cmd_name].execute(cmd_args)
                else:
                    self.display.show_message(f"Unknown command: '{cmd_name}'. Type 'help' for options.")
            except (KeyboardInterrupt, EOFError):
                self.display.show_message("\nExiting...")
                break
            except Exception as e:
                self.display.show_error(str(e))

    def show_help(self):
        self.display.show_message("\nAvailable commands:")
        self.display.show_message("  help        - Show available commands")
        self.display.show_message("  back / exit - Return to main menu or exit")
        for name, cmd in self._commands.items():
            self.display.show_message(f"  {name:<11} - {cmd.get_help()}")

    @abstractmethod
    def show_welcome(self) -> None:
        pass


# ==============================================================================
# TOPIC 1: CHARACTER CATALOG MODE
# ==============================================================================
class CatalogInterpreter(Interpreter):
    def __init__(self, display, presenter, engine: GameEngine, storage: FileStorageRepository):
        super().__init__(display)
        self.presenter = presenter
        self.engine = engine
        self.storage = storage
        self.http_client = GenshinHttpClient()

        self.register_command("list", ListCatalogCommand(self))
        self.register_command("sync", SyncApiCatalogCommand(self))
        self.register_command("info", CharInfoCommand(self))
        self.register_command("create", CreateCharDialogCommand(self))
        self.register_command("save", SaveCatalogCommand(self))
        self.register_command("load", LoadCatalogCommand(self))

    def show_welcome(self):
        self.display.show_message("\n=== TOPIC 1: CHARACTER CATALOG MODE ===")


class ListCatalogCommand(Command):
    def __init__(self, cli: CatalogInterpreter): self.cli = cli
    def get_help(self): return "Display all available characters in the catalog"

    def execute(self, args: List[str]) -> None:
        self.cli.presenter.present_objects(self.cli.engine, "char")


class SyncApiCatalogCommand(Command):
    def __init__(self, cli: CatalogInterpreter): self.cli = cli
    def get_help(self): return "Fetch & update characters from remote API (with offline fallback)"

    def execute(self, args: List[str]) -> None:
        self.cli.display.show_message("Syncing character catalog from API...")
        ids = self.cli.http_client.fetch_character_list()[:3]
        existing_names = {c.name for c in self.cli.engine.characters}
        added = 0
        for cid in ids:
            data = self.cli.http_client.fetch_character_details(cid)
            name = data.get("name", cid.capitalize())
            if name in existing_names:
                continue
            stats = self.cli.http_client.generate_stats_by_rarity(data.get("rarity", 4))
            img_url = f"https://genshin.jmp.blue/characters/{cid.lower()}/icon-big"
            abilities = [{"name": s.get("name"), "description": s.get("description")}
                         for s in data.get("skillTalents", [])]
            if data.get("weapon", "") in ["Sword", "Claymore", "Polearm"]:
                char = Warrior(name, stats["hp"], stats["armor"], stats["attack"],
                               data.get("description", ""), abilities, img_url)
            else:
                char = Mage(name, stats["hp"], stats["armor"], stats["attack"],
                            data.get("description", ""), abilities, img_url)
            self.cli.engine.add_character(char)
            added += 1
        self.cli.display.show_message(f"Catalog updated. New characters added: {added}.")


class CharInfoCommand(Command):
    def __init__(self, cli: CatalogInterpreter): self.cli = cli
    def get_help(self): return "info <id> — Show character details and graphics URL"

    def execute(self, args: List[str]) -> None:
        if not args:
            raise ValueError("Usage: info <character_id>")
        idx = int(args[0])
        char = self.cli.engine.characters[idx]
        self.cli.display.show_message(f"\n--- CHARACTER PROFILE [{idx}] ---")
        self.cli.display.show_message(f"Name:         {char.name}")
        self.cli.display.show_message(f"Class:        {char.__class__.__name__}")
        self.cli.display.show_message(f"Stats:        HP={char.max_health} | ARM={char.total_armor} | ATK={char.total_attack_power}")
        self.cli.display.show_message(f"Description:  {char.description}")
        self.cli.display.show_message(f"Graphics URL: {char.image_url}")


class CreateCharDialogCommand(Command):
    """Interactive multi-step wizard for creating a custom character."""

    def __init__(self, cli: CatalogInterpreter): self.cli = cli
    def get_help(self): return "Create a new character via interactive dialog"

    def execute(self, args: List[str]) -> None:
        d = self.cli.display
        d.show_message("\n--- NEW CHARACTER CREATION WIZARD ---")
        name = d.read_input("Enter character name: ").strip()
        if not name:
            raise ValueError("Character name cannot be empty.")

        role = d.read_input("Choose class (1 - Warrior, 2 - Mage): ").strip()
        hp = int(d.read_input("Enter Health (HP): ").strip() or "100")
        armor = int(d.read_input("Enter Armor (ARM): ").strip() or "10")
        atk = int(d.read_input("Enter Attack Power (ATK): ").strip() or "15")
        desc = d.read_input("Enter short bio/description: ").strip() or "Custom hero"
        img_url = d.read_input("Enter graphics/avatar URL (optional): ").strip()

        if role == "2":
            char = Mage(name, hp, armor, atk, desc, image_url=img_url)
        else:
            char = Warrior(name, hp, armor, atk, desc, image_url=img_url)

        idx = self.cli.engine.add_character(char)
        d.show_message(f"Character '{char.name}' created with ID [{idx}]!")


class SaveCatalogCommand(Command):
    def __init__(self, cli: CatalogInterpreter): self.cli = cli
    def get_help(self): return "Save all characters to local JSON storage"

    def execute(self, args: List[str]) -> None:
        path = self.cli.storage.save_characters(self.cli.engine.characters)
        self.cli.display.show_message(f"Saved {len(self.cli.engine.characters)} characters to '{path}'.")


class LoadCatalogCommand(Command):
    def __init__(self, cli: CatalogInterpreter): self.cli = cli
    def get_help(self): return "Load saved characters from local JSON storage"

    def execute(self, args: List[str]) -> None:
        loaded = self.cli.storage.load_characters()
        self.cli.engine._characters = loaded
        self.cli.display.show_message(f"Loaded {len(loaded)} characters from storage.")


# ==============================================================================
# TOPIC 2: TEXT-BASED COMBAT GAME MODE
# ==============================================================================
class GameInterpreter(Interpreter):
    def __init__(self, display, presenter, engine: GameEngine, storage: FileStorageRepository):
        super().__init__(display)
        self.presenter = presenter
        self.engine = engine
        self.storage = storage
        self.engine.events.subscribe(self.presenter)

        self.register_command("roster", RosterCommand(self))
        self.register_command("select", SelectFightersCommand(self))
        self.register_command("start", StartMatchCommand(self))
        self.register_command("attack", TurnAttackCommand(self))
        self.register_command("strategy", SwitchTurnStrategyCommand(self))
        self.register_command("status", MatchStatusCommand(self))
        self.register_command("save-result", SaveMatchResultCommand(self))

    def show_welcome(self):
        self.display.show_message("\n=== TOPIC 2: TEXT-BASED COMBAT GAME MODE ===")


class RosterCommand(Command):
    def __init__(self, cli: GameInterpreter): self.cli = cli
    def get_help(self): return "List available characters for selection"

    def execute(self, args: List[str]) -> None:
        self.cli.presenter.present_objects(self.cli.engine, "char")


class SelectFightersCommand(Command):
    def __init__(self, cli: GameInterpreter): self.cli = cli
    def get_help(self): return "select <p1_id> <p2_id> — Choose two fighters"

    def execute(self, args: List[str]) -> None:
        if len(args) < 2:
            raise ValueError("Usage: select <player1_id> <player2_id>")
        self.cli.engine.select_fighters(int(args[0]), int(args[1]))


class StartMatchCommand(Command):
    def __init__(self, cli: GameInterpreter): self.cli = cli
    def get_help(self): return "Start the combat match loop"

    def execute(self, args: List[str]) -> None:
        self.cli.engine.start_game()
        self.cli.display.show_message(f"Turn 1: {self.cli.engine.player1.name}'s move! Type 'attack' or 'strategy'.")


class TurnAttackCommand(Command):
    def __init__(self, cli: GameInterpreter): self.cli = cli
    def get_help(self): return "Perform attack in the active match loop"

    def execute(self, args: List[str]) -> None:
        self.cli.engine.execute_turn_attack()
        if self.cli.engine.game_started:
            next_fighter = (self.cli.engine.player1 if self.cli.engine.active_turn == 1
                            else self.cli.engine.player2)
            self.cli.display.show_message(f"Next turn: {next_fighter.name}")


class SwitchTurnStrategyCommand(Command):
    def __init__(self, cli: GameInterpreter): self.cli = cli
    def get_help(self): return "strategy <melee|shield|pyroblast> — Change active fighter strategy"

    def execute(self, args: List[str]) -> None:
        if not self.cli.engine.game_started:
            raise RuntimeError("Start a match first.")
        if not args:
            raise ValueError("Usage: strategy <melee|shield|pyroblast>")
        fighter = (self.cli.engine.player1 if self.cli.engine.active_turn == 1
                   else self.cli.engine.player2)
        mapping = {
            "melee": MeleeAttackStrategy(),
            "shield": ShieldSlamStrategy(),
            "pyroblast": PyroblastAttackStrategy()
        }
        mode = args[0].lower()
        if mode not in mapping:
            raise ValueError("Choose from: melee, shield, pyroblast")
        fighter.set_attack_strategy(mapping[mode])
        self.cli.display.show_message(f"{fighter.name} switched strategy to {mapping[mode].__class__.__name__}.")


class MatchStatusCommand(Command):
    def __init__(self, cli: GameInterpreter): self.cli = cli
    def get_help(self): return "Show current match HP and turn state"

    def execute(self, args: List[str]) -> None:
        e = self.cli.engine
        if not e.player1 or not e.player2:
            self.cli.display.show_message("No fighters selected yet.")
            return
        self.cli.display.show_message(
            f"P1: {e.player1.name} ({e.player1.health}/{e.player1.max_health} HP) | "
            f"P2: {e.player2.name} ({e.player2.health}/{e.player2.max_health} HP) | "
            f"Winner: {e.winner or 'In Progress'}"
        )


class SaveMatchResultCommand(Command):
    def __init__(self, cli: GameInterpreter): self.cli = cli
    def get_help(self): return "Save match state and combat log to JSON file"

    def execute(self, args: List[str]) -> None:
        summary = self.cli.engine.get_match_summary()
        path = self.cli.storage.save_match_result(summary)
        self.cli.display.show_message(f"Match state & results saved to '{path}'.")


# ==============================================================================
# TOPIC 3: STRUCTURED TEXT & LORE EDITOR MODE (Custom Domain)
# ==============================================================================
class TextInterpreter(Interpreter):
    def __init__(self, display, presenter, storage: FileStorageRepository):
        super().__init__(display)
        self.presenter = presenter
        self.storage = storage
        self.builder = DocumentBuilder("RPG Chronicle Document")
        self.doc = self.builder.get_document()
        self.history = DocumentHistory()

        self.register_command("add-h", AddHeadingCommand(self))
        self.register_command("add-p", AddParagraphCommand(self))
        self.register_command("add-img", AddImageCommand(self))
        self.register_command("undo", UndoTextCommand(self))
        self.register_command("render", RenderTextCommand(self))
        self.register_command("export-doc", ExportTextCommand(self))

    def show_welcome(self):
        self.display.show_message("\n=== TOPIC 3: STRUCTURED LORE & TEXT EDITOR MODE ===")


class AddHeadingCommand(Command):
    def __init__(self, cli: TextInterpreter): self.cli = cli
    def get_help(self): return "add-h <level> <text> — Add structured heading"

    def execute(self, args: List[str]) -> None:
        if len(args) < 2:
            raise ValueError("Usage: add-h <1-6> <text>")
        self.cli.history.push(self.cli.doc.create_memento())
        self.cli.doc.add_element(Heading(" ".join(args[1:]), level=int(args[0])))
        self.cli.display.show_message("Heading added.")


class AddParagraphCommand(Command):
    def __init__(self, cli: TextInterpreter): self.cli = cli
    def get_help(self): return "add-p <text> — Add text paragraph"

    def execute(self, args: List[str]) -> None:
        if not args:
            raise ValueError("Usage: add-p <text>")
        self.cli.history.push(self.cli.doc.create_memento())
        self.cli.doc.add_element(Paragraph(" ".join(args)))
        self.cli.display.show_message("Paragraph added.")


class AddImageCommand(Command):
    def __init__(self, cli: TextInterpreter): self.cli = cli
    def get_help(self): return "add-img <alt_text> <url> — Add graphics element"

    def execute(self, args: List[str]) -> None:
        if len(args) < 2:
            raise ValueError("Usage: add-img <alt_text> <url>")
        self.cli.history.push(self.cli.doc.create_memento())
        self.cli.doc.add_element(Image(args[0], args[1]))
        self.cli.display.show_message("Image element added.")


class UndoTextCommand(Command):
    def __init__(self, cli: TextInterpreter): self.cli = cli
    def get_help(self): return "undo — Revert last document change (Memento)"

    def execute(self, args: List[str]) -> None:
        self.cli.doc.restore_memento(self.cli.history.pop())
        self.cli.display.show_message("Last change undone.")


class RenderTextCommand(Command):
    def __init__(self, cli: TextInterpreter): self.cli = cli
    def get_help(self): return "render [md|plain] — Display formatted document"

    def execute(self, args: List[str]) -> None:
        fmt = args[0].lower() if args else "md"
        visitor = PlainTextExportVisitor() if fmt == "plain" else MarkdownExportVisitor()
        self.cli.presenter.present_whole_document(self.cli.doc, visitor)


class ExportTextCommand(Command):
    def __init__(self, cli: TextInterpreter): self.cli = cli
    def get_help(self): return "export-doc <filename.md> — Save structured document to file"

    def execute(self, args: List[str]) -> None:
        filename = args[0] if args else "chronicle.md"
        rendered = self.cli.doc.export(MarkdownExportVisitor())
        path = self.cli.storage.save_text_document(rendered, filename)
        self.cli.display.show_message(f"Document exported to '{path}'.")
