from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class ScoreCalculation(db.Model):
    """
    Stores the final calculated scores for players.
    Now stored in a MySQL database using SQLAlchemy.
    """

    __tablename__ = "ScoreCalculations"

    CalculationID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PlayerID = db.Column(db.Integer, nullable=False, unique=True)  # Each player has one score calculation record
    BaseScore = db.Column(db.Integer, nullable=False, default=0)
    Bonus = db.Column(db.Integer, nullable=False, default=0)
    Penalty = db.Column(db.Integer, nullable=False, default=0)
    FinalScore = db.Column(db.Integer, nullable=False, default=0)

    def __init__(self, player_id, base_score=0, bonus=0, penalty=0):
        self.PlayerID = player_id
        self.BaseScore = base_score
        self.Bonus = bonus
        self.Penalty = penalty
        self.FinalScore = max(base_score + bonus - penalty, 0)  # Ensure score is never negative

    def to_dict(self):
        return {
            "CalculationID": self.CalculationID,
            "PlayerID": self.PlayerID,
            "BaseScore": self.BaseScore,
            "Bonus": self.Bonus,
            "Penalty": self.Penalty,
            "FinalScore": self.FinalScore
        }

    def apply_bonus(self, bonus_points):
        """
        Applies bonus points to the final score.
        """
        self.Bonus += bonus_points
        self.FinalScore = max(self.BaseScore + self.Bonus - self.Penalty, 0)
        db.session.commit()
        return {"message": f"Bonus of {bonus_points} points applied. Total bonus: {self.Bonus}"}

    def apply_penalty(self, penalty_points):
        """
        Applies penalty points to the final score.
        """
        self.Penalty += penalty_points
        self.FinalScore = max(self.BaseScore + self.Bonus - self.Penalty, 0)
        db.session.commit()
        return {"message": f"Penalty of {penalty_points} points applied. Total penalty: {self.Penalty}"}

    def recalculate_score(self):
        """
        Recalculates the final score based on base score, bonus, and penalties.
        """
        self.FinalScore = max(self.BaseScore + self.Bonus - self.Penalty, 0)
        db.session.commit()
        return {"message": "Score recalculated.", "FinalScore": self.FinalScore}

    def reset_calculator(self):
        """
        Resets the calculation for a new game session.
        """
        self.Bonus = 0
        self.Penalty = 0
        self.FinalScore = self.BaseScore
        db.session.commit()
        return {"message": "Score calculator has been reset."}
