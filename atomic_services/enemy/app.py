import os
import json
import random
from flask import Flask, jsonify, request
from models import db, Enemy

app = Flask(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+mysqlconnector://user:password@mysql/enemy_db"
)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# Get enemy by ID


@app.route("/enemy/<int:enemy_id>", methods=["GET"])
def get_enemy(enemy_id):
    enemy = Enemy.query.get(enemy_id)
    if enemy:
        return jsonify(enemy.to_dict()), 200
    return jsonify({"error": "Enemy not found"}), 404

# Get enemies by room (using the EnemyIDs from Room table)


@app.route("/enemy/room/<int:room_id>", methods=["GET"])
def get_enemies_by_room(room_id):
    # This would typically involve a call to the room service to get EnemyIDs
    # For now, we'll just return all enemies
    enemies = Enemy.query.all()
    return jsonify([enemy.to_dict() for enemy in enemies]), 200

# Enemy attack


@app.route("/enemy/<int:enemy_id>/attack", methods=["GET"])
def enemy_attack(enemy_id):
    enemy = Enemy.query.get(enemy_id)
    if not enemy:
        return jsonify({"error": "Enemy not found"}), 404

    # For now, return basic damage based on the enemy's damage stat
    damage = random.randint(1, enemy.Damage)
    return jsonify({
        "enemy_name": enemy.Name,
        "damage": damage,
        "message": f"{enemy.Name} attacks for {damage} damage!"
    })

# Damage enemy


@app.route("/enemy/<int:enemy_id>/damage", methods=["POST"])
def damage_enemy(enemy_id):
    enemy = Enemy.query.get(enemy_id)
    if not enemy:
        return jsonify({"error": "Enemy not found"}), 404

    data = request.get_json()
    damage = data.get("damage", 0)

    enemy.Health -= damage

    response = {
        "enemy_name": enemy.Name,
        "damage_dealt": damage,
        "remaining_health": enemy.Health,
        "message": f"{enemy.Name} took {damage} damage!"
    }

    if enemy.Health <= 0:
        response["message"] = f"{enemy.Name} has been defeated!"
        response["points"] = enemy.Points
        response["loot"] = enemy.Loot
        db.session.delete(enemy)

    db.session.commit()
    return jsonify(response)

# Create new enemy (admin endpoint)


@app.route("/enemy", methods=["POST"])
def create_enemy():
    data = request.get_json()

    required_fields = ['name', 'description',
                       'health', 'damage', 'attack', 'points']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    new_enemy = Enemy(
        Name=data['name'],
        Description=data['description'],
        Health=data['health'],
        Damage=data['damage'],
        Attack=data['attack'],
        Points=data['points'],
        Loot=data.get('loot')  # Optional field
    )

    db.session.add(new_enemy)
    db.session.commit()

    return jsonify(new_enemy.to_dict()), 201


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5005, debug=True)
