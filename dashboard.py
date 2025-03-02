"""
Dashboard for the LLM Mafia Game Competition.
"""

import io
import base64
import matplotlib

matplotlib.use("Agg")  # Use Agg backend for non-interactive mode
import matplotlib.pyplot as plt
import numpy as np
from flask import Flask, render_template, request, jsonify
from firebase_manager import FirebaseManager

app = Flask(__name__)
firebase = FirebaseManager()


@app.route("/")
def index():
    """Render the main dashboard page."""
    return render_template("index.html")


@app.route("/api/stats")
def get_stats():
    """Get statistics from Firebase."""
    stats = firebase.get_model_stats()
    return jsonify(stats)


@app.route("/api/games")
def get_games():
    """Get game results from Firebase."""
    limit = request.args.get("limit", default=100, type=int)
    games = firebase.get_game_results(limit=limit)
    return jsonify(games)


@app.route("/api/chart/win_rates")
def get_win_rate_chart():
    """Generate a win rate chart."""
    stats = firebase.get_model_stats()

    if not stats:
        return jsonify({"error": "No data available"})

    # Sort models by overall win rate
    sorted_models = sorted(stats.items(), key=lambda x: x[1]["win_rate"], reverse=True)

    # Extract data for chart
    models = [model for model, _ in sorted_models]
    win_rates = [stats[model]["win_rate"] * 100 for model in models]
    mafia_win_rates = [stats[model]["mafia_win_rate"] * 100 for model in models]
    villager_win_rates = [stats[model]["villager_win_rate"] * 100 for model in models]
    doctor_win_rates = [stats[model]["doctor_win_rate"] * 100 for model in models]

    # Create chart
    plt.figure(figsize=(12, 8))

    # Set width of bars
    bar_width = 0.2

    # Set position of bars on x axis
    r1 = np.arange(len(models))
    r2 = [x + bar_width for x in r1]
    r3 = [x + bar_width for x in r2]
    r4 = [x + bar_width for x in r3]

    # Create bars
    plt.bar(r1, win_rates, width=bar_width, label="Overall", color="blue")
    plt.bar(r2, mafia_win_rates, width=bar_width, label="Mafia", color="red")
    plt.bar(r3, villager_win_rates, width=bar_width, label="Villager", color="green")
    plt.bar(r4, doctor_win_rates, width=bar_width, label="Doctor", color="purple")

    # Add labels and title
    plt.xlabel("Models")
    plt.ylabel("Win Rate (%)")
    plt.title("Win Rates by Model and Role")
    plt.xticks(
        [r + bar_width * 1.5 for r in range(len(models))],
        [model.split("/")[-1] for model in models],
        rotation=45,
        ha="right",
    )
    plt.legend()

    # Adjust layout
    plt.tight_layout()

    # Save chart to memory
    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)

    # Encode chart as base64
    chart_url = base64.b64encode(img.getvalue()).decode()

    # Close the figure to free memory
    plt.close()

    return jsonify({"chart_url": chart_url})


@app.route("/api/chart/games_played")
def get_games_played_chart():
    """Generate a games played chart."""
    stats = firebase.get_model_stats()

    if not stats:
        return jsonify({"error": "No data available"})

    # Sort models by number of games played
    sorted_models = sorted(stats.items(), key=lambda x: x[1]["games"], reverse=True)

    # Extract data for chart
    models = [model for model, _ in sorted_models]
    games_played = [stats[model]["games"] for model in models]
    mafia_games = [stats[model]["mafia_games"] for model in models]
    villager_games = [stats[model]["villager_games"] for model in models]
    doctor_games = [stats[model]["doctor_games"] for model in models]

    # Create chart
    plt.figure(figsize=(12, 8))

    # Create stacked bars
    plt.bar(models, mafia_games, label="Mafia", color="red")
    plt.bar(models, villager_games, bottom=mafia_games, label="Villager", color="green")
    plt.bar(
        models,
        doctor_games,
        bottom=[mafia_games[i] + villager_games[i] for i in range(len(models))],
        label="Doctor",
        color="purple",
    )

    # Add labels and title
    plt.xlabel("Models")
    plt.ylabel("Games Played")
    plt.title("Games Played by Model and Role")
    plt.xticks(
        [model for model in models],
        [model.split("/")[-1] for model in models],
        rotation=45,
        ha="right",
    )
    plt.legend()

    # Adjust layout
    plt.tight_layout()

    # Save chart to memory
    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)

    # Encode chart as base64
    chart_url = base64.b64encode(img.getvalue()).decode()

    # Close the figure to free memory
    plt.close()

    return jsonify({"chart_url": chart_url})


# Create templates directory and index.html
@app.route("/create_templates")
def create_templates():
    """Create templates directory and index.html."""
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
        // Fetch win rate chart
        fetch('/api/chart/win_rates')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('win-rate-chart').innerHTML = 'No data available';
                } else {
                    document.getElementById('win-rate-chart').innerHTML = `<img src="data:image/png;base64,${data.chart_url}" class="chart" alt="Win Rates Chart">`;
                }
            })
            .catch(error => {
                console.error('Error fetching win rate chart:', error);
                document.getElementById('win-rate-chart').innerHTML = 'Error loading chart';
            });
        
        // Fetch games played chart
        fetch('/api/chart/games_played')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('games-played-chart').innerHTML = 'No data available';
                } else {
                    document.getElementById('games-played-chart').innerHTML = `<img src="data:image/png;base64,${data.chart_url}" class="chart" alt="Games Played Chart">`;
                }
            })
            .catch(error => {
                console.error('Error fetching games played chart:', error);
                document.getElementById('games-played-chart').innerHTML = 'Error loading chart';
            });
        
        // Fetch model statistics
        fetch('/api/stats')
            .then(response => response.json())
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
            .then(response => response.json())
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


if __name__ == "__main__":
    # Create templates
    import os

    if not os.path.exists("templates"):
        os.makedirs("templates")
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
        // Fetch win rate chart
        fetch('/api/chart/win_rates')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('win-rate-chart').innerHTML = 'No data available';
                } else {
                    document.getElementById('win-rate-chart').innerHTML = `<img src="data:image/png;base64,${data.chart_url}" class="chart" alt="Win Rates Chart">`;
                }
            })
            .catch(error => {
                console.error('Error fetching win rate chart:', error);
                document.getElementById('win-rate-chart').innerHTML = 'Error loading chart';
            });
        
        // Fetch games played chart
        fetch('/api/chart/games_played')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('games-played-chart').innerHTML = 'No data available';
                } else {
                    document.getElementById('games-played-chart').innerHTML = `<img src="data:image/png;base64,${data.chart_url}" class="chart" alt="Games Played Chart">`;
                }
            })
            .catch(error => {
                console.error('Error fetching games played chart:', error);
                document.getElementById('games-played-chart').innerHTML = 'Error loading chart';
            });
        
        // Fetch model statistics
        fetch('/api/stats')
            .then(response => response.json())
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
            .then(response => response.json())
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

    # Run the app
    app.run(debug=True)
