import sys
from abc import ABC, abstractmethod


class IConsoleDisplay(ABC):
    """Abstract console I/O interface supporting Dependency Inversion."""

    @abstractmethod
    def show_message(self, message: str) -> None: pass

    @abstractmethod
    def show_error(self, error: str) -> None: pass

    @abstractmethod
    def read_input(self, prompt: str) -> str: pass


class StandardConsoleDisplay(IConsoleDisplay):
    def show_message(self, message: str) -> None:
        sys.stdout.write(message + "\n")
        sys.stdout.flush()

    def show_error(self, error: str) -> None:
        sys.stderr.write(f"[ERROR]: {error}\n")
        sys.stderr.flush()

    def read_input(self, prompt: str) -> str:
        sys.stdout.write(prompt)
        sys.stdout.flush()
        return sys.stdin.readline().strip()
