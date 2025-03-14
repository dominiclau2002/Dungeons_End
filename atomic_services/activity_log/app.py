import os
from flask import Flask, jsonify
from models import db, ActivityLog

app = Flask(__name__)

# ✅ Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://user:password@mysql/activity_log_db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# ✅ API to get logs by player ID
@app.route("/log/<int:player_id>", methods=["GET"])
def get_logs(player_id):
    logs = ActivityLog.query.filter_by(player_id=player_id).all()
    return jsonify([log.to_dict() for log in logs]), 200

# ✅ API to get all logs
@app.route("/log", methods=["GET"])
def get_all_logs():
    logs = ActivityLog.query.all()
    return jsonify([log.to_dict() for log in logs]), 200

# ✅ Clear all logs
@app.route("/log", methods=["DELETE"])
def clear_logs():
    ActivityLog.query.delete()
    db.session.commit()
    return jsonify({"message": "Activity logs cleared!"}), 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5013, debug=True)
