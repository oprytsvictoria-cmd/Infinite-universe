# RPG Character Catalog, Text Combat Engine & Structured Lore Editor

A modular, SOLID-compliant Command-Line Interface (CLI) application built in Python that integrates three functional modes within a single unified runtime:
1. **Character Catalog:** Sync characters from remote/fallback API, inspect profiles with graphics URLs, create custom characters via an interactive wizard, and persist data to JSON.
2. **Text-Based Combat Game:** Select fighters from the catalog, execute a turn-based combat loop with dynamic strategy switching, and save match outcomes.
3. **Structured Text & Lore Editor:** Build Markdown/PlainText documents with Undo history (`Memento`) and multi-format rendering (`Visitor`).

See [DESIGN_DOCUMENT.md](DESIGN_DOCUMENT.md) for full architectural specifications.

## Running the Application
```bash
python main.py
```

## Running Tests
```bash
python -m unittest discover -s tests -v
```
