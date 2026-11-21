import os
import tempfile
import unittest
from infra.display import IConsoleDisplay
from infra.data import FileStorageRepository
from core.characters import GameEngine
from cli.presenter import GamePresenter, TextPresenter
from cli.commands import CatalogInterpreter, GameInterpreter, TextInterpreter


class MockDisplay(IConsoleDisplay):
    def __init__(self, inputs: list):
        self.inputs = list(inputs)
        self.messages = []
        self.errors = []

    def show_message(self, message: str) -> None:
        self.messages.append(message)

    def show_error(self, error: str) -> None:
        self.errors.append(error)

    def read_input(self, prompt: str) -> str:
        return self.inputs.pop(0) if self.inputs else "exit"


class TestFullCLISystem(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = FileStorageRepository(self.temp_dir.name)
        self.engine = GameEngine()
        self.engine.setup_demo()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_topic1_catalog_create_info_and_persistence(self):
        inputs = [
            "create",
            "Arthur Pendragon",
            "1",
            "150",
            "20",
            "25",
            "King of Camelot",
            "https://example.com/arthur.png",
            "info 2",
            "save",
            "exit"
        ]
        display = MockDisplay(inputs)
        presenter = GamePresenter(display)
        cli = CatalogInterpreter(display, presenter, self.engine, self.storage)
        cli.run()

        self.assertEqual(len(self.engine.characters), 3)
        self.assertTrue(any("https://example.com/arthur.png" in m for m in display.messages))

        loaded = self.storage.load_characters()
        self.assertEqual(len(loaded), 3)
        self.assertEqual(loaded[2].name, "Arthur Pendragon")

    def test_topic2_combat_game_loop_and_save_result(self):
        inputs = [
            "select 0 1",
            "start",
            "attack",
            "strategy pyroblast",
            "attack",
            "attack",
            "attack",
            "attack",
            "attack",
            "attack",
            "save-result",
            "exit"
        ]
        display = MockDisplay(inputs)
        presenter = GamePresenter(display)
        cli = GameInterpreter(display, presenter, self.engine, self.storage)
        cli.run()

        self.assertIsNotNone(self.engine.winner)
        result_file = os.path.join(self.temp_dir.name, "game_results.json")
        self.assertTrue(os.path.exists(result_file))

    def test_topic3_structured_text_editor_undo_and_export(self):
        inputs = [
            "add-h 1 Battle Chronicle",
            "add-p Mistake line",
            "undo",
            "add-p The heroes prevailed.",
            "add-img Banner https://example.com/banner.png",
            "render plain",
            "export-doc report.md",
            "exit"
        ]
        display = MockDisplay(inputs)
        presenter = TextPresenter(display)
        cli = TextInterpreter(display, presenter, self.storage)
        cli.run()

        exported = os.path.join(self.temp_dir.name, "report.md")
        self.assertTrue(os.path.exists(exported))
        with open(exported, "r", encoding="utf-8") as f:
            text = f.read()
        self.assertIn("# BATTLE CHRONICLE", text)
        self.assertIn("The heroes prevailed.", text)
        self.assertNotIn("Mistake line", text)


if __name__ == "__main__":
    unittest.main()
