import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import firebase_manager as firebase_manager_module
from firebase_manager import FirebaseManager


class FirebaseManagerTests(unittest.TestCase):
    def make_manager(self):
        with patch.object(firebase_manager_module.config, "DATABASE_URL", ""):
            return FirebaseManager()

    def test_store_game_result_rejects_non_dict_participants(self):
        manager = self.make_manager()
        manager.initialized = True

        result = manager.store_game_result("game-1", "Villagers", ["bad-payload"])

        self.assertFalse(result)

    def test_store_game_log_rejects_non_list_rounds(self):
        manager = self.make_manager()
        manager.initialized = True

        result = manager.store_game_log(
            "game-1",
            {"round": 1},
            {"Alice": {"model_name": "openai/gpt-5.4", "role": "Villager"}},
        )

        self.assertFalse(result)

    def test_get_model_stats_supports_legacy_and_object_participants(self):
        manager = self.make_manager()
        manager.initialized = True
        fake_results = [
            {
                "winner": "Villagers",
                "participants": {
                    "Alice": {
                        "model_name": "openai/gpt-5.4",
                        "role": "Villager",
                    },
                    "Bob": {
                        "model_name": "anthropic/claude-sonnet-4.6",
                        "role": "Mafia",
                    },
                },
            },
            {
                "winner": "Mafia",
                "participants": {
                    "openai/gpt-5.4": "Doctor",
                    "anthropic/claude-sonnet-4.6": "Mafia",
                },
            },
        ]

        with patch.object(manager, "get_game_results", return_value=fake_results):
            stats = manager.get_model_stats()

        self.assertEqual(stats["openai/gpt-5.4"]["games_played"], 2)
        self.assertEqual(stats["openai/gpt-5.4"]["games_won"], 1)
        self.assertEqual(stats["openai/gpt-5.4"]["villager_games"], 1)
        self.assertEqual(stats["openai/gpt-5.4"]["doctor_games"], 1)
        self.assertEqual(stats["anthropic/claude-sonnet-4.6"]["mafia_wins"], 1)
        self.assertAlmostEqual(stats["anthropic/claude-sonnet-4.6"]["win_rate"], 0.5)

    def test_get_model_analytics_returns_timeline_and_matchups(self):
        manager = self.make_manager()
        manager.initialized = True
        fake_results = [
            {
                "game_id": "game-1",
                "timestamp": 100,
                "game_type": "Classic Mafia",
                "language": "English",
                "participant_count": 3,
                "winner": "Villagers",
                "participants": {
                    "Alice": {
                        "player_name": "Alice",
                        "model_name": "openai/gpt-5.4",
                        "role": "Villager",
                    },
                    "Bob": {
                        "player_name": "Bob",
                        "model_name": "anthropic/claude-sonnet-4.6",
                        "role": "Mafia",
                    },
                    "Cara": {
                        "player_name": "Cara",
                        "model_name": "google/gemini-3.1-pro-preview",
                        "role": "Doctor",
                    },
                },
            },
            {
                "game_id": "game-2",
                "timestamp": 200,
                "game_type": "Classic Mafia",
                "language": "English",
                "participant_count": 3,
                "winner": "Mafia",
                "participants": {
                    "Alice": {
                        "player_name": "Alice",
                        "model_name": "openai/gpt-5.4",
                        "role": "Villager",
                    },
                    "Bob": {
                        "player_name": "Bob",
                        "model_name": "anthropic/claude-sonnet-4.6",
                        "role": "Mafia",
                    },
                    "Cara": {
                        "player_name": "Cara",
                        "model_name": "google/gemini-3.1-pro-preview",
                        "role": "Doctor",
                    },
                },
            },
        ]

        with patch.object(manager, "get_game_results", return_value=fake_results):
            analytics = manager.get_model_analytics("openai/gpt-5.4")

        self.assertIsNotNone(analytics)
        self.assertEqual(analytics["games_played"], 2)
        self.assertEqual(analytics["games_won"], 1)
        self.assertEqual(len(analytics["timeline"]), 2)
        self.assertEqual(analytics["timeline"][0]["cumulative_win_rate"], 1.0)
        self.assertEqual(analytics["timeline"][1]["cumulative_win_rate"], 0.5)
        self.assertEqual(analytics["lost_most_against"][0]["model_name"], "anthropic/claude-sonnet-4.6")


if __name__ == "__main__":
    unittest.main()
