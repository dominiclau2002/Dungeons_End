import os
from flask import Flask, jsonify, request
from models import db, Score

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://user:password@mysql/score_db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/score/<int:player_id>", methods=["GET"])
def get_score(player_id):
    score = Score.query.filter_by(player_id=player_id).first()
    return jsonify(score.to_dict()) if score else ({"error": "Score not found"}, 404)

@app.route("/score/<int:player_id>/add", methods=["POST"])
def add_points(player_id):
    data = request.json
    points = data["points"]
    action = data["action"]

    score = Score.query.filter_by(player_id=player_id).first()
    if not score:
        score = Score(player_id=player_id, total_score=0)
        db.session.add(score)

    score.add_score(action, points)
    db.session.commit()

    return jsonify(score.to_dict())

@app.route("/score/<int:player_id>/reset", methods=["POST"])
def reset_score(player_id):
    score = Score.query.filter_by(player_id=player_id).first()
    if score:
        score.reset_score()
        db.session.commit()
        return jsonify({"message": "Score reset!"})
    return jsonify({"error": "Player score not found"}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5008, debug=True)
