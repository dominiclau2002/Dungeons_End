import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from score import Score, db

app = Flask(__name__)

# ✅ Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://user:password@score_db/score_db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ✅ Initialize Database
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/score/<int:player_id>", methods=["GET"])
def get_score(player_id):
    """
    Retrieves the score of a player.
    """
    score = Score.query.filter_by(PlayerID=player_id).first()
    
    if not score:
        return jsonify({"error": "Score not found"}), 404

    return jsonify(score.to_dict())

@app.route("/score/<int:player_id>/add", methods=["POST"])
def add_score(player_id):
    """
    Adds points to a player's score.
    """
    data = request.get_json()
    action = data.get("action", "Unknown Action")
    points = data.get("points", 0)

    score = Score.query.filter_by(PlayerID=player_id).first()

    if not score:
        # ✅ If no score record exists, create one
        score = Score(player_id=player_id)
        db.session.add(score)
        db.session.commit()

    result = score.add_score(action, points)
    return jsonify(result)

@app.route("/score/<int:player_id>/reset", methods=["POST"])
def reset_score(player_id):
    """
    Resets a player's score.
    """
    score = Score.query.filter_by(PlayerID=player_id).first()

    if not score:
        return jsonify({"error": "Score not found"}), 404

    result = score.reset_score()
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5008, debug=True)
