import os
from flask import Flask, jsonify
from models import db, CharacterModel

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://user:password@mysql/character_db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# db.init_app(app)

@app.route("/character/<string:name>", methods=["GET"])
def get_character(name):
    character = CharacterModel.query.filter_by(name=name).first()
    if not character:
        return jsonify({"error": "CharacterModel not found"}), 404
    return jsonify(character.to_dict())

@app.route("/characters", methods=["GET"])
def get_all_characters():
    characters = CharacterModel.query.all()
    return jsonify([char.to_dict() for char in characters])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
