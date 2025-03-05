"""
Logger for the LLM Mafia Game Competition.
Provides colorful and formatted logging for the game simulation.
"""

import os
from enum import Enum
from datetime import datetime
import time


class Color(Enum):
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # Bright foreground colors
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

    # Make Color accessible as a class attribute
    Color = Color

    def __init__(self, log_to_file=True, log_dir="logs"):
        """
        Initialize the game logger.

        Args:
            log_to_file (bool): Whether to log to a file in addition to console.
            log_dir (str): Directory to store log files.
        """
        self.log_to_file = log_to_file
        self.log_file = None

        # Role colors
        self.role_colors = {
            "Mafia": Color.RED,
            "Villager": Color.GREEN,
            "Doctor": Color.BLUE,
        }

        # Phase colors
        self.phase_colors = {
            "setup": Color.CYAN,
            "night": Color.BRIGHT_BLUE,
            "day": Color.BRIGHT_YELLOW,
        }

        # Create log directory if needed
        if log_to_file:
            os.makedirs(log_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = open(f"{log_dir}/mafia_game_{timestamp}.log", "w")

    def __del__(self):
        """Close log file when logger is destroyed."""
        if self.log_file:
            self.log_file.close()

    def _write_to_file(self, text):
        """Write plain text to log file."""
        if self.log_to_file and self.log_file:
            # Remove ANSI color codes for file logging
            clean_text = text
            for color in Color:
                clean_text = clean_text.replace(color.value, "")
            self.log_file.write(clean_text + "\n")
            self.log_file.flush()

    def print(self, text, color=None, bold=False, underline=False):
        """
        Print colored text to console and log file.

        Args:
            text (str): Text to print.
            color (Color, optional): Color to use.
            bold (bool, optional): Whether to make text bold.
            underline (bool, optional): Whether to underline text.
        """
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

    def header(self, text, color=Color.CYAN):
        """Print a header with a box around it."""
        width = len(text) + 4
        border = "+" + "-" * (width - 2) + "+"

        self.print("")
        self.print(border, color, bold=True)
        self.print(f"| {text} |", color, bold=True)
        self.print(border, color, bold=True)

    def game_start(self, game_number, game_id, language):
        """Log game start."""
        self.header(
            f"GAME {game_number} (ID: {game_id} LANGUAGE: {language}) STARTED",
            Color.BRIGHT_MAGENTA,
        )

    def game_end(self, game_number, winner, rounds):
        """Log game end."""
        color = Color.RED if winner == "Mafia" else Color.GREEN
        self.header(
            f"GAME {game_number} ENDED - {winner} WIN AFTER {rounds} ROUNDS", color
        )

    def phase_header(self, phase, round_number):
        """Log phase header."""
        phase_name = phase.upper()
        color = self.phase_colors.get(phase.lower(), Color.WHITE)
        self.header(f"{phase_name} PHASE - ROUND {round_number}", color)

    def player_setup(self, player_name, role):
        """Log player setup."""
        role_color = self.role_colors.get(role, Color.WHITE)
        self.print(f"Player: {player_name}", Color.BRIGHT_WHITE, bold=True)
        self.print(f"Role: {role}", role_color, bold=True)
        self.print("-" * 40, Color.BRIGHT_BLACK)

    def player_response(self, player_name, role, response):
        """Log player response."""
        role_color = self.role_colors.get(role, Color.WHITE)

        # Format the response with indentation
        formatted_response = response.replace("\n", "\n    ")

        self.print(f"┌─ {player_name} ({role}) ", role_color, bold=True)
        self.print(f"└─ {formatted_response}", Color.WHITE)
        self.print("")

    def player_action(self, player_name, role, action):
        """Log player action."""
        role_color = self.role_colors.get(role, Color.WHITE)
        self.print(f"ACTION: {player_name} ({role}) - {action}", role_color, bold=True)

    def event(self, text, color=Color.YELLOW):
        """Log game event."""
        self.print(f"EVENT: {text}", color, bold=True)

    def error(self, text):
        """Log error."""
        self.print(f"ERROR: {text}", Color.BRIGHT_RED, bold=True)

    def log_model_issue(self, model_name, issue_type, details):
        """
        Log model-specific issues to help with debugging.

        Args:
            model_name (str): The name of the model having issues.
            issue_type (str): Type of issue (e.g., "timeout", "empty_response", "invalid_format").
            details (str): Additional details about the issue.
        """
        # Create a timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # Format the log message
        log_message = (
            f"[{timestamp}] MODEL ISSUE: {model_name} - {issue_type} - {details}"
        )

        # Print to console
        self.print(log_message, Color.BRIGHT_YELLOW, bold=True)

        # Also log to a model-specific log file
        model_short_name = model_name.split("/")[-1].replace(":", "_")
        log_dir = "logs/model_issues"
        os.makedirs(log_dir, exist_ok=True)

        log_file = f"{log_dir}/{model_short_name}_issues.log"
        with open(log_file, "a") as f:
            f.write(f"{log_message}\n")

    def stats(self, stats_dict):
        """Log game statistics."""
        self.header("SIMULATION STATISTICS", Color.BRIGHT_CYAN)

        for key, value in stats_dict.items():
            if key == "model_stats":
                continue
            if isinstance(value, float):
                self.print(f"{key}: {value:.2f}", Color.BRIGHT_WHITE)
            else:
                self.print(f"{key}: {value}", Color.BRIGHT_WHITE)

        if "model_stats" in stats_dict:
            self.header("MODEL STATISTICS", Color.BRIGHT_CYAN)

            for model, model_stats in stats_dict["model_stats"].items():
                self.print(f"\n{model}:", Color.BRIGHT_MAGENTA, bold=True)

                for stat_key, stat_value in model_stats.items():
                    if isinstance(stat_value, float):
                        self.print(
                            f"  {stat_key}: {stat_value:.2f}", Color.BRIGHT_WHITE
                        )
                    else:
                        self.print(f"  {stat_key}: {stat_value}", Color.BRIGHT_WHITE)
