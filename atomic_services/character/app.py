import os
from flask import Flask, jsonify
from models import db, Character

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://user:password@mysql/character_db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

def seed_characters():
    characters = [
        {"name": "Warrior", "hp": 100, "skill_description": "Berserker attack deals extra damage based on missing HP."},
        {"name": "Cleric", "hp": 80, "skill_description": "Heals for 15 HP if dice roll succeeds."},
        {"name": "Rogue", "hp": 75, "skill_description": "Backstab: Double damage if dice roll succeeds."},
        {"name": "Witch", "hp": 70, "skill_description": "Poisons enemy for damage over time if dice roll succeeds."}
    ]

    if Character.query.first() is None:
        for char_data in default_characters:
            character = Character(**char_data)
            db.session.add(character)
        db.session.commit()
        print("Default characters seeded.")
    else:
        print("Characters already seeded.")

with app.app_context():
    db.init_app(app)
    db.create_all()
    seed_characters()

@app.route("/character/<string:name>", methods=["GET"])
def get_character(name):
    character = Character.query.filter_by(name=name).first()
    if not character:
        return jsonify({"error": "Character not found"}), 404
    return jsonify(character.to_dict())

@app.route("/characters", methods=["GET"])
def get_all_characters():
    characters = Character.query.all()
    return jsonify([char.to_dict() for char in characters])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
