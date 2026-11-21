from core.text import Document, IDocumentVisitor, MarkdownExportVisitor
from core.characters import GameEngine, IGameObserver
from infra.display import IConsoleDisplay


class TextPresenter:
    """Presenter responsible for rendering structured documents via Visitor."""

    def __init__(self, display: IConsoleDisplay):
        self._display = display

    def present_whole_document(self, doc: Document, visitor: IDocumentVisitor = None) -> None:
        active_visitor = visitor or MarkdownExportVisitor()
        output = [f"=== DOCUMENT: {doc.title} ===\n", doc.export(active_visitor)]
        self._display.show_message("\n".join(output))


class GamePresenter(IGameObserver):
    """Presenter for displaying catalog entries and real-time game events."""

    def __init__(self, display: IConsoleDisplay):
        self._display = display

    def on_game_event(self, event_type: str, message: str) -> None:
        self._display.show_message(f"[{event_type}] {message}")

    def present_objects(self, engine: GameEngine, mode: str) -> None:
        if mode == "char":
            if not engine.characters:
                self._display.show_message("Catalog is empty.")
                return
            for i, c in enumerate(engine.characters):
                strat = c.attack_strategy.__class__.__name__
                self._display.show_message(
                    f"[{i}] {c.name} ({c.__class__.__name__}) — HP: {c.health}/{c.max_health} | "
                    f"ATK: {c.total_attack_power} | ARM: {c.total_armor} | Strategy: {strat}"
                )
