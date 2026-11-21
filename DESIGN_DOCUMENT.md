# Software Design Document (SDD)
**Project Name:** RPG Character Catalog, Text Combat Engine & Structured Lore Editor  
**Version:** 1.0  
**Architecture Style:** Layered Architecture + Command / Template Method / Strategy / Observer / Memento / Visitor  

---

## 1. Purpose and Scope
This document describes the software architecture, module structure, and Command-Line Interface (CLI) design of a modular console application. The system integrates three functional domains within a single unified process:
1. **Topic 1 — Character Catalog:** Synchronizing characters from a remote/fallback API, viewing detailed character profiles (including graphics/avatar URLs), creating custom characters via an interactive CLI wizard, and persisting user-created characters to local JSON storage.
2. **Topic 2 — Text-Based Combat Game:** Selecting playable characters from the catalog, initializing an interactive turn-based battle loop, executing combat actions, dynamically switching combat strategies, and saving match results/logs.
3. **Topic 3 — Custom Domain (Structured Text & Lore Editor):** Managing structured documents (headings, paragraphs, links, images) with undo history (Memento) and multi-format export (Visitor) for character dossiers and game chronicles.

---

## 2. System Architecture & Project Structure

The project strictly follows **SOLID principles** and separates concerns across four layers:

```text
RPG_CLI_System/
├── core/                        # Domain Models & Business Logic (Zero I/O dependencies)
│   ├── characters.py            # Character, Warrior, Mage, Item, Strategy, Observer, GameEngine
│   └── text.py                  # Document, TextElements, DocumentBuilder, Visitor, Memento
├── infra/                       # External Integrations, Persistence & Console I/O
│   ├── display.py               # IConsoleDisplay & StandardConsoleDisplay
│   ├── data.py                  # ISerializer, JSONDataMapper & FileStorageRepository
│   └── remote.py                # GenshinHttpClient (API client with offline fallback)
├── cli/                         # Command-Line Interface & Presentation Layer
│   ├── commands.py              # Command, Interpreter (Template Method) & 3 Mode Interpreters
│   └── presenter.py             # GamePresenter & TextPresenter
├── tests/                       # Unit & Integration Tests
│   └── test_cli_full.py         # Automated tests for Catalog, Game Loop, Storage, and Text Editor
├── DESIGN_DOCUMENT.md           # This architectural specification
├── README.md                    # Quickstart & repository overview
└── main.py                      # Application Entry Point & Mode Router
```

### Layer Responsibilities
* **Core Layer (`core/`):** Contains pure domain entities (`Warrior`, `Mage`, `Document`) and behavioral design patterns (`IAttackStrategy`, `IDocumentVisitor`, `DocumentMemento`, `GameEventManager`). It has zero direct dependencies on console I/O or file paths.
* **Infrastructure Layer (`infra/`):** Abstracts external dependencies behind interfaces (`IConsoleDisplay`, `ISerializer`). Handles JSON persistence (`storage/characters.json`, `storage/game_results.json`) and HTTP requests to `genshin.jmp.blue` with an automatic offline fallback generator.
* **Presentation & CLI Layer (`cli/`):** Implements the **Command** and **Template Method** patterns. `Interpreter` manages the REPL loop, while dedicated `Presenter` classes format domain objects for console output.

---

## 3. Detailed CLI Implementation Specification

### 3.1 Command Loop Architecture (`Interpreter` & `Command`)
Every CLI mode inherits from the abstract `Interpreter` class, which implements a **Template Method** (`run()`):
1. Displays mode-specific banner (`show_welcome()`) and available commands (`show_help()`).
2. Reads user input via `IConsoleDisplay.read_input("> ")`.
3. Splits input into `command_name` and `args`.
4. Handles built-in navigation commands (`help`, `back`/`exit`/`quit`) or dispatches execution to a registered `Command` object (`execute(args)`).
5. Catches exceptions gracefully and renders errors via `IConsoleDisplay.show_error()`.

---

### 3.2 Mode 1: Character Catalog (`CatalogInterpreter`)
Manages discovery, inspection, creation, and persistence of game characters.

| Command | Arguments | Action Description |
| :--- | :--- | :--- |
| `list` | none | Displays all available characters (built-in, API-synced, and user-created) with IDs and classes. |
| `sync` | none | Fetches remote character & weapon lists via `GenshinHttpClient` and updates the catalog. |
| `info` | `<char_id>` | Outputs full character dossier: stats, abilities, **graphics/portrait URL**, and structured description. |
| `create` | none | Launches an **interactive multi-step dialog wizard** prompting for Name, Class (`Warrior`/`Mage`), HP, Armor, Attack, Description, and Graphics URL. |
| `save` | none | Serializes all current characters via `JSONDataMapper` to `storage/characters.json`. |
| `load` | none | Restores previously saved characters from `storage/characters.json`. |

---

### 3.3 Mode 2: Text-Based Combat Game (`GameInterpreter`)
Provides an interactive turn-based battle engine with state persistence.

| Command | Arguments | Action Description |
| :--- | :--- | :--- |
| `roster` | none | Lists available characters that can be selected for battle. |
| `select` | `<p1_id> <p2_id>` | Assigns Player 1 and Player 2 fighters for the upcoming match. |
| `start` | none | Initializes the active match state, resets HP to max, and starts the battle session. |
| `attack` | none | Executes the active fighter's current `IAttackStrategy` against the opponent and switches turns. |
| `strategy` | `<melee\|shield\|pyroblast>` | Dynamically swaps the active fighter's combat algorithm (`Strategy` pattern). |
| `status` | none | Displays current HP, ATK, ARM, active turn, and match status. |
| `save-result` | none | Saves the completed or current match state and combat log to `storage/game_results.json`. |

---

### 3.4 Mode 3: Structured Text & Lore Editor (`TextInterpreter`)
Custom domain mode for building structured RPG documentation and lore chronicles.

| Command | Arguments | Action Description |
| :--- | :--- | :--- |
| `add-h` | `<level> <text>` | Adds a Markdown heading (levels 1-6) and records a `DocumentMemento`. |
| `add-p` | `<text>` | Appends a text paragraph and records a `DocumentMemento`. |
| `add-img` | `<alt> <url>` | Embeds a graphics reference element into the document. |
| `undo` | none | Reverts the document to its previous state using `DocumentHistory` (`Memento` pattern). |
| `render` | `[md\|plain]` | Traverses the document using `MarkdownExportVisitor` or `PlainTextExportVisitor`. |
| `export-doc` | `<filename>` | Saves the rendered structured document to `storage/<filename>`. |
