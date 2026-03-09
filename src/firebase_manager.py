"""Database manager backed by PostgreSQL (Neon-compatible)."""

from __future__ import annotations

import json
import os
import sys
import time
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
        except Exception as exc:
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

    def store_game_result(self, game_id, winner, participants, game_type=config.GAME_TYPE, language=config.LANGUAGE):
        if not self.initialized:
            print("Database not initialized. Cannot store game result.")
            return False

        try:
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
                            len(participants),
                            winner,
                            json.dumps(participants),
                        ),
                    )
            return True
        except Exception as exc:
            print(f"Error storing game result: {exc}")
            return False

    def store_game_log(self, game_id, rounds, participants, game_type=config.GAME_TYPE, language=config.LANGUAGE, critic_review=None):
        if not self.initialized:
            print("Database not initialized. Cannot store game log.")
            return False

        try:
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
                            len(participants),
                            json.dumps(rounds),
                            json.dumps(critic_review) if critic_review else None,
                        ),
                    )
            return True
        except Exception as exc:
            print(f"Error storing game log: {exc}")
            return False

    def get_game_results(self, limit=100):
        if not self.initialized:
            print("Database not initialized. Cannot get game results.")
            return []

        try:
            with self._connection() as conn:
                with conn.cursor() as cur:
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
        except Exception as exc:
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
        except Exception as exc:
            print(f"Error getting model stats: {exc}")
            return {}

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
        except Exception as exc:
            print(f"Error getting game log: {exc}")
            return None
