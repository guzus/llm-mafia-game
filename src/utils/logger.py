"""Logger for the Mafia game."""

import os
from datetime import datetime
import time
from enum import Enum


class Color(Enum):
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


class GameLogger:
    """Logger for the Mafia game simulation."""

    def __init__(self, log_to_file: bool = True, log_dir: str = "logs"):
        self.log_to_file = log_to_file
        self.log_file = None
        self.Color = Color

        # Role and phase colors
        self.role_colors = {
            "Mafia": Color.RED,
            "Villager": Color.GREEN,
            "Doctor": Color.BLUE,
        }

        self.phase_colors = {
            "setup": Color.CYAN,
            "night": Color.BRIGHT_BLUE,
            "day": Color.BRIGHT_YELLOW,
        }

        # Create log directory and file
        if log_to_file:
            os.makedirs(log_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = open(f"{log_dir}/mafia_game_{timestamp}.log", "w")

    def __del__(self):
        if self.log_file:
            self.log_file.close()

    def _write_to_file(self, text: str):
        """Write plain text to log file."""
        if self.log_to_file and self.log_file:
            clean_text = text
            for color in Color:
                clean_text = clean_text.replace(color.value, "")
            self.log_file.write(clean_text + "\n")
            self.log_file.flush()

    def print(
        self,
        text: str,
        color: Color = None,
        bold: bool = False,
        underline: bool = False,
    ):
        """Print colored text to console and log file."""
        formatted_text = text

        if color:
            formatted_text = f"{color.value}{formatted_text}"
        if bold:
            formatted_text = f"{Color.BOLD.value}{formatted_text}"
        if underline:
            formatted_text = f"{Color.UNDERLINE.value}{formatted_text}"
        if color or bold or underline:
            formatted_text = f"{formatted_text}{Color.RESET.value}"

        print(formatted_text)
        self._write_to_file(formatted_text)

    def header(self, text: str, color: Color = Color.CYAN):
        """Print a header with a box around it."""
        width = len(text) + 4
        border = "+" + "-" * (width - 2) + "+"

        self.print("")
        self.print(border, color, bold=True)
        self.print(f"| {text} |", color, bold=True)
        self.print(border, color, bold=True)

    def game_start(self, game_number: int, game_id: str, language: str):
        """Log game start."""
        self.header(
            f"GAME {game_number} (ID: {game_id} LANGUAGE: {language}) STARTED",
            Color.BRIGHT_MAGENTA,
        )

    def game_end(self, game_number: int, winner: str, rounds: int):
        """Log game end."""
        color = Color.RED if winner == "Mafia" else Color.GREEN
        self.header(
            f"GAME {game_number} ENDED - {winner} WIN AFTER {rounds} ROUNDS", color
        )

    def phase_header(self, phase: str, round_number: int):
        """Log phase header."""
        color = self.phase_colors.get(phase.lower(), Color.WHITE)
        self.header(f"{phase.upper()} PHASE - ROUND {round_number}", color)

    def player_setup(
        self, player_name: str, role: str, player_display_name: str = None
    ):
        """Log player setup."""
        role_color = self.role_colors.get(role, Color.WHITE)
        self.print(f"Player: {player_name}", Color.BRIGHT_WHITE, bold=True)
        if player_display_name and player_display_name != player_name:
            self.print(f"Name: {player_display_name}", Color.BRIGHT_CYAN, bold=True)
        self.print(f"Role: {role}", role_color, bold=True)
        self.print("-" * 40, Color.BRIGHT_BLACK)

    def player_response(
        self, model_name: str, role: str, response: str, player_name: str = None
    ):
        """Log player response."""
        role_color = self.role_colors.get(role, Color.WHITE)
        formatted_response = response.replace("\n", "\n    ")

        display_name = model_name
        if player_name and player_name != model_name:
            display_name = f"{player_name} [{model_name}]"

        self.print(f"┌─ {display_name} ({role}) ", role_color, bold=True)
        self.print(f"└─ {formatted_response}", Color.WHITE)
        self.print("")

    def player_action(
        self, model_name: str, role: str, action: str, player_name: str = None
    ):
        """Log player action."""
        role_color = self.role_colors.get(role, Color.WHITE)

        display_name = model_name
        if player_name and player_name != model_name:
            display_name = f"{player_name} [{model_name}]"

        self.print(f"ACTION: {display_name} ({role}) - {action}", role_color, bold=True)

    def event(self, text: str, color: Color = Color.YELLOW):
        """Log game event."""
        self.print(f"EVENT: {text}", color, bold=True)

    def error(self, text: str):
        """Log an error message."""
        self.print(f"ERROR: {text}", Color.RED, bold=True)

    def warning(self, text: str):
        """Log a warning message."""
        self.print(f"WARNING: {text}", Color.YELLOW, bold=True)

    def stats(self, stats_dict: dict):
        """Log game statistics."""
        self.header("GAME STATISTICS", Color.BRIGHT_CYAN)
        for key, value in stats_dict.items():
            if key == "elapsed_time":
                self.print(
                    f"{key.replace('_', ' ').title()}: {value:.2f} seconds", Color.WHITE
                )
            else:
                self.print(f"{key.replace('_', ' ').title()}: {value}", Color.WHITE)
