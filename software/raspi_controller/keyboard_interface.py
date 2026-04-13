from __future__ import annotations

import select
import sys
import termios
import tty
from dataclasses import dataclass
from typing import Literal

Command = Literal["stop", "forward", "backward", "turn_left", "turn_right", "quit"]


@dataclass(frozen=True)
class KeyBinding:
    sequence: str
    command: Command
    label: str


KEY_BINDINGS = (
    KeyBinding("\x1b[A", "forward", "arrow up"),
    KeyBinding("\x1b[B", "backward", "arrow down"),
    KeyBinding("\x1b[D", "turn_left", "arrow left"),
    KeyBinding("\x1b[C", "turn_right", "arrow right"),
    KeyBinding("k", "forward", "k"),
    KeyBinding("j", "backward", "j"),
    KeyBinding("h", "turn_left", "h"),
    KeyBinding("l", "turn_right", "l"),
    KeyBinding(" ", "stop", "space"),
    KeyBinding("s", "stop", "s"),
    KeyBinding("q", "quit", "q"),
)


class KeyboardInterface:
    """Non-blocking terminal keyboard reader for SSH or a local Pi terminal."""

    def __init__(self) -> None:
        self._command: Command = "stop"
        self._fd = sys.stdin.fileno()
        self._old_settings = None

        try:
            self._old_settings = termios.tcgetattr(self._fd)
        except termios.error:
            print("[keyboard] stdin is not a TTY; keyboard input is disabled.")
            return

        tty.setcbreak(self._fd)
        print(
            "\nKeyboard control:\n"
            "  k / j  = walk forward / backward\n"
            "  h / l  = turn left / right\n"
            "  ↑ / ↓  = walk forward / backward\n"
            "  ← / →  = turn left / right\n"
            "  Space  = stop and hold neutral stance\n"
            "  q      = quit safely\n"
        )

    # EVENT CHECKER:
    # Reads keyboard input and returns the event/command for the movement state
    # machine: stop, forward, backward, turn_left, turn_right, or quit.
    def poll(self) -> Command:
        if self._old_settings is None:
            return self._command

        while _has_input():
            sequence = sys.stdin.read(1)
            if sequence == "\x1b" and _has_input(timeout=0.01):
                sequence += sys.stdin.read(1)
                if _has_input(timeout=0.01):
                    sequence += sys.stdin.read(1)

            for binding in KEY_BINDINGS:
                if sequence == binding.sequence:
                    if binding.command != self._command:
                        print(f"[keyboard] {binding.label} -> {binding.command}")
                    self._command = binding.command
                    break

        return self._command

    # SERVICE FUNCTION:
    # Restores terminal settings when the movement controller shuts down.
    def close(self) -> None:
        if self._old_settings is not None:
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old_settings)
            self._old_settings = None

# EVENT CHECKER HELPER:
# Checks whether the terminal has keyboard input waiting to be read.
def _has_input(timeout: float = 0.0) -> bool:
    readable, _, _ = select.select([sys.stdin], [], [], timeout)
    return bool(readable)
