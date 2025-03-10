from flask import Flask, jsonify
from atomic_services.player import Player
from atomic_services.enemy import enemy_instances
from composite_services.activity_log_service import activity_log

app = Flask(__name__)

# Simulated player instance (Replace with real player management later)
player = Player(name="Hero")

@app.route('/game/restart', methods=['POST'])
def restart_game():
    """
    Resets the game:
    - Resets player health
    - Resets all enemies
    - Clears activity logs
    """
    # Reset Player Health
    player.health = 100  # Full health

    # Reset All Enemies
    for room_name in enemy_instances.keys():
        enemy_instances[room_name].health = 30  # Reset enemy health (customize per enemy)

    # Clear Activity Log
    activity_log.clear()  # Clears all logged actions

    return jsonify({
        "message": "Game has been restarted!",
        "player_health": player.health,
        "enemies_reset": list(enemy_instances.keys()),  # Shows which enemies were reset
        "logs_cleared": True
    })

@app.route('/game/save', methods=['POST'])
def save_game():
    """
    Saves the current game state (player stats, enemy states, logs).
    """
    game_state = {
        "player": {
            "name": player.name,
            "health": player.health
        },
        "enemies": {
            room: enemy_instances[room].health for room in enemy_instances
        },
        "logs": activity_log  # Current activity log
    }

    # In a real system, this would be saved to a database
    with open("saved_game.json", "w") as file:
        import json
        json.dump(game_state, file)

    return jsonify({"message": "Game progress saved!"})

@app.route('/game/load', methods=['POST'])
def load_game():
    """
    Loads the saved game state.
    """
    import json
    try:
        with open("saved_game.json", "r") as file:
            game_state = json.load(file)

        # Restore Player
        player.health = game_state["player"]["health"]

        # Restore Enemies
        for room, health in game_state["enemies"].items():
            if room in enemy_instances:
                enemy_instances[room].health = health 

        # Restore Activity Logs
        global activity_log
        activity_log = game_state["logs"]

        return jsonify({"message": "Game progress loaded!", "player_health": player.health})
    except FileNotFoundError:
        return jsonify({"message": "No saved game found!"}), 404

if __name__ == '__main__':
    app.run(port=5009, debug=True)
