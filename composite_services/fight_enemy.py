from flask import Flask, jsonify, request
from atomic_services.player import Player
from atomic_services.enemy import get_enemy
from atomic_services.dice import Dice

app = Flask(__name__)

# Simulated player instance (should be replaced with a proper player management system)
player = Player(name="Hero")

@app.route('/combat/<room_name>/start', methods=['GET'])
def start_combat(room_name):
    """
    Starts combat with an enemy in the specified room.
    """
    enemy = get_enemy(room_name)

    if enemy.is_defeated():
        return jsonify({"message": f"{enemy.name} is already defeated!"}), 400

    return jsonify({
        "message": f"You encountered a {enemy.name}!",
        "player_health": player.health,
        "enemy_health": enemy.health
    })

@app.route('/combat/<room_name>/attack', methods=['POST'])
def player_attack(room_name):
    """
    The player attacks the enemy.
    Uses dice roll to determine damage.
    """
    if player.health <= 0:
        return jsonify({"message": "You are already dead! Game Over."}), 400

    enemy = get_enemy(room_name)

    if enemy.is_defeated():
        return jsonify({"message": f"{enemy.name} is already defeated!"}), 400

    # Roll damage based on player's weapon (for now, assume a simple D6 roll)
    dice = Dice(6)
    damage = dice.roll()[0]  # Single D6 roll

    enemy_result = enemy.take_damage(damage)

    if enemy.is_defeated():
        loot = enemy.drop_loot()
        return jsonify({
            "message": f"You defeated {enemy.name}!",
            "damage_dealt": damage,
            "enemy_health": 0,
            "loot": loot
        })

    return jsonify({
        "message": f"You attacked {enemy.name} for {damage} damage!",
        "damage_dealt": damage,
        "enemy_health": enemy.health
    })

@app.route('/combat/<room_name>/enemy-turn', methods=['POST'])
def enemy_attack(room_name):
    """
    The enemy takes its turn and attacks the player.
    """
    enemy = get_enemy(room_name)

    if enemy.is_defeated():
        return jsonify({"message": f"{enemy.name} is already defeated!"}), 400

    attack_result = enemy.attack()
    damage = attack_result["damage"]

    player.decrease_health(damage)

    # Check if the player has lost all HP
    if player.health <= 0:
        return jsonify({
            "message": f"{enemy.name} attacked you with {attack_result['attack']} for {damage} damage! You have been defeated.",
            "player_health": 0,
            "game_over": True
        })

    return jsonify({
        "message": f"{enemy.name} attacked you with {attack_result['attack']} for {damage} damage!",
        "player_health": player.health,
        "enemy_health": enemy.health,
        "status_effect": attack_result["status_effect"]
    })

@app.route('/combat/game-over', methods=['GET'])
def game_over():
    """
    Handles game over state when the player has 0 HP.
    """
    if player.health > 0:
        return jsonify({"message": "You are still alive! Keep fighting."}), 400

    return jsonify({
        "message": "Game Over! You have been defeated.",
        "restart": "/restart"  # Future feature for restarting the game
    })

if __name__ == '__main__':
    app.run(port=5008, debug=True)


# run service
# python composite_services/combat_service.py

# start combat
# GET http://127.0.0.1:5008/combat/Room 2/start

# player attack
# POST http://127.0.0.1:5008/combat/Room 2/attack

# enemy attack
# POST http://127.0.0.1:5008/combat/Room 2/enemy-turn

# check for gameover
# GET http://127.0.0.1:5008/combat/game-over