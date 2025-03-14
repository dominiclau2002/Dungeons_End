from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import Flask, jsonify, request
import os

app = Flask(__name__)

# ✅ Database Configuration
DATABASE_URL = "mysql+mysqlconnector://root:@localhost/activity_log_db"
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class ActivityLog(db.Model):
    """
    Stores all player actions in the game.
    Now stored in a MySQL database using SQLAlchemy.
    """
    __tablename__ = "ActivityLogs"

    LogID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PlayerID = db.Column(db.Integer, nullable=False)
    Action = db.Column(db.String(255), nullable=False)
    Timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, player_id, action):
        self.PlayerID = player_id
        self.Action = action

    def to_dict(self):
        return {
            "LogID": self.LogID,
            "PlayerID": self.PlayerID,
            "Action": self.Action,
            "Timestamp": self.Timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }

# ✅ API Endpoints

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
