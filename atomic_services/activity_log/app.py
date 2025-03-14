import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from activity_log import ActivityLog, db

app = Flask(__name__)

# ✅ Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://user:password@activity_log_db/activity_log_db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ✅ Initialize Database
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/log", methods=["POST"])
def log_activity():
    """
    Logs a player action.
    """
    data = request.get_json()
    player_id = data.get("player_id")
    action = data.get("action")

    if not player_id or not action:
        return jsonify({"error": "PlayerID and Action are required"}), 400

    log_entry = ActivityLog(player_id=player_id, action=action)
    db.session.add(log_entry)
    db.session.commit()

    return jsonify({"message": "Action logged successfully!", "log": log_entry.to_dict()}), 201

@app.route("/log/<int:player_id>", methods=["GET"])
def get_player_logs(player_id):
    """
    Retrieves all logs for a specific player.
    """
    logs = ActivityLog.query.filter_by(PlayerID=player_id).all()

    if not logs:
        return jsonify({"message": "No logs found for this player."})

    return jsonify([log.to_dict() for log in logs])

@app.route("/log/clear", methods=["DELETE"])
def clear_logs():
    """
    Clears all logs (Used when restarting a game).
    """
    db.session.query(ActivityLog).delete()
    db.session.commit()
    return jsonify({"message": "All logs have been cleared!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5013, debug=True)
