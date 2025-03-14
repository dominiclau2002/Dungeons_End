from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Score(db.Model):
    """
    Represents the score of a player.
    Now stored in a MySQL database using SQLAlchemy.
    """

    __tablename__ = "Scores"

    ScoreID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PlayerID = db.Column(db.Integer, nullable=False, unique=True)  # Each player has one score record
    TotalScore = db.Column(db.Integer, nullable=False, default=0)
    ActionLog = db.Column(db.JSON, nullable=False)  # Stores action history as JSON

    def __init__(self, player_id, total_score=0, action_log=None):
        self.PlayerID = player_id
        self.TotalScore = total_score
        self.ActionLog = action_log if action_log else []

    def to_dict(self):
        return {
            "ScoreID": self.ScoreID,
            "PlayerID": self.PlayerID,
            "TotalScore": self.TotalScore,
            "ActionLog": self.ActionLog,
        }

    def add_score(self, action, points):
        """
        Adds score based on a specific action.
        """
        self.TotalScore += points
        self.ActionLog.append({"action": action, "points": points})
        db.session.commit()
        return {"message": f"Action '{action}' earned {points} points. Total score: {self.TotalScore}"}

    def reset_score(self):
        """
        Resets the player's score.
        """
        self.TotalScore = 0
        self.ActionLog = []
        db.session.commit()
        return {"message": "Score has been reset."}
