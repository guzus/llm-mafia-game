"""
Dashboard for the LLM Mafia Game Competition.
"""

import io
import base64
import json
import time
import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
import matplotlib

matplotlib.use("Agg")  # Use Agg backend for non-interactive mode
import matplotlib.pyplot as plt
import numpy as np
from flask import Flask, render_template, request, jsonify, Response, make_response
from firebase_manager import FirebaseManager

app = Flask(__name__, static_folder="static", template_folder="templates")
firebase = FirebaseManager()


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


@app.route("/api/stats")
def get_stats():
    """Get statistics from Firebase."""
    stats = firebase.get_model_stats()

    # Set cache control headers for better performance
    response = make_response(jsonify(stats))
    response.headers["Content-Type"] = "application/json"
    response.headers["Cache-Control"] = "max-age=60"  # Cache for 60 seconds

    return response


@app.route("/api/games")
def get_games():
    """Get game results from Firebase."""
    try:
        limit = request.args.get("limit", default=100, type=int)
        if limit < 1 or limit > 1000:
            return make_response(
                jsonify({"error": "Limit must be between 1 and 1000"}), 400
            )

        games = firebase.get_game_results(limit=limit)

        # Validate timestamp format
        for game in games:
            if "timestamp" in game and isinstance(game["timestamp"], int):
                # Ensure timestamp is in seconds, not milliseconds
                if game["timestamp"] > 10000000000:  # If in milliseconds
                    game["timestamp"] = game["timestamp"] // 1000

        response = make_response(jsonify(games))
        response.headers["Content-Type"] = "application/json"
        response.headers["Cache-Control"] = "max-age=60"

        return response
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


@app.route("/api/game/<game_id>")
def get_game(game_id):
    """Get game data from Firebase."""
    game_data = firebase.get_game_log(game_id)

    if not game_data:
        return jsonify({"error": "Game not found"}), 404

    # Set cache control headers for better performance
    response = make_response(jsonify(game_data))
    response.headers["Content-Type"] = "application/json"
    response.headers["Cache-Control"] = "max-age=60"  # Cache for 60 seconds

    return response


@app.route("/api/chart/win_rates")
def get_win_rate_chart():
    """Generate a win rate chart."""
    try:
        stats = firebase.get_model_stats()

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
        stats = firebase.get_model_stats()

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
        stats = firebase.get_model_stats()

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
        stats = firebase.get_model_stats()

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


# Create templates directory and index.html
@app.route("/create_templates")
def create_templates():
    """Create templates directory and index.html."""
    try:
        import os

        # Create templates directory if it doesn't exist
        if not os.path.exists("templates"):
            os.makedirs("templates")

        # Create index.html
        with open("templates/index.html", "w") as f:
            f.write(
                """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Mafia Game Competition</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        h1, h2 {
            color: #333;
        }
        .chart-container {
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 20px;
        }
        .chart {
            width: 100%;
            max-width: 100%;
            height: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background-color: white;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f8f8;
            font-weight: bold;
        }
        tr:hover {
            background-color: #f1f1f1;
        }
        .loading {
            text-align: center;
            padding: 20px;
            font-style: italic;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>LLM Mafia Game Competition</h1>
        
        <div class="chart-container">
            <h2>Win Rates by Model and Role</h2>
            <div id="win-rate-chart" class="loading">Loading chart...</div>
        </div>
        
        <div class="chart-container">
            <h2>Games Played by Model and Role</h2>
            <div id="games-played-chart" class="loading">Loading chart...</div>
        </div>
        
        <h2>Model Statistics</h2>
        <table id="stats-table">
            <thead>
                <tr>
                    <th>Model</th>
                    <th>Games Played</th>
                    <th>Overall Win Rate</th>
                    <th>Mafia Win Rate</th>
                    <th>Villager Win Rate</th>
                    <th>Doctor Win Rate</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td colspan="6" class="loading">Loading data...</td>
                </tr>
            </tbody>
        </table>
        
        <h2>Recent Games</h2>
        <table id="games-table">
            <thead>
                <tr>
                    <th>Game ID</th>
                    <th>Winner</th>
                    <th>Participants</th>
                    <th>Timestamp</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td colspan="4" class="loading">Loading data...</td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <script>
        // Load charts directly as images (more efficient)
        document.addEventListener('DOMContentLoaded', function() {
            // Win rates chart
            document.getElementById('win-rate-chart').innerHTML = 
                `<img src="/api/chart/win_rates/image" class="chart" alt="Win Rates Chart" 
                      onerror="loadFallbackChart('win-rate-chart')">`;
            
            // Games played chart
            document.getElementById('games-played-chart').innerHTML = 
                `<img src="/api/chart/games_played/image" class="chart" alt="Games Played Chart" 
                      onerror="loadFallbackChart('games-played-chart')">`;
        });
        
        // Fallback to base64 method if direct image loading fails
        function loadFallbackChart(elementId) {
            console.log(`Direct image loading failed for ${elementId}, trying base64 method...`);
            
            const endpoint = elementId === 'win-rate-chart' ? 
                '/api/chart/win_rates' : '/api/chart/games_played';
                
            fetch(endpoint)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.error) {
                        document.getElementById(elementId).innerHTML = 'No data available';
                    } else {
                        document.getElementById(elementId).innerHTML = 
                            `<img src="data:image/png;base64,${data.chart_url}" class="chart" 
                                  alt="${elementId === 'win-rate-chart' ? 'Win Rates' : 'Games Played'} Chart">`;
                    }
                })
                .catch(error => {
                    console.error(`Error fetching chart data: ${error}`);
                    document.getElementById(elementId).innerHTML = 'Error loading chart';
                });
        }
        
        // Fetch model statistics
        fetch('/api/stats')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                const tableBody = document.querySelector('#stats-table tbody');
                tableBody.innerHTML = '';
                
                if (Object.keys(data).length === 0) {
                    tableBody.innerHTML = '<tr><td colspan="6" class="loading">No data available</td></tr>';
                    return;
                }
                
                // Sort models by win rate
                const sortedModels = Object.keys(data).sort((a, b) => data[b].win_rate - data[a].win_rate);
                
                for (const model of sortedModels) {
                    const stats = data[model];
                    const row = document.createElement('tr');
                    
                    // Format model name to show only the last part
                    const modelName = model.split('/').pop();
                    
                    row.innerHTML = `
                        <td>${modelName}</td>
                        <td>${stats.games_played}</td>
                        <td>${(stats.win_rate * 100).toFixed(2)}%</td>
                        <td>${(stats.mafia_win_rate * 100).toFixed(2)}% (${stats.mafia_wins}/${stats.mafia_games})</td>
                        <td>${(stats.villager_win_rate * 100).toFixed(2)}% (${stats.villager_wins}/${stats.villager_games})</td>
                        <td>${(stats.doctor_win_rate * 100).toFixed(2)}% (${stats.doctor_wins}/${stats.doctor_games})</td>
                    `;
                    
                    tableBody.appendChild(row);
                }
            })
            .catch(error => {
                console.error('Error fetching model statistics:', error);
                document.querySelector('#stats-table tbody').innerHTML = '<tr><td colspan="6" class="loading">Error loading data</td></tr>';
            });
        
        // Fetch recent games
        fetch('/api/games?limit=10')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                const tableBody = document.querySelector('#games-table tbody');
                tableBody.innerHTML = '';
                
                if (data.length === 0) {
                    tableBody.innerHTML = '<tr><td colspan="4" class="loading">No games available</td></tr>';
                    return;
                }
                
                // Sort games by timestamp (newest first)
                data.sort((a, b) => b.timestamp - a.timestamp);
                
                for (const game of data) {
                    const row = document.createElement('tr');
                    
                    // Format timestamp
                    const date = new Date(game.timestamp * 1000);
                    const formattedDate = date.toLocaleString();
                    
                    // Format participants
                    const participants = Object.entries(game.participants)
                        .map(([model, role]) => `${model.split('/').pop()} (${role})`)
                        .join(', ');
                    
                    row.innerHTML = `
                        <td>${game.game_id}</td>
                        <td>${game.winner}</td>
                        <td>${participants}</td>
                        <td>${formattedDate}</td>
                    `;
                    
                    tableBody.appendChild(row);
                }
            })
            .catch(error => {
                console.error('Error fetching recent games:', error);
                document.querySelector('#games-table tbody').innerHTML = '<tr><td colspan="4" class="loading">Error loading data</td></tr>';
            });
    </script>
</body>
</html>"""
            )

        return "Templates created successfully!"
    except Exception as e:
        return make_response(f"Error creating templates: {str(e)}", 500)


@app.route("/poker")
def poker_index():
    """Render the poker games dashboard page."""
    return render_template("poker_index.html")


@app.route("/poker/game/<game_id>")
def poker_game_detail(game_id):
    """Render the poker game detail page."""
    # Get game data to pass to the template
    game_data = firebase.get_poker_game_log(game_id)

    # If game data not found, return 404
    if not game_data:
        return render_template("404.html", message="Poker game not found"), 404

    return render_template(
        "poker_game_detail.html", game_id=game_id, game_data=game_data
    )


@app.route("/api/poker/games")
def get_poker_games():
    """Get poker game results from Firebase."""
    limit = request.args.get("limit", default=100, type=int)
    games = firebase.get_poker_game_results(limit=limit)

    # Set cache control headers for better performance
    response = make_response(jsonify(games))
    response.headers["Content-Type"] = "application/json"
    response.headers["Cache-Control"] = "max-age=60"  # Cache for 60 seconds

    return response


@app.route("/api/poker/game/<game_id>")
def get_poker_game(game_id):
    """Get poker game data from Firebase."""
    game_data = firebase.get_poker_game_log(game_id)

    if not game_data:
        return jsonify({"error": "Poker game not found"}), 404

    # Set cache control headers for better performance
    response = make_response(jsonify(game_data))
    response.headers["Content-Type"] = "application/json"
    response.headers["Cache-Control"] = "max-age=60"  # Cache for 60 seconds

    return response


@app.route("/api/poker/stats")
def get_poker_stats():
    """Get poker model statistics from Firebase."""
    stats = firebase.get_poker_model_stats()

    # Set cache control headers for better performance
    response = make_response(jsonify(stats))
    response.headers["Content-Type"] = "application/json"
    response.headers["Cache-Control"] = "max-age=60"  # Cache for 60 seconds

    return response


if __name__ == "__main__":
    try:
        # Parse command line arguments
        import argparse

        parser = argparse.ArgumentParser(description="LLM Mafia Dashboard")
        parser.add_argument(
            "--port", type=int, default=5000, help="Port to run the server on"
        )
        args = parser.parse_args()

        # Create templates
        import os

        if not os.path.exists("templates"):
            os.makedirs("templates")
            print("Created templates directory")

            # Create the template file by calling the create_templates function
            from flask import current_app

            with app.app_context():
                create_templates()
                print("Created index.html template")

        # Run the app
        print(f"Starting the dashboard application on port {args.port}...")
        app.run(debug=True, host="0.0.0.0", port=args.port)
    except Exception as e:
        print(f"Error starting application: {e}")
