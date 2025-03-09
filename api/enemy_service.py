from flask import Flask, jsonify, request
from atomic_services.enemy import get_enemy, enemy_instances

app = Flask(__name__)

@app.route('/enemy/<room_name>', methods=['GET'])
def get_enemy_info(room_name):
    """
    Retrieves enemy details for the specified room.
    """
    enemy = get_enemy(room_name)
    return jsonify({
        "name": enemy.name,
        "health": enemy.health,
        "attacks": enemy.attacks,
        "status_effects": enemy.status_effects,
        "loot": enemy.loot
    })

@app.route('/enemy/<room_name>/attack', methods=['GET'])
def enemy_attack(room_name):
    """
    Enemy performs a random attack.
    """
    enemy = get_enemy(room_name)
    return jsonify(enemy.attack())

@app.route('/enemy/<room_name>/damage', methods=['POST'])
def damage_enemy(room_name):
    """
    Player attacks the enemy.
    Request JSON: {"damage": 10}
    """
    enemy = get_enemy(room_name)
    data = request.get_json()
    damage = data.get("damage", 0)
    
    result = enemy.take_damage(damage)

    if enemy.is_defeated():
        # Remove the defeated enemy from the instance
        del enemy_instances[room_name]
        return jsonify({
            "message": result["message"],
            "loot": result["loot"]
        })

    return jsonify(result)

if __name__ == '__main__':
    app.run(port=5005, debug=True)
