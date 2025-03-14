import os, json, random
from flask import Flask, jsonify, request
from models import db, Enemy

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://user:password@mysql/enemy_db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/enemy/<int:room_id>", methods=["GET"])
def get_enemy(room_id):
    enemy = Enemy.query.filter_by(room_id=room_id).first()
    if enemy:
        return jsonify(enemy.to_dict()), 200
    return jsonify({"error": "Enemy not found"}), 404

@app.route("/enemy/<int:room_id>/attack", methods=["GET"])
def enemy_attack(room_id):
    enemy = Enemy.query.filter_by(room_id=room_id).first()
    if not enemy:
        return jsonify({"error": "No enemy found"}), 404

    attacks = json.loads(enemy.attacks)
    attack_name, damage_range = random.choice(list(attacks.items()))
    damage = random.randint(*damage_range)
    return jsonify({"attack": attack_name, "damage": damage})

@app.route("/enemy/<int:room_id>/damage", methods=["POST"])
def damage_enemy(room_id):
    enemy = Enemy.query.filter_by(room_id=room_id).first()
    if not enemy:
        return jsonify({"error": "Enemy not found"}), 404

    damage = request.json.get("damage", 0)
    enemy.health -= damage

    if enemy.health <= 0:
        loot = json.loads(enemy.loot)
        db.session.delete(enemy)
        db.session.commit()
        return jsonify({"message": "Enemy defeated!", "loot": loot})

    db.session.commit()
    return jsonify({"message": "Enemy damaged", "remaining_health": enemy.health})

if __name__ == '__main__':
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5005, debug=True)
