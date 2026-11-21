from abc import ABC, abstractmethod
from typing import List
import copy


# ==============================================================================
# VISITOR PATTERN
# Purpose: Separates document traversal and formatting algorithms from the
# document element classes (Paragraph, Heading, Link, Image).
# ==============================================================================
class IDocumentVisitor(ABC):
    """Visitor interface declaring visit methods for each concrete element type."""

    @abstractmethod
    def visit_paragraph(self, element: 'Paragraph') -> str: pass

    @abstractmethod
    def visit_heading(self, element: 'Heading') -> str: pass

    @abstractmethod
    def visit_link(self, element: 'Link') -> str: pass

    @abstractmethod
    def visit_image(self, element: 'Image') -> str: pass


class MarkdownExportVisitor(IDocumentVisitor):
    """Concrete visitor that renders document elements into Markdown format."""

    def visit_paragraph(self, element: 'Paragraph') -> str:
        return element.content

    def visit_heading(self, element: 'Heading') -> str:
        prefix = "#" * element.level
        return f"{prefix} {element.text.upper() if element.level == 1 else element.text}"

    def visit_link(self, element: 'Link') -> str:
        return f"{element.text} ({element.url})"

    def visit_image(self, element: 'Image') -> str:
        return f"[IMAGE: {element.alt_text} -> {element.src}]"


class PlainTextExportVisitor(IDocumentVisitor):
    """Concrete visitor that strips markup and outputs clean plain text."""

    def visit_paragraph(self, element: 'Paragraph') -> str:
        return element.content

    def visit_heading(self, element: 'Heading') -> str:
        return element.text.upper() if element.level == 1 else element.text

    def visit_link(self, element: 'Link') -> str:
        return f"{element.text} [{element.url}]"

    def visit_image(self, element: 'Image') -> str:
        return f"Image: {element.alt_text} ({element.src})"


class TextElement(ABC):
    """Abstract base class for all structured document elements."""

    @abstractmethod
    def accept(self, visitor: IDocumentVisitor) -> str:
        """Entry point for the Visitor pattern (double dispatch)."""
        pass

    def render(self) -> str:
        """Default rendering helper delegating to MarkdownExportVisitor."""
        return self.accept(MarkdownExportVisitor())


class Paragraph(TextElement):
    def __init__(self, content: str):
        self._content = content

    @property
    def content(self) -> str:
        return self._content

    def accept(self, visitor: IDocumentVisitor) -> str:
        return visitor.visit_paragraph(self)


class Link(TextElement):
    def __init__(self, text: str, url: str):
        self._text = text
        self._url = url

    @property
    def text(self) -> str:
        return self._text

    @property
    def url(self) -> str:
        return self._url

    def accept(self, visitor: IDocumentVisitor) -> str:
        return visitor.visit_link(self)


class Image(TextElement):
    def __init__(self, alt_text: str, src: str):
        self._alt_text = alt_text
        self._src = src

    @property
    def alt_text(self) -> str:
        return self._alt_text

    @property
    def src(self) -> str:
        return self._src

    def accept(self, visitor: IDocumentVisitor) -> str:
        return visitor.visit_image(self)


class Heading(TextElement):
    def __init__(self, text: str, level: int = 1):
        if not (1 <= level <= 6):
            raise ValueError("Heading level must be between 1 and 6.")
        self._text = text
        self._level = level

    @property
    def text(self) -> str:
        return self._text

    @property
    def level(self) -> int:
        return self._level

    def accept(self, visitor: IDocumentVisitor) -> str:
        return visitor.visit_heading(self)


# ==============================================================================
# MEMENTO PATTERN
# Purpose: Captures and externalizes internal Document state without violating
# encapsulation so the document can be restored later (Undo functionality).
# ==============================================================================
class DocumentMemento:
    """Snapshot of a Document's state (Memento)."""

    def __init__(self, title: str, elements: List[TextElement]):
        self._title = title
        self._elements = copy.deepcopy(elements)

    def get_saved_title(self) -> str:
        return self._title

    def get_saved_elements(self) -> List[TextElement]:
        return copy.deepcopy(self._elements)


class DocumentHistory:
    """Caretaker managing the stack of DocumentMemento snapshots."""

    def __init__(self):
        self._history: List[DocumentMemento] = []

    def push(self, memento: DocumentMemento) -> None:
        self._history.append(memento)

    def pop(self) -> DocumentMemento:
        if not self._history:
            raise IndexError("History is empty. Nothing to undo.")
        return self._history.pop()

    def has_history(self) -> bool:
        return len(self._history) > 0


class Document:
    """Document container acting as the Originator in the Memento pattern."""

    def __init__(self, title: str):
        self._title = title
        self._elements: List[TextElement] = []

    @property
    def title(self) -> str:
        return self._title

    @property
    def elements(self) -> List[TextElement]:
        return self._elements

    def create_memento(self) -> DocumentMemento:
        return DocumentMemento(self._title, self._elements)

    def restore_memento(self, memento: DocumentMemento) -> None:
        self._title = memento.get_saved_title()
        self._elements = memento.get_saved_elements()

    def export(self, visitor: IDocumentVisitor) -> str:
        return "\n\n".join(el.accept(visitor) for el in self._elements)

    def add_element(self, element: TextElement) -> None:
        self._elements.append(element)

    def remove_element_at(self, index: int) -> None:
        if 0 <= index < len(self._elements):
            self._elements.pop(index)
        else:
            raise IndexError("Element index out of range.")

    def move_element(self, from_index: int, to_index: int) -> None:
        if 0 <= from_index < len(self._elements) and 0 <= to_index < len(self._elements):
            element = self._elements.pop(from_index)
            self._elements.insert(to_index, element)
        else:
            raise IndexError("Index out of range.")


class DocumentBuilder:
    """Fluent Builder API for constructing structured documents."""

    def __init__(self, title: str):
        self._document = Document(title)

    def add_heading(self, text: str, level: int = 1) -> 'DocumentBuilder':
        self._document.add_element(Heading(text, level))
        return self

    def add_paragraph(self, content: str) -> 'DocumentBuilder':
        self._document.add_element(Paragraph(content))
        return self

    def add_link(self, text: str, url: str) -> 'DocumentBuilder':
        self._document.add_element(Link(text, url))
        return self

    def add_image(self, alt_text: str, src: str) -> 'DocumentBuilder':
        self._document.add_element(Image(alt_text, src))
        return self

    def get_document(self) -> Document:
        return self._document
