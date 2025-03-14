import os
from flask import Flask, jsonify, request
from models import db, ActivityLog

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://user:password@mysql/activity_log_db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/log", methods=["POST"])
def log_activity():
    data = request.get_json()
    player_id = data.get("player_id")
    action = data.get("action")

    if not player_id or not action:
        return jsonify({"error": "Player ID and action are required"}), 400

    new_log = ActivityLog(player_id=player_id, action=action)
    db.session.add(new_player)
    db.session.commit()

    return jsonify({"message": "Activity logged", "log": new_log.to_dict()}), 201

@app.route("/log/<int:player_id>", methods=["GET"])
def get_logs(player_id):
    logs = ActivityLog.query.filter_by(player_id=player_id).all()
    return jsonify([log.to_dict() for log in logs])

@app.route("/log/clear", methods=["DELETE"])
def clear_logs():
    db.session.query(ActivityLog).delete()
    db.session.commit()
    return jsonify({"message": "Activity logs cleared!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5013, debug=True)
