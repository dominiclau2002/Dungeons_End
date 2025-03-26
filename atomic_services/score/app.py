import os
from flask import Flask, jsonify, request
from models import db, Score
from sqlalchemy import func

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://user:password@mysql/score_db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/score", methods=["POST"])
def add_score():
    data = request.get_json()
    
    required_fields = ["player_id", "points", "reason"]
    if not data or not all(field in data for field in required_fields):
        return jsonify({
            "error": "Missing required fields",
            "required": required_fields
        }), 400

    valid_reasons = ['combat', 'item_collection']
    if data['reason'] not in valid_reasons:
        return jsonify({
            "error": "Invalid reason",
            "valid_reasons": valid_reasons
        }), 400

    new_score = Score(
        PlayerID=data['player_id'],
        Points=data['points'],
        Reason=data['reason']
    )
    
    db.session.add(new_score)
    db.session.commit()

    return jsonify({
        "message": "Score entry added successfully",
        "score": new_score.to_dict()
    }), 201

@app.route("/score/total/<int:player_id>", methods=["GET"])
def get_total_score(player_id):
    total_score = db.session.query(
        func.sum(Score.Points)
    ).filter_by(PlayerID=player_id).scalar() or 0

    score_entries = Score.query.filter_by(PlayerID=player_id).all()
    
    return jsonify({
        "player_id": player_id,
        "total_score": total_score,
        "score_history": [entry.to_dict() for entry in score_entries]
    }), 200

@app.route("/score/<int:player_id>/reason/<string:reason>", methods=["GET"])
def get_scores_by_reason(player_id, reason):
    valid_reasons = ['combat', 'item_collection']
    if reason not in valid_reasons:
        return jsonify({
            "error": "Invalid reason",
            "valid_reasons": valid_reasons
        }), 400

    scores = Score.query.filter_by(
        PlayerID=player_id,
        Reason=reason
    ).all()

    total = sum(score.Points for score in scores)

    return jsonify({
        "player_id": player_id,
        "reason": reason,
        "total_score": total,
        "score_entries": [score.to_dict() for score in scores]
    }), 200

@app.route("/scores", methods=["GET"])
def get_all_scores():
    scores = Score.query.all()
    return jsonify({
        "scores": [score.to_dict() for score in scores]
    }), 200

@app.route("/score/<int:player_id>", methods=["DELETE"])
def delete_player_scores(player_id):
    scores = Score.query.filter_by(PlayerID=player_id).all()
    if not scores:
        return jsonify({
            "message": "No scores found for this player"
        }), 404

    for score in scores:
        db.session.delete(score)
    db.session.commit()

    return jsonify({
        "message": f"All scores deleted for player {player_id}"
    }), 200

@app.route("/score/entry/<int:score_id>", methods=["GET"])
def get_score_entry(score_id):
    score = Score.query.get(score_id)
    if not score:
        return jsonify({
            "error": "Score entry not found"
        }), 404

    return jsonify(score.to_dict()), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5008, debug=True)
