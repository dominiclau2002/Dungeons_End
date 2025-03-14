import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from calculator import ScoreCalculation, db

app = Flask(__name__)

# ✅ Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://user:password@calculator_db/calculator_db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ✅ Initialize Database
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/score/calculate/<int:player_id>", methods=["GET"])
def get_calculated_score(player_id):
    """
    Retrieves the final calculated score of a player.
    """
    calculation = ScoreCalculation.query.filter_by(PlayerID=player_id).first()
    
    if not calculation:
        return jsonify({"error": "Score calculation not found"}), 404

    return jsonify(calculation.to_dict())

@app.route("/score/calculate/<int:player_id>/bonus", methods=["POST"])
def add_bonus(player_id):
    """
    Adds bonus points to a player's final score.
    """
    data = request.get_json()
    bonus_points = data.get("bonus", 0)

    calculation = ScoreCalculation.query.filter_by(PlayerID=player_id).first()

    if not calculation:
        return jsonify({"error": "Score calculation not found"}), 404

    result = calculation.apply_bonus(bonus_points)
    return jsonify(result)

@app.route("/score/calculate/<int:player_id>/penalty", methods=["POST"])
def add_penalty(player_id):
    """
    Adds penalty points to a player's final score.
    """
    data = request.get_json()
    penalty_points = data.get("penalty", 0)

    calculation = ScoreCalculation.query.filter_by(PlayerID=player_id).first()

    if not calculation:
        return jsonify({"error": "Score calculation not found"}), 404

    result = calculation.apply_penalty(penalty_points)
    return jsonify(result)

@app.route("/score/calculate/<int:player_id>/reset", methods=["POST"])
def reset_calculation(player_id):
    """
    Resets the score calculation for a player.
    """
    calculation = ScoreCalculation.query.filter_by(PlayerID=player_id).first()

    if not calculation:
        return jsonify({"error": "Score calculation not found"}), 404

    result = calculation.reset_calculator()
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5009, debug=True)
