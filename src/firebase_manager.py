"""Database manager backed by PostgreSQL (Neon-compatible)."""

from __future__ import annotations

import json
import os
import sys
import time
from collections import defaultdict
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.rows import dict_row

try:
    import src.config as config
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import config


class FirebaseManager:
    """Backward-compatible data access layer now powered by PostgreSQL."""

    def __init__(self):
        self.database_url = getattr(config, "DATABASE_URL", "")
        self.initialized = bool(self.database_url)

        if not self.initialized:
            print("DATABASE_URL is not configured. Database features are disabled.")
            return

        try:
            self._ensure_schema()
            print("PostgreSQL initialized successfully.")
        except psycopg.Error as exc:
            print(f"Error initializing PostgreSQL: {exc}")
            self.initialized = False

    @contextmanager
    def _connection(self):
        conn = psycopg.connect(self.database_url, row_factory=dict_row)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS mafia_games (
                        game_id TEXT PRIMARY KEY,
                        timestamp BIGINT NOT NULL,
                        game_type TEXT NOT NULL,
                        language TEXT NOT NULL,
                        participant_count INTEGER NOT NULL,
                        winner TEXT NOT NULL,
                        participants JSONB NOT NULL
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS game_logs (
                        game_id TEXT PRIMARY KEY REFERENCES mafia_games(game_id) ON DELETE CASCADE,
                        timestamp BIGINT NOT NULL,
                        game_type TEXT NOT NULL,
                        language TEXT NOT NULL,
                        participant_count INTEGER NOT NULL,
                        rounds JSONB NOT NULL,
                        critic_review JSONB
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_mafia_games_timestamp
                    ON mafia_games(timestamp DESC);
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_mafia_games_game_type
                    ON mafia_games(game_type);
                    """
                )

    def _normalize_participants(self, participants: dict[str, Any]) -> list[dict[str, Any]]:
        normalized = []
        for participant_key, data in (participants or {}).items():
            if isinstance(data, dict):
                normalized.append(
                    {
                        "player_name": data.get("player_name") or participant_key,
                        "model_name": data.get("model_name") or participant_key,
                        "role": data.get("role"),
                    }
                )
            else:
                normalized.append(
                    {
                        "player_name": participant_key,
                        "model_name": participant_key,
                        "role": data,
                    }
                )
        return normalized

    def _did_model_win(self, role: str | None, winner: str | None) -> bool:
        if role == "Mafia":
            return winner == "Mafia"
        if role in {"Villager", "Doctor"}:
            return winner == "Villagers"
        return False

    def _validate_participants(self, participants: Any) -> dict[str, Any]:
        if not isinstance(participants, dict):
            raise TypeError("participants must be a dictionary keyed by player name")
        return participants

    def _validate_rounds(self, rounds: Any) -> list[Any]:
        if not isinstance(rounds, list):
            raise TypeError("rounds must be a list")
        return rounds

    def store_game_result(self, game_id, winner, participants, game_type=config.GAME_TYPE, language=config.LANGUAGE):
        if not self.initialized:
            print("Database not initialized. Cannot store game result.")
            return False

        try:
            validated_participants = self._validate_participants(participants)
            with self._connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO mafia_games (game_id, timestamp, game_type, language, participant_count, winner, participants)
                        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                        ON CONFLICT (game_id) DO UPDATE SET
                            timestamp = EXCLUDED.timestamp,
                            game_type = EXCLUDED.game_type,
                            language = EXCLUDED.language,
                            participant_count = EXCLUDED.participant_count,
                            winner = EXCLUDED.winner,
                            participants = EXCLUDED.participants;
                        """,
                        (
                            game_id,
                            int(time.time()),
                            game_type,
                            language,
                            len(validated_participants),
                            winner,
                            json.dumps(validated_participants),
                        ),
                    )
            return True
        except (psycopg.Error, TypeError, ValueError) as exc:
            print(f"Error storing game result: {exc}")
            return False

    def store_game_log(self, game_id, rounds, participants, game_type=config.GAME_TYPE, language=config.LANGUAGE, critic_review=None):
        if not self.initialized:
            print("Database not initialized. Cannot store game log.")
            return False

        try:
            validated_participants = self._validate_participants(participants)
            validated_rounds = self._validate_rounds(rounds)
            with self._connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO game_logs (game_id, timestamp, game_type, language, participant_count, rounds, critic_review)
                        VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
                        ON CONFLICT (game_id) DO UPDATE SET
                            timestamp = EXCLUDED.timestamp,
                            game_type = EXCLUDED.game_type,
                            language = EXCLUDED.language,
                            participant_count = EXCLUDED.participant_count,
                            rounds = EXCLUDED.rounds,
                            critic_review = EXCLUDED.critic_review;
                        """,
                        (
                            game_id,
                            int(time.time()),
                            game_type,
                            language,
                            len(validated_participants),
                            json.dumps(validated_rounds),
                            json.dumps(critic_review) if critic_review else None,
                        ),
                    )
            return True
        except (psycopg.Error, TypeError, ValueError) as exc:
            print(f"Error storing game log: {exc}")
            return False

    def get_game_results(self, limit=100):
        if not self.initialized:
            print("Database not initialized. Cannot get game results.")
            return []

        try:
            with self._connection() as conn:
                with conn.cursor() as cur:
                    if limit is None:
                        cur.execute(
                            """
                            SELECT game_id, timestamp, game_type, language, participant_count, winner, participants
                            FROM mafia_games
                            ORDER BY timestamp DESC;
                            """
                        )
                    else:
                        cur.execute(
                            """
                            SELECT game_id, timestamp, game_type, language, participant_count, winner, participants
                            FROM mafia_games
                            ORDER BY timestamp DESC
                            LIMIT %s;
                            """,
                            (limit,),
                        )
                    rows = cur.fetchall()
            for row in rows:
                if isinstance(row.get("participants"), str):
                    row["participants"] = json.loads(row["participants"])
            return rows
        except (psycopg.Error, json.JSONDecodeError, TypeError) as exc:
            print(f"Error getting game results: {exc}")
            return []

    def get_model_stats(self):
        if not self.initialized:
            print("Database not initialized. Cannot get model stats.")
            return {}

        try:
            results = self.get_game_results(limit=1000)
            stats: dict[str, dict[str, Any]] = {}

            for game in results:
                winner = game.get("winner")
                participants = game.get("participants", {})

                for player_name, data in participants.items():
                    if isinstance(data, dict):
                        role = data.get("role")
                        model = data.get("model_name", player_name)
                    else:
                        role = data
                        model = player_name

                    if model not in stats:
                        stats[model] = {
                            "games_played": 0,
                            "games_won": 0,
                            "mafia_games": 0,
                            "mafia_wins": 0,
                            "villager_games": 0,
                            "villager_wins": 0,
                            "doctor_games": 0,
                            "doctor_wins": 0,
                        }

                    stats[model]["games_played"] += 1

                    if role == "Mafia":
                        stats[model]["mafia_games"] += 1
                        if winner == "Mafia":
                            stats[model]["mafia_wins"] += 1
                            stats[model]["games_won"] += 1
                    elif role == "Doctor":
                        stats[model]["doctor_games"] += 1
                        if winner == "Villagers":
                            stats[model]["doctor_wins"] += 1
                            stats[model]["games_won"] += 1
                    elif role == "Villager":
                        stats[model]["villager_games"] += 1
                        if winner == "Villagers":
                            stats[model]["villager_wins"] += 1
                            stats[model]["games_won"] += 1

            for model in stats:
                played = stats[model]["games_played"]
                mafia_games = stats[model]["mafia_games"]
                villager_games = stats[model]["villager_games"]
                doctor_games = stats[model]["doctor_games"]

                stats[model]["win_rate"] = stats[model]["games_won"] / played if played else 0
                stats[model]["mafia_win_rate"] = stats[model]["mafia_wins"] / mafia_games if mafia_games else 0
                stats[model]["villager_win_rate"] = stats[model]["villager_wins"] / villager_games if villager_games else 0
                stats[model]["doctor_win_rate"] = stats[model]["doctor_wins"] / doctor_games if doctor_games else 0

            return stats
        except (psycopg.Error, TypeError, ValueError) as exc:
            print(f"Error getting model stats: {exc}")
            return {}

    def get_model_analytics(self, model_name: str):
        if not self.initialized:
            print("Database not initialized. Cannot get model analytics.")
            return None

        try:
            results = sorted(
                self.get_game_results(limit=None),
                key=lambda game: (game.get("timestamp", 0), game.get("game_id", "")),
            )

            appearances = []
            opponent_stats: dict[str, dict[str, Any]] = defaultdict(
                lambda: {"games": 0, "wins": 0, "losses": 0}
            )
            role_stats = {
                "Mafia": {"games": 0, "wins": 0},
                "Villager": {"games": 0, "wins": 0},
                "Doctor": {"games": 0, "wins": 0},
            }
            language_stats: dict[str, dict[str, int]] = defaultdict(
                lambda: {"games": 0, "wins": 0}
            )
            lobby_size_stats: dict[str, dict[str, int]] = defaultdict(
                lambda: {"games": 0, "wins": 0}
            )

            total_games = 0
            total_wins = 0
            current_win_streak = 0
            current_loss_streak = 0
            best_win_streak = 0
            worst_loss_streak = 0

            for game in results:
                participants = self._normalize_participants(game.get("participants", {}))
                matching = [
                    participant
                    for participant in participants
                    if participant["model_name"] == model_name
                ]

                if not matching:
                    continue

                for participant in matching:
                    role = participant.get("role")
                    won = self._did_model_win(role, game.get("winner"))
                    total_games += 1
                    total_wins += int(won)

                    if won:
                        current_win_streak += 1
                        current_loss_streak = 0
                    else:
                        current_loss_streak += 1
                        current_win_streak = 0

                    best_win_streak = max(best_win_streak, current_win_streak)
                    worst_loss_streak = max(worst_loss_streak, current_loss_streak)

                    if role in role_stats:
                        role_stats[role]["games"] += 1
                        role_stats[role]["wins"] += int(won)

                    language = game.get("language") or "Unknown"
                    language_stats[language]["games"] += 1
                    language_stats[language]["wins"] += int(won)

                    lobby_key = str(game.get("participant_count") or 0)
                    lobby_size_stats[lobby_key]["games"] += 1
                    lobby_size_stats[lobby_key]["wins"] += int(won)

                    if role == "Mafia":
                        opponents = [
                            other for other in participants if other.get("role") != "Mafia"
                        ]
                        allies = [
                            other
                            for other in participants
                            if other.get("role") == "Mafia"
                            and other.get("model_name") != model_name
                        ]
                    else:
                        opponents = [
                            other for other in participants if other.get("role") == "Mafia"
                        ]
                        allies = [
                            other
                            for other in participants
                            if other.get("role") != "Mafia"
                            and other.get("model_name") != model_name
                        ]

                    for opponent in opponents:
                        matchup = opponent_stats[opponent["model_name"]]
                        matchup["games"] += 1
                        if won:
                            matchup["wins"] += 1
                        else:
                            matchup["losses"] += 1

                    appearances.append(
                        {
                            "game_id": game.get("game_id"),
                            "timestamp": game.get("timestamp"),
                            "game_type": game.get("game_type"),
                            "language": language,
                            "participant_count": game.get("participant_count"),
                            "winner": game.get("winner"),
                            "player_name": participant.get("player_name"),
                            "role": role,
                            "result": "win" if won else "loss",
                            "opponents": [
                                {
                                    "model_name": opponent.get("model_name"),
                                    "player_name": opponent.get("player_name"),
                                    "role": opponent.get("role"),
                                }
                                for opponent in opponents
                            ],
                            "allies": [
                                {
                                    "model_name": ally.get("model_name"),
                                    "player_name": ally.get("player_name"),
                                    "role": ally.get("role"),
                                }
                                for ally in allies
                            ],
                        }
                    )

            if not appearances:
                return None

            timeline = []
            cumulative_games = 0
            cumulative_wins = 0
            for appearance in appearances:
                cumulative_games += 1
                if appearance["result"] == "win":
                    cumulative_wins += 1

                timeline.append(
                    {
                        "game_id": appearance["game_id"],
                        "timestamp": appearance["timestamp"],
                        "result": appearance["result"],
                        "role": appearance["role"],
                        "cumulative_win_rate": (
                            cumulative_wins / cumulative_games if cumulative_games else 0
                        ),
                    }
                )

            matchup_breakdown = []
            for opponent_model, stats in opponent_stats.items():
                games = stats["games"]
                wins = stats["wins"]
                losses = stats["losses"]
                matchup_breakdown.append(
                    {
                        "model_name": opponent_model,
                        "games": games,
                        "wins": wins,
                        "losses": losses,
                        "win_rate": wins / games if games else 0,
                    }
                )

            matchup_breakdown.sort(
                key=lambda item: (item["games"], item["wins"], item["win_rate"]),
                reverse=True,
            )

            role_breakdown = {}
            for role_name, stats in role_stats.items():
                games = stats["games"]
                wins = stats["wins"]
                role_breakdown[role_name] = {
                    "games": games,
                    "wins": wins,
                    "losses": games - wins,
                    "win_rate": wins / games if games else 0,
                }

            language_breakdown = [
                {
                    "language": language,
                    "games": stats["games"],
                    "wins": stats["wins"],
                    "losses": stats["games"] - stats["wins"],
                    "win_rate": stats["wins"] / stats["games"] if stats["games"] else 0,
                }
                for language, stats in sorted(
                    language_stats.items(),
                    key=lambda item: item[1]["games"],
                    reverse=True,
                )
            ]

            lobby_breakdown = [
                {
                    "participant_count": int(participant_count),
                    "games": stats["games"],
                    "wins": stats["wins"],
                    "losses": stats["games"] - stats["wins"],
                    "win_rate": stats["wins"] / stats["games"] if stats["games"] else 0,
                }
                for participant_count, stats in sorted(
                    lobby_size_stats.items(),
                    key=lambda item: int(item[0]),
                )
            ]

            won_most_against = sorted(
                matchup_breakdown,
                key=lambda item: (item["wins"], item["games"], item["win_rate"]),
                reverse=True,
            )[:5]
            lost_most_against = sorted(
                matchup_breakdown,
                key=lambda item: (item["losses"], item["games"], 1 - item["win_rate"]),
                reverse=True,
            )[:5]
            best_matchups = [
                item
                for item in sorted(
                    matchup_breakdown,
                    key=lambda item: (item["win_rate"], item["games"]),
                    reverse=True,
                )
                if item["games"] >= 2
            ][:5]
            toughest_matchups = [
                item
                for item in sorted(
                    matchup_breakdown,
                    key=lambda item: (item["win_rate"], -item["games"]),
                )
                if item["games"] >= 2
            ][:5]

            recent_games = sorted(
                appearances,
                key=lambda appearance: (
                    appearance.get("timestamp", 0),
                    appearance.get("game_id", ""),
                ),
                reverse=True,
            )[:20]

            return {
                "model_name": model_name,
                "games_played": total_games,
                "games_won": total_wins,
                "games_lost": total_games - total_wins,
                "win_rate": total_wins / total_games if total_games else 0,
                "current_win_streak": current_win_streak,
                "current_loss_streak": current_loss_streak,
                "best_win_streak": best_win_streak,
                "worst_loss_streak": worst_loss_streak,
                "role_breakdown": role_breakdown,
                "language_breakdown": language_breakdown,
                "lobby_breakdown": lobby_breakdown,
                "timeline": timeline,
                "recent_games": recent_games,
                "matchups": matchup_breakdown,
                "won_most_against": won_most_against,
                "lost_most_against": lost_most_against,
                "best_matchups": best_matchups,
                "toughest_matchups": toughest_matchups,
            }
        except (psycopg.Error, TypeError, ValueError) as exc:
            print(f"Error getting model analytics: {exc}")
            return None

    def get_game_log(self, game_id):
        if not self.initialized:
            print("Database not initialized. Cannot get game log.")
            return None

        try:
            with self._connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT gl.game_id, gl.timestamp, gl.game_type, gl.language, gl.participant_count,
                               gl.rounds, gl.critic_review, mg.participants, mg.winner
                        FROM game_logs gl
                        JOIN mafia_games mg ON mg.game_id = gl.game_id
                        WHERE gl.game_id = %s;
                        """,
                        (game_id,),
                    )
                    row = cur.fetchone()

            if not row:
                print(f"Game log not found for game ID: {game_id}")
                return None

            return row
        except psycopg.Error as exc:
            print(f"Error getting game log: {exc}")
            return None
