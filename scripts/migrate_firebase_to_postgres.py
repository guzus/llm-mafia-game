"""Migrate LLM Mafia data from Firestore to PostgreSQL."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import src.config as config

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError as exc:  # pragma: no cover - handled at runtime
    raise SystemExit(
        "firebase-admin is required for this migration. "
        "Run with: uv run --with firebase-admin scripts/migrate_firebase_to_postgres.py"
    ) from exc


@dataclass
class MigrationStats:
    mafia_games_seen: int = 0
    mafia_games_imported: int = 0
    game_logs_seen: int = 0
    game_logs_imported: int = 0
    skipped_logs_missing_game: int = 0
    orphaned_logs_archived: int = 0


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate Firestore data to PostgreSQL")
    parser.add_argument(
        "--firebase-credentials",
        default=os.getenv("FIREBASE_CREDENTIALS_PATH", str(ROOT / "firebase_credentials.json")),
        help="Path to the Firebase service account JSON",
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", getattr(config, "DATABASE_URL", "")),
        help="PostgreSQL connection URL",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read and validate source data without writing to PostgreSQL",
    )
    return parser.parse_args()


def init_firestore(credentials_path: str):
    if not Path(credentials_path).exists():
        raise FileNotFoundError(f"Firebase credentials not found: {credentials_path}")

    if not firebase_admin._apps:
        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred)

    return firestore.client()


def connect_postgres(database_url: str):
    if not database_url:
        raise ValueError("DATABASE_URL is required")
    return psycopg.connect(database_url, row_factory=dict_row)


def ensure_schema(conn: psycopg.Connection) -> None:
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
            CREATE TABLE IF NOT EXISTS firestore_orphaned_game_logs (
                game_id TEXT PRIMARY KEY,
                timestamp BIGINT NOT NULL,
                game_type TEXT NOT NULL,
                language TEXT NOT NULL,
                participant_count INTEGER NOT NULL,
                participants JSONB,
                rounds JSONB NOT NULL,
                critic_review JSONB,
                raw_payload JSONB NOT NULL,
                migrated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )


def normalize_mafia_game(doc_id: str, data: dict[str, Any]) -> dict[str, Any]:
    participants = data.get("participants") or {}
    game_id = data.get("game_id") or doc_id
    return {
        "game_id": game_id,
        "timestamp": int(data.get("timestamp") or 0),
        "game_type": data.get("game_type") or getattr(config, "GAME_TYPE", "Classic Mafia"),
        "language": data.get("language") or "English",
        "participant_count": int(data.get("participant_count") or len(participants)),
        "winner": data.get("winner") or "Unknown",
        "participants": participants,
    }


def normalize_game_log(doc_id: str, data: dict[str, Any], game_row: dict[str, Any] | None) -> dict[str, Any]:
    game_id = data.get("game_id") or doc_id
    participants = (game_row or {}).get("participants") or {}
    participant_count = data.get("participant_count")
    if participant_count is None:
        participant_count = (game_row or {}).get("participant_count") or len(participants)

    return {
        "game_id": game_id,
        "timestamp": int(data.get("timestamp") or (game_row or {}).get("timestamp") or 0),
        "game_type": data.get("game_type") or (game_row or {}).get("game_type") or getattr(config, "GAME_TYPE", "Classic Mafia"),
        "language": data.get("language") or (game_row or {}).get("language") or "English",
        "participant_count": int(participant_count or 0),
        "rounds": data.get("rounds") or [],
        "critic_review": data.get("critic_review"),
    }


def load_firestore_collection(client, collection_name: str) -> dict[str, dict[str, Any]]:
    docs: dict[str, dict[str, Any]] = {}
    for doc in client.collection(collection_name).stream():
        docs[doc.id] = doc.to_dict() or {}
    return docs


def upsert_mafia_games(conn: psycopg.Connection, games: dict[str, dict[str, Any]], stats: MigrationStats, dry_run: bool) -> dict[str, dict[str, Any]]:
    normalized_games: dict[str, dict[str, Any]] = {}
    with conn.cursor() as cur:
        for doc_id, game_data in games.items():
            stats.mafia_games_seen += 1
            normalized = normalize_mafia_game(doc_id, game_data)
            normalized_games[normalized["game_id"]] = normalized

            if dry_run:
                continue

            cur.execute(
                """
                INSERT INTO mafia_games (
                    game_id, timestamp, game_type, language, participant_count, winner, participants
                )
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
                    normalized["game_id"],
                    normalized["timestamp"],
                    normalized["game_type"],
                    normalized["language"],
                    normalized["participant_count"],
                    normalized["winner"],
                    json.dumps(normalized["participants"]),
                ),
            )
            stats.mafia_games_imported += 1

    if dry_run:
        stats.mafia_games_imported = stats.mafia_games_seen

    return normalized_games


def upsert_game_logs(
    conn: psycopg.Connection,
    logs: dict[str, dict[str, Any]],
    games_by_id: dict[str, dict[str, Any]],
    stats: MigrationStats,
    dry_run: bool,
) -> None:
    with conn.cursor() as cur:
        for doc_id, log_data in logs.items():
            stats.game_logs_seen += 1
            game_id = log_data.get("game_id") or doc_id
            game_row = games_by_id.get(game_id)

            if not game_row:
                stats.skipped_logs_missing_game += 1
                archive_orphaned_log(cur, doc_id, log_data, stats, dry_run)
                continue

            normalized = normalize_game_log(doc_id, log_data, game_row)

            if dry_run:
                continue

            cur.execute(
                """
                INSERT INTO game_logs (
                    game_id, timestamp, game_type, language, participant_count, rounds, critic_review
                )
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
                    normalized["game_id"],
                    normalized["timestamp"],
                    normalized["game_type"],
                    normalized["language"],
                    normalized["participant_count"],
                    json.dumps(normalized["rounds"]),
                    json.dumps(normalized["critic_review"]) if normalized["critic_review"] is not None else None,
                ),
            )
            stats.game_logs_imported += 1

    if dry_run:
        stats.game_logs_imported = stats.game_logs_seen - stats.skipped_logs_missing_game


def archive_orphaned_log(
    cur,
    doc_id: str,
    log_data: dict[str, Any],
    stats: MigrationStats,
    dry_run: bool,
) -> None:
    participants = log_data.get("participants")
    participant_count = log_data.get("participant_count")
    if participant_count is None and isinstance(participants, dict):
        participant_count = len(participants)

    if dry_run:
        stats.orphaned_logs_archived += 1
        return

    cur.execute(
        """
        INSERT INTO firestore_orphaned_game_logs (
            game_id, timestamp, game_type, language, participant_count,
            participants, rounds, critic_review, raw_payload
        )
        VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb)
        ON CONFLICT (game_id) DO UPDATE SET
            timestamp = EXCLUDED.timestamp,
            game_type = EXCLUDED.game_type,
            language = EXCLUDED.language,
            participant_count = EXCLUDED.participant_count,
            participants = EXCLUDED.participants,
            rounds = EXCLUDED.rounds,
            critic_review = EXCLUDED.critic_review,
            raw_payload = EXCLUDED.raw_payload,
            migrated_at = NOW();
        """,
        (
            log_data.get("game_id") or doc_id,
            int(log_data.get("timestamp") or 0),
            log_data.get("game_type") or getattr(config, "GAME_TYPE", "Classic Mafia"),
            log_data.get("language") or "English",
            int(participant_count or 0),
            json.dumps(participants) if participants is not None else None,
            json.dumps(log_data.get("rounds") or []),
            json.dumps(log_data.get("critic_review")) if log_data.get("critic_review") is not None else None,
            json.dumps(log_data),
        ),
    )
    stats.orphaned_logs_archived += 1


def fetch_target_counts(conn: psycopg.Connection) -> dict[str, int]:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS count FROM mafia_games;")
        mafia_games = cur.fetchone()["count"]
        cur.execute("SELECT COUNT(*) AS count FROM game_logs;")
        game_logs = cur.fetchone()["count"]
        cur.execute("SELECT COUNT(*) AS count FROM firestore_orphaned_game_logs;")
        orphaned_game_logs = cur.fetchone()["count"]
    return {
        "mafia_games": mafia_games,
        "game_logs": game_logs,
        "firestore_orphaned_game_logs": orphaned_game_logs,
    }


def main() -> int:
    args = get_args()
    stats = MigrationStats()

    firestore_client = init_firestore(args.firebase_credentials)
    conn = connect_postgres(args.database_url)

    try:
        ensure_schema(conn)
        source_games = load_firestore_collection(firestore_client, "mafia_games")
        source_logs = load_firestore_collection(firestore_client, "game_logs")

        print(
            f"Loaded Firestore collections: mafia_games={len(source_games)}, game_logs={len(source_logs)}"
        )

        games_by_id = upsert_mafia_games(conn, source_games, stats, args.dry_run)
        upsert_game_logs(conn, source_logs, games_by_id, stats, args.dry_run)

        if args.dry_run:
            conn.rollback()
            print("Dry run completed. No PostgreSQL changes were written.")
        else:
            conn.commit()

        print(
            "Migration summary: "
            f"mafia_games imported={stats.mafia_games_imported}/{stats.mafia_games_seen}, "
            f"game_logs imported={stats.game_logs_imported}/{stats.game_logs_seen}, "
            f"skipped_logs_missing_game={stats.skipped_logs_missing_game}, "
            f"orphaned_logs_archived={stats.orphaned_logs_archived}"
        )

        if not args.dry_run:
            target_counts = fetch_target_counts(conn)
            print(
                "Target counts after import: "
                f"mafia_games={target_counts['mafia_games']}, "
                f"game_logs={target_counts['game_logs']}, "
                f"firestore_orphaned_game_logs={target_counts['firestore_orphaned_game_logs']}"
            )

        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
