"""
Dashboard for the LLM Mafia Game Competition.
"""

import io
import base64
import json
import os
import time
import datetime
import copy
import threading
import traceback
import uuid
from functools import wraps
from hmac import compare_digest
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import matplotlib

matplotlib.use("Agg")  # Use Agg backend for non-interactive mode
import matplotlib.pyplot as plt
import numpy as np
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    Response,
    make_response,
    redirect,
    session,
    url_for,
)
import config
from firebase_manager import FirebaseManager
from flask_caching import Cache
from openrouter import get_openrouter_account_state
from simulate import run_simulation

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = (
    os.getenv("ADMIN_SESSION_SECRET")
    or os.getenv("FLASK_SECRET_KEY")
    or os.getenv("SECRET_KEY")
    or "llm-mafia-local-admin-secret"
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = bool(os.getenv("RAILWAY_ENVIRONMENT"))
firebase = FirebaseManager()

# Configure Flask-Caching
cache_config = {
    "CACHE_TYPE": "SimpleCache",  # Simple in-memory cache
    "CACHE_DEFAULT_TIMEOUT": 30,  # Default timeout in seconds
}
cache = Cache(app, config=cache_config)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
DEFAULT_ADMIN_MODELS = [
    "openai/gpt-5.4",
    "x-ai/grok-4.1-fast",
    "google/gemini-3.1-pro-preview",
    "anthropic/claude-sonnet-4.6",
    "anthropic/claude-sonnet-4.5",
    "deepseek/deepseek-v3.2",
    "qwen/qwen3-max",
    "openai/gpt-4.1-mini",
]
ADMIN_MODEL_PRESETS = {
    "latest_frontier": DEFAULT_ADMIN_MODELS,
    "budget_mix": [
        "x-ai/grok-4.1-fast",
        "deepseek/deepseek-v3.2",
        "qwen/qwen3-max",
        "openai/gpt-4.1-mini",
        "google/gemini-2.5-flash",
        "moonshotai/kimi-k2",
        "meta-llama/llama-4-maverick",
        "mistralai/mistral-small-24b-instruct-2501",
    ],
    "free_models": config.FREE_MODELS,
}
SIMULATION_LOG_LIMIT = 200
simulation_state_lock = threading.Lock()
simulation_state = {
    "job_id": None,
    "running": False,
    "status": "idle",
    "started_at": None,
    "finished_at": None,
    "config": None,
    "result": None,
    "error": None,
    "events": [],
}


# Add template filter for formatting timestamps
@app.template_filter("strftime")
def _jinja2_filter_strftime(timestamp):
    """Convert a Unix timestamp to a formatted datetime string."""
    try:
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return "Invalid timestamp"


# Data models for type safety and validation
@dataclass
class ModelStats:
    games_played: int
    games_won: int
    win_rate: float
    mafia_games: int
    mafia_wins: int
    mafia_win_rate: float
    villager_games: int
    villager_wins: int
    villager_win_rate: float
    doctor_games: int
    doctor_wins: int
    doctor_win_rate: float


@dataclass
class GameResult:
    game_id: str
    timestamp: int
    game_type: str
    participant_count: int
    winner: str
    participants: Dict[str, str]


@dataclass
class ChartResponse:
    chart_url: str


@dataclass
class ErrorResponse:
    error: str


def is_admin_configured():
    """Return True when admin password auth is enabled."""
    return bool(ADMIN_PASSWORD)


def is_admin_authenticated():
    """Return True when the current session has passed admin auth."""
    return bool(session.get("admin_authenticated"))


def admin_required(view):
    """Require a valid admin session for HTML routes."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_admin_configured():
            return render_template(
                "404.html", message="Admin dashboard is not configured"
            ), 503
        if not is_admin_authenticated():
            return redirect(url_for("admin_dashboard"))
        return view(*args, **kwargs)

    return wrapped


def admin_api_required(view):
    """Require a valid admin session for JSON routes."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_admin_configured():
            return jsonify({"error": "Admin dashboard is not configured"}), 503
        if not is_admin_authenticated():
            return jsonify({"error": "Authentication required"}), 401
        return view(*args, **kwargs)

    return wrapped


def get_admin_presets():
    """Return model presets for the admin simulation form."""
    return {
        preset_name: {
            "label": preset_name.replace("_", " ").title(),
            "models": models,
        }
        for preset_name, models in ADMIN_MODEL_PRESETS.items()
    }


def _snapshot_simulation_state():
    """Return a copy of the current simulation job state."""
    with simulation_state_lock:
        return copy.deepcopy(simulation_state)


def _append_simulation_event(message, level="info"):
    """Append a bounded event log entry for the admin dashboard."""
    with simulation_state_lock:
        simulation_state["events"].append(
            {
                "timestamp": int(time.time()),
                "level": level,
                "message": message,
            }
        )
        simulation_state["events"] = simulation_state["events"][-SIMULATION_LOG_LIMIT:]


def _clear_dashboard_caches():
    """Clear cached dashboard payloads after new games are stored."""
    cache.clear()


def _validate_admin_models(models):
    """Validate the submitted model roster."""
    if not models:
        return "At least one model is required."

    if config.UNIQUE_MODELS and len(models) < config.PLAYERS_PER_GAME:
        return (
            f"Need at least {config.PLAYERS_PER_GAME} unique models because "
            "UNIQUE_MODELS is enabled."
        )

    return None


def _parse_simulation_request(payload):
    """Validate and normalize simulation request input."""
    if not isinstance(payload, dict):
        return None, "Invalid request payload."

    try:
        num_games = int(payload.get("num_games", 1))
        max_workers = int(payload.get("max_workers", 1))
    except (TypeError, ValueError):
        return None, "Numeric fields must be valid integers."

    if num_games < 1 or num_games > 25:
        return None, "Number of games must be between 1 and 25."

    if max_workers < 1 or max_workers > 8:
        return None, "Max workers must be between 1 and 8."

    parallel_value = payload.get("parallel", False)
    if isinstance(parallel_value, str):
        parallel = parallel_value.strip().lower() in {"1", "true", "yes", "on"}
    else:
        parallel = bool(parallel_value)
    language = (payload.get("language") or config.LANGUAGE).strip() or config.LANGUAGE

    models = [
        line.strip()
        for line in str(payload.get("models", "")).splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    validation_error = _validate_admin_models(models)
    if validation_error:
        return None, validation_error

    return {
        "num_games": num_games,
        "parallel": parallel,
        "max_workers": max_workers,
        "language": language,
        "models": models,
    }, None


def _run_admin_simulation(job_id, simulation_config):
    """Background worker that runs a simulation without blocking the request."""
    try:
        _append_simulation_event(
            "Starting background simulation with "
            f"{simulation_config['num_games']} game(s), "
            f"{len(simulation_config['models'])} model(s), "
            f"language={simulation_config['language']}.",
        )

        balance_snapshot = get_cached_openrouter_account_state()
        remaining = balance_snapshot.get("remaining_credits")
        if remaining is not None:
            _append_simulation_event(
                f"OpenRouter remaining credits: {remaining:.4f}.",
                level="info" if remaining > 0 else "warning",
            )

        result = run_simulation(
            num_games=simulation_config["num_games"],
            parallel=simulation_config["parallel"],
            max_workers=simulation_config["max_workers"],
            language=simulation_config["language"],
            models=simulation_config["models"],
            status_callback=_append_simulation_event,
        )

        latest_game = firebase.get_game_results(limit=1)
        last_game_id = latest_game[0]["game_id"] if latest_game else None

        _clear_dashboard_caches()
        cache.delete_memoized(get_cached_openrouter_account_state)

        with simulation_state_lock:
            if simulation_state["job_id"] != job_id:
                return
            simulation_state["running"] = False
            simulation_state["status"] = "completed"
            simulation_state["finished_at"] = int(time.time())
            simulation_state["result"] = {
                **result,
                "last_game_id": last_game_id,
                "models": simulation_config["models"],
            }
            simulation_state["error"] = None
        _append_simulation_event("Simulation job completed successfully.", level="success")
    except Exception as exc:
        with simulation_state_lock:
            if simulation_state["job_id"] != job_id:
                return
            simulation_state["running"] = False
            simulation_state["status"] = "failed"
            simulation_state["finished_at"] = int(time.time())
            simulation_state["error"] = {
                "message": str(exc),
                "traceback": traceback.format_exc(limit=12),
            }
        _append_simulation_event(f"Simulation job failed: {exc}", level="error")


@app.route("/")
def index():
    """Render the main dashboard page."""
    return render_template("index.html")


@app.route("/game/<game_id>")
def game_detail(game_id):
    """Render the game detail page."""
    # Get game data to pass to the template
    game_data = firebase.get_game_log(game_id)

    # If game data not found, return 404
    if not game_data:
        return render_template("404.html", message="Game not found"), 404

    return render_template("game_detail.html", game_id=game_id, game_data=game_data)


@app.route("/model/<path:model_name>")
def model_detail(model_name):
    """Render the model detail page."""
    analytics = get_cached_model_analytics(model_name)

    if not analytics:
        return render_template("404.html", message="Model not found"), 404

    return render_template("model_detail.html", model_name=model_name)


@app.route("/admin")
def admin_dashboard():
    """Render the password-gated admin dashboard."""
    if not is_admin_configured():
        return render_template(
            "404.html", message="Admin dashboard is not configured"
        ), 503

    if not is_admin_authenticated():
        return render_template("admin.html", authenticated=False, error=None)

    return render_template(
        "admin.html",
        authenticated=True,
        admin_presets=get_admin_presets(),
        default_language=config.LANGUAGE,
        default_num_games=1,
        default_max_workers=1,
        initial_simulation_state=_snapshot_simulation_state(),
        initial_openrouter_state=get_cached_openrouter_account_state(),
        players_per_game=config.PLAYERS_PER_GAME,
        unique_models=config.UNIQUE_MODELS,
        default_models="\n".join(DEFAULT_ADMIN_MODELS),
        using_fallback_secret=app.secret_key == "llm-mafia-local-admin-secret",
    )


@app.route("/admin/login", methods=["POST"])
def admin_login():
    """Authenticate an admin session."""
    if not is_admin_configured():
        return render_template(
            "404.html", message="Admin dashboard is not configured"
        ), 503

    submitted_password = request.form.get("password", "")
    if compare_digest(submitted_password, ADMIN_PASSWORD):
        session["admin_authenticated"] = True
        session["admin_authenticated_at"] = int(time.time())
        return redirect(url_for("admin_dashboard"))

    return render_template("admin.html", authenticated=False, error="Invalid password"), 401


@app.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    """Clear the admin session."""
    session.clear()
    return redirect(url_for("admin_dashboard"))


@app.route("/api/stats")
def get_stats():
    """Get statistics from the database."""
    stats = get_cached_model_stats()

    # Set cache control headers for better performance
    response = make_response(jsonify(stats))
    response.headers["Content-Type"] = "application/json"
    response.headers["Cache-Control"] = "max-age=60"  # Cache for 60 seconds

    return response


@app.route("/api/model/<path:model_name>")
def get_model(model_name):
    """Get analytics for a single model."""
    analytics = get_cached_model_analytics(model_name)

    if not analytics:
        return jsonify({"error": "Model not found"}), 404

    response = make_response(jsonify(analytics))
    response.headers["Content-Type"] = "application/json"
    response.headers["Cache-Control"] = "max-age=60"
    return response


@cache.cached(timeout=30, key_prefix="model_stats")
def get_cached_model_stats():
    """Get cached model statistics from the database."""
    return firebase.get_model_stats()


@cache.memoize(timeout=60)
def get_cached_model_analytics(model_name):
    """Get cached analytics for a specific model."""
    return firebase.get_model_analytics(model_name)


@cache.memoize(timeout=15)
def get_cached_openrouter_account_state():
    """Get a short-lived cached view of OpenRouter account state."""
    return get_openrouter_account_state()


@app.route("/api/admin/overview")
@admin_api_required
def get_admin_overview():
    """Return OpenRouter balance and simulation state for the admin dashboard."""
    response = make_response(
        jsonify(
            {
                "openrouter": get_cached_openrouter_account_state(),
                "simulation": _snapshot_simulation_state(),
            }
        )
    )
    response.headers["Content-Type"] = "application/json"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/api/admin/openrouter/refresh", methods=["POST"])
@admin_api_required
def refresh_admin_openrouter_state():
    """Force-refresh the cached OpenRouter balance payload."""
    cache.delete_memoized(get_cached_openrouter_account_state)
    response = make_response(jsonify(get_cached_openrouter_account_state()))
    response.headers["Content-Type"] = "application/json"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/api/admin/simulations", methods=["POST"])
@admin_api_required
def start_admin_simulation():
    """Start a background simulation job."""
    payload = request.get_json(silent=True) or request.form.to_dict()
    simulation_config, error = _parse_simulation_request(payload)
    if error:
        return jsonify({"error": error}), 400

    with simulation_state_lock:
        if simulation_state["running"]:
            return (
                jsonify(
                    {
                        "error": "A simulation is already running.",
                        "simulation": copy.deepcopy(simulation_state),
                    }
                ),
                409,
            )

        job_id = str(uuid.uuid4())
        simulation_state["job_id"] = job_id
        simulation_state["running"] = True
        simulation_state["status"] = "running"
        simulation_state["started_at"] = int(time.time())
        simulation_state["finished_at"] = None
        simulation_state["config"] = simulation_config
        simulation_state["result"] = None
        simulation_state["error"] = None
        simulation_state["events"] = []

    _append_simulation_event("Simulation job queued from the admin dashboard.")
    worker = threading.Thread(
        target=_run_admin_simulation,
        args=(job_id, simulation_config),
        daemon=True,
    )
    worker.start()

    response = make_response(
        jsonify(
            {
                "ok": True,
                "job_id": job_id,
                "simulation": _snapshot_simulation_state(),
            }
        ),
        202,
    )
    response.headers["Content-Type"] = "application/json"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/api/games")
def get_games():
    """Get game results from the database."""
    try:
        limit = request.args.get("limit", default=100, type=int)
        if limit < 1 or limit > 1000:
            return make_response(
                jsonify({"error": "Limit must be between 1 and 1000"}), 400
            )

        games = get_cached_game_results(limit)

        # Validate timestamp format
        for game in games:
            if "timestamp" in game and isinstance(game["timestamp"], int):
                # Ensure timestamp is in seconds, not milliseconds
                if game["timestamp"] > 10000000000:  # If in milliseconds
                    game["timestamp"] = game["timestamp"] // 1000

        response = make_response(jsonify(games))
        response.headers["Content-Type"] = "application/json"
        response.headers["Cache-Control"] = "max-age=10"  # Cache for 10 seconds

        return response
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


@cache.memoize(timeout=30)
def get_cached_game_results(limit):
    """Get cached game results from the database.

    Args:
        limit (int): Maximum number of results to retrieve.

    Returns:
        list: List of game results.
    """
    return firebase.get_game_results(limit=limit)


@app.route("/api/game/<game_id>")
def get_game(game_id):
    """Get game data from the database."""
    game_data = get_cached_game_log(game_id)

    if not game_data:
        return jsonify({"error": "Game not found"}), 404

    # Set cache control headers for better performance
    response = make_response(jsonify(game_data))
    response.headers["Content-Type"] = "application/json"
    response.headers["Cache-Control"] = "max-age=120"  # Cache for 120 seconds

    return response


@cache.memoize(timeout=120)
def get_cached_game_log(game_id):
    """Get cached game log data from the database.

    Args:
        game_id (str): The ID of the game to retrieve.

    Returns:
        dict: Game log data or None if not found.
    """
    return firebase.get_game_log(game_id)


@app.route("/api/chart/win_rates")
def get_win_rate_chart():
    """Generate a win rate chart."""
    try:
        stats = get_cached_model_stats()

        if not stats:
            return make_response(jsonify({"error": "No data available"}), 404)

        # Sort models by overall win rate
        sorted_models = sorted(
            stats.items(), key=lambda x: x[1]["win_rate"], reverse=True
        )

        # Extract data for chart
        models = [model for model, _ in sorted_models]
        win_rates = [stats[model]["win_rate"] * 100 for model in models]
        mafia_win_rates = [stats[model]["mafia_win_rate"] * 100 for model in models]
        villager_win_rates = [
            stats[model]["villager_win_rate"] * 100 for model in models
        ]
        doctor_win_rates = [stats[model]["doctor_win_rate"] * 100 for model in models]

        # Create chart with explicit figure and axes
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.set_facecolor("white")  # Set white background
        ax.set_facecolor("white")  # Set white background for plot area

        # Set width of bars
        bar_width = 0.2

        # Set position of bars on x axis
        r1 = np.arange(len(models))
        r2 = [x + bar_width for x in r1]
        r3 = [x + bar_width for x in r2]
        r4 = [x + bar_width for x in r3]

        # Create bars
        ax.bar(r1, win_rates, width=bar_width, label="Overall", color="blue")
        ax.bar(r2, mafia_win_rates, width=bar_width, label="Mafia", color="red")
        ax.bar(r3, villager_win_rates, width=bar_width, label="Villager", color="green")
        ax.bar(r4, doctor_win_rates, width=bar_width, label="Doctor", color="purple")

        # Add labels and title
        ax.set_xlabel("Models", fontsize=12, fontweight="bold")
        ax.set_ylabel("Win Rate (%)", fontsize=12, fontweight="bold")
        ax.set_title("Win Rates by Model and Role", fontsize=14, fontweight="bold")

        # Ensure axes are visible
        ax.spines["top"].set_visible(True)
        ax.spines["right"].set_visible(True)
        ax.spines["bottom"].set_visible(True)
        ax.spines["left"].set_visible(True)

        # Set tick parameters to ensure visibility
        ax.tick_params(axis="both", which="major", labelsize=10, width=1, length=5)
        ax.tick_params(axis="both", which="minor", width=1, length=3)

        # Set x-ticks
        ax.set_xticks([r + bar_width * 1.5 for r in range(len(models))])
        ax.set_xticklabels(
            [model.split("/")[-1] for model in models], rotation=45, ha="right"
        )

        # Add grid for better readability
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        # Add legend
        ax.legend(fontsize=10)

        # Adjust layout
        plt.tight_layout()

        # Save chart to memory with optimized settings
        img = io.BytesIO()
        plt.savefig(img, format="png", dpi=120, bbox_inches="tight", pad_inches=0.2)
        img.seek(0)

        # Encode chart as base64
        chart_url = base64.b64encode(img.getvalue()).decode()

        # Close the figure to free memory
        plt.close(fig)

        # Create response with appropriate headers
        response = make_response(jsonify({"chart_url": chart_url}))
        response.headers["Content-Type"] = "application/json"
        response.headers["Cache-Control"] = "max-age=300"  # Cache for 5 minutes

        return response
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


@app.route("/api/chart/games_played")
def get_games_played_chart():
    """Generate a games played chart."""
    try:
        stats = get_cached_model_stats()

        if not stats:
            return make_response(jsonify({"error": "No data available"}), 404)

        # Sort models by number of games played
        sorted_models = sorted(
            stats.items(), key=lambda x: x[1]["games_played"], reverse=True
        )

        # Extract data for chart
        models = [model for model, _ in sorted_models]
        games_played = [stats[model]["games_played"] for model in models]
        mafia_games = [stats[model]["mafia_games"] for model in models]
        villager_games = [stats[model]["villager_games"] for model in models]
        doctor_games = [stats[model]["doctor_games"] for model in models]

        # Create chart with explicit figure and axes
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.set_facecolor("white")  # Set white background
        ax.set_facecolor("white")  # Set white background for plot area

        # Create stacked bars
        ax.bar(models, mafia_games, label="Mafia", color="red")
        ax.bar(
            models, villager_games, bottom=mafia_games, label="Villager", color="green"
        )
        ax.bar(
            models,
            doctor_games,
            bottom=[mafia_games[i] + villager_games[i] for i in range(len(models))],
            label="Doctor",
            color="purple",
        )

        # Add labels and title
        ax.set_xlabel("Models", fontsize=12, fontweight="bold")
        ax.set_ylabel("Games Played", fontsize=12, fontweight="bold")
        ax.set_title("Games Played by Model and Role", fontsize=14, fontweight="bold")

        # Ensure axes are visible
        ax.spines["top"].set_visible(True)
        ax.spines["right"].set_visible(True)
        ax.spines["bottom"].set_visible(True)
        ax.spines["left"].set_visible(True)

        # Set tick parameters to ensure visibility
        ax.tick_params(axis="both", which="major", labelsize=10, width=1, length=5)
        ax.tick_params(axis="both", which="minor", width=1, length=3)

        # Set x-ticks
        ax.set_xticks([model for model in models])
        ax.set_xticklabels(
            [model.split("/")[-1] for model in models], rotation=45, ha="right"
        )

        # Add grid for better readability
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        # Add legend
        ax.legend(fontsize=10)

        # Adjust layout
        plt.tight_layout()

        # Save chart to memory with optimized settings
        img = io.BytesIO()
        plt.savefig(img, format="png", dpi=120, bbox_inches="tight", pad_inches=0.2)
        img.seek(0)

        # Encode chart as base64
        chart_url = base64.b64encode(img.getvalue()).decode()

        # Close the figure to free memory
        plt.close(fig)

        # Create response with appropriate headers
        response = make_response(jsonify({"chart_url": chart_url}))
        response.headers["Content-Type"] = "application/json"
        response.headers["Cache-Control"] = "max-age=300"  # Cache for 5 minutes

        return response
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


@app.route("/api/chart/win_rates/image")
def get_win_rate_image():
    """Generate a win rate chart and return it directly as an image."""
    try:
        stats = get_cached_model_stats()

        if not stats:
            return make_response("No data available", 404)

        # Sort models by overall win rate
        sorted_models = sorted(
            stats.items(), key=lambda x: x[1]["win_rate"], reverse=True
        )

        # Extract data for chart
        models = [model for model, _ in sorted_models]
        win_rates = [stats[model]["win_rate"] * 100 for model in models]
        mafia_win_rates = [stats[model]["mafia_win_rate"] * 100 for model in models]
        villager_win_rates = [
            stats[model]["villager_win_rate"] * 100 for model in models
        ]
        doctor_win_rates = [stats[model]["doctor_win_rate"] * 100 for model in models]

        # Create chart with explicit figure and axes
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.set_facecolor("white")  # Set white background
        ax.set_facecolor("white")  # Set white background for plot area

        # Set width of bars
        bar_width = 0.2

        # Set position of bars on x axis
        r1 = np.arange(len(models))
        r2 = [x + bar_width for x in r1]
        r3 = [x + bar_width for x in r2]
        r4 = [x + bar_width for x in r3]

        # Create bars
        ax.bar(r1, win_rates, width=bar_width, label="Overall", color="blue")
        ax.bar(r2, mafia_win_rates, width=bar_width, label="Mafia", color="red")
        ax.bar(r3, villager_win_rates, width=bar_width, label="Villager", color="green")
        ax.bar(r4, doctor_win_rates, width=bar_width, label="Doctor", color="purple")

        # Add labels and title
        ax.set_xlabel("Models", fontsize=12, fontweight="bold")
        ax.set_ylabel("Win Rate (%)", fontsize=12, fontweight="bold")
        ax.set_title("Win Rates by Model and Role", fontsize=14, fontweight="bold")

        # Ensure axes are visible
        ax.spines["top"].set_visible(True)
        ax.spines["right"].set_visible(True)
        ax.spines["bottom"].set_visible(True)
        ax.spines["left"].set_visible(True)

        # Set tick parameters to ensure visibility
        ax.tick_params(axis="both", which="major", labelsize=10, width=1, length=5)
        ax.tick_params(axis="both", which="minor", width=1, length=3)

        # Set x-ticks
        ax.set_xticks([r + bar_width * 1.5 for r in range(len(models))])
        ax.set_xticklabels(
            [model.split("/")[-1] for model in models], rotation=45, ha="right"
        )

        # Add grid for better readability
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        # Add legend
        ax.legend(fontsize=10)

        # Adjust layout
        plt.tight_layout()

        # Save chart to memory with optimized settings
        img = io.BytesIO()
        plt.savefig(img, format="png", dpi=120, bbox_inches="tight", pad_inches=0.2)
        img.seek(0)

        # Close the figure to free memory
        plt.close(fig)

        # Return the image directly
        response = make_response(img.getvalue())
        response.headers["Content-Type"] = "image/png"
        response.headers["Cache-Control"] = "max-age=300"  # Cache for 5 minutes

        return response
    except Exception as e:
        return make_response(str(e), 500)


@app.route("/api/chart/games_played/image")
def get_games_played_image():
    """Generate a games played chart and return it directly as an image."""
    try:
        stats = get_cached_model_stats()

        if not stats:
            return make_response("No data available", 404)

        # Sort models by number of games played
        sorted_models = sorted(
            stats.items(), key=lambda x: x[1]["games_played"], reverse=True
        )

        # Extract data for chart
        models = [model for model, _ in sorted_models]
        games_played = [stats[model]["games_played"] for model in models]
        mafia_games = [stats[model]["mafia_games"] for model in models]
        villager_games = [stats[model]["villager_games"] for model in models]
        doctor_games = [stats[model]["doctor_games"] for model in models]

        # Create chart with explicit figure and axes
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.set_facecolor("white")  # Set white background
        ax.set_facecolor("white")  # Set white background for plot area

        # Create stacked bars
        ax.bar(models, mafia_games, label="Mafia", color="red")
        ax.bar(
            models, villager_games, bottom=mafia_games, label="Villager", color="green"
        )
        ax.bar(
            models,
            doctor_games,
            bottom=[mafia_games[i] + villager_games[i] for i in range(len(models))],
            label="Doctor",
            color="purple",
        )

        # Add labels and title
        ax.set_xlabel("Models", fontsize=12, fontweight="bold")
        ax.set_ylabel("Games Played", fontsize=12, fontweight="bold")
        ax.set_title("Games Played by Model and Role", fontsize=14, fontweight="bold")

        # Ensure axes are visible
        ax.spines["top"].set_visible(True)
        ax.spines["right"].set_visible(True)
        ax.spines["bottom"].set_visible(True)
        ax.spines["left"].set_visible(True)

        # Set tick parameters to ensure visibility
        ax.tick_params(axis="both", which="major", labelsize=10, width=1, length=5)
        ax.tick_params(axis="both", which="minor", width=1, length=3)

        # Set x-ticks
        ax.set_xticks([model for model in models])
        ax.set_xticklabels(
            [model.split("/")[-1] for model in models], rotation=45, ha="right"
        )

        # Add grid for better readability
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        # Add legend
        ax.legend(fontsize=10)

        # Adjust layout
        plt.tight_layout()

        # Save chart to memory with optimized settings
        img = io.BytesIO()
        plt.savefig(img, format="png", dpi=120, bbox_inches="tight", pad_inches=0.2)
        img.seek(0)

        # Close the figure to free memory
        plt.close(fig)

        # Return the image directly
        response = make_response(img.getvalue())
        response.headers["Content-Type"] = "image/png"
        response.headers["Cache-Control"] = "max-age=300"  # Cache for 5 minutes

        return response
    except Exception as e:
        return make_response(str(e), 500)


if __name__ == "__main__":
    try:
        # Parse command line arguments
        import argparse

        parser = argparse.ArgumentParser(description="LLM Mafia Dashboard")
        default_port = int(os.getenv("PORT", "5000"))
        parser.add_argument(
            "--port", type=int, default=default_port, help="Port to run the server on"
        )
        args = parser.parse_args()

        # Run the app
        print(f"Starting the dashboard application on port {args.port}...")
        debug = os.getenv("FLASK_DEBUG", "").lower() == "true"
        app.run(debug=debug, host="0.0.0.0", port=args.port)
    except Exception as e:
        print(f"Error starting application: {e}")
