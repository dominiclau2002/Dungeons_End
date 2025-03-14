import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from enemy import Enemy, db

app = Flask(__name__)

# ✅ Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://user:password@mysql:3306/enemy_db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ✅ Initialize Database
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/enemy/<int:room_id>", methods=["GET"])
def get_enemy(room_id):
    """
    Retrieves the enemy in a given room.
    If none exists, creates a new one.
    """
    enemy = Enemy.query.filter_by(RoomID=room_id).first()

    if not enemy:
        # ✅ If no enemy exists, create a new one
        enemy = Enemy(
            room_id=room_id,
            name="Goblin",
            health=30,
            attacks={"Slash": (5, 12), "Bite": (3, 8)},
            loot=["Gold Coin", "Rusty Dagger"],
        )
        db.session.add(enemy)
        db.session.commit()

    return jsonify(enemy.to_dict())

@app.route("/enemy/<int:room_id>/attack", methods=["GET"])
def enemy_attack(room_id):
    """
    The enemy performs an attack.
    """
    enemy = Enemy.query.filter_by(RoomID=room_id).first()

    if not enemy:
        return jsonify({"error": "No enemy found in this room"}), 404

    return jsonify(enemy.attack())

@app.route("/enemy/<int:room_id>/damage", methods=["POST"])
def damage_enemy(room_id):
    """
    Player attacks an enemy in a room.
    """
    enemy = Enemy.query.filter_by(RoomID=room_id).first()

    if not enemy:
        return jsonify({"error": "No enemy found in this room"}), 404

    data = request.get_json()
    damage = data.get("damage", 0)

    result = enemy.take_damage(damage)

    if enemy.Health <= 0:
        db.session.delete(enemy)  # Remove defeated enemy from the database
    db.session.commit()

    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)