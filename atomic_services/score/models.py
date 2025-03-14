from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()

class Score(db.Model):
    __tablename__ = "scores"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    player_id = db.Column(db.Integer, nullable=False, unique=True)
    total_score = db.Column(db.Integer, default=0)
    action_log = db.Column(db.Text, default='[]')  # Store JSON as string

    def to_dict(self):
        return {
            "score_id": self.id,
            "player_id": self.player_id,
            "total_score": self.total_score,
            "action_log": json.loads(self.action_log),
        }

    def add_score(self, action, points):
        log = json.loads(self.action_log)
        log_entry = {"action": action, "points": points}
        log.append(log_entry)
        self.total_score += points
        self.action_log = json.dumps(log)

    def reset_score(self):
        self.total_score = 0
        self.action_log = json.dumps([])
