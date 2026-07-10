from __future__ import annotations

from collections.abc import Iterable

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:  # pragma: no cover - fallback for minimal environments
    Console = None
    Table = None


class TUIConsole:
    def __init__(self) -> None:
        self._console = Console() if Console else None

    def print(self, message: str = "") -> None:
        if self._console:
            self._console.print(message)
        else:
            print(message)

    def rule(self, title: str) -> None:
        if self._console:
            self._console.rule(title)
        else:
            print(f"\n--- {title} ---")

    def table(self, title: str, columns: list[str], rows: Iterable[Iterable[str]]) -> None:
        if self._console and Table:
            table = Table(title=title)
            for column in columns:
                table.add_column(column)
            for row in rows:
                table.add_row(*[str(item) for item in row])
            self._console.print(table)
            return
        print(title)
        print(" | ".join(columns))
        for row in rows:
            print(" | ".join(str(item) for item in row))


console = TUIConsole()


def prompt_text(label: str) -> str:
    try:
        from prompt_toolkit import prompt

        return prompt(f"{label}: ")
    except ImportError:  # pragma: no cover
        return input(f"{label}: ")
