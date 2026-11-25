"""Shared console behaviour: numbered menu, clear screen, pause and text formats."""

import getpass
import os
import sys

from domain.exceptions import ViajesAventuraError
from persistence.database import DatabaseError

PAUSE_PROMPT = "\nPresiona Enter para volver al menú..."

# ANSI codes: clear the screen, clear the scroll history, move the cursor to the top.
# They work in Git Bash, PowerShell, CMD, Windows Terminal, VS Code, macOS and Linux.
CLEAR_CODES = "\033[2J\033[3J\033[H"

if os.name == "nt":
    os.system("")  # turns on ANSI codes in the classic Windows console


def clear_screen():
    """Clear the console. Git Bash (mintty) may not report a terminal, but sets TERM."""
    if sys.stdout.isatty() or os.environ.get("TERM", "").startswith("xterm"):
        sys.stdout.write(CLEAR_CODES)
        sys.stdout.flush()


def money(amount):
    """450000 -> $450.000"""
    return "$" + f"{amount:,}".replace(",", ".")


def day(value):
    """date(2026, 11, 20) -> 20-11-2026"""
    return value.strftime("%d-%m-%Y") if value else "-"


class ConsoleMenu:
    """Numbered menu. Each option is (label, action) or (label, action, pause_after).

    The screen is cleared before the menu and after choosing, so only the
    current action is visible; after it, the menu waits for Enter.
    """

    TITLE = "Menú"
    EXIT_LABEL = "Volver"

    def __init__(self, input_func=input, output_func=print, clear_func=None, pause=True,
                 password_func=None):
        self._input = input_func
        self._print = output_func
        self._clear = clear_func or clear_screen
        self._pause = pause
        self._read_password = password_func or getpass.getpass

    def options(self):
        raise NotImplementedError

    def header(self):
        """Optional line under the title (for example, who is logged in)."""
        return None

    def run(self):
        options = self.options()
        while True:
            self._clear()
            self._print(f"=== {self.TITLE} ===")
            if self.header():
                self._print(self.header())
            for number, option in enumerate(options, start=1):
                self._print(f"{number}. {option[0]}")
            self._print(f"0. {self.EXIT_LABEL}")
            choice = self._input("Elige una opción: ").strip()
            self._clear()
            if choice == "0":
                return
            pause_after = True
            if choice.isdigit() and 1 <= int(choice) <= len(options):
                label, action, *rest = options[int(choice) - 1]
                pause_after = rest[0] if rest else True
                if pause_after:
                    self._print(f"--- {label} ---")
                try:
                    action()
                except (ViajesAventuraError, DatabaseError) as error:
                    self._print(f"Error: {error}")
                    pause_after = True
            else:
                self._print("Opción no válida.")
            if self._pause and pause_after:
                self._input(PAUSE_PROMPT)

    def _confirm(self, question):
        return self._input(f"{question} (s/n): ").strip().lower() == "s"

    def _submenu_settings(self):
        """Pass the same console functions to a menu opened from this one."""
        return {
            "input_func": self._input, "output_func": self._print,
            "clear_func": self._clear, "pause": self._pause,
            "password_func": self._read_password,
        }
