# \text-game\atomic_services\calculator.py

from atomic_services.score import Score

class ScoreCalculator:
    """Handles the final calculation of the player's score at the end of the game."""

    def __init__(self, score: Score):
        self.score = score
        self.bonus = 0
        self.penalty = 0

    def apply_bonus(self, bonus_points):
        """Applies bonus points for optimal game decisions."""
        self.bonus += bonus_points
        return {"message": f"Bonus of {bonus_points} points applied. Total bonus: {self.bonus}"}

    def apply_penalty(self, penalty_points):
        """Applies penalties for bad decisions or failed dice rolls."""
        self.penalty += penalty_points
        return {"message": f"Penalty of {penalty_points} points applied. Total penalty: {self.penalty}"}

    def calculate_final_score(self):
        """Computes the final score, factoring in bonuses and penalties."""
        final_score = self.score.get_total_score() + self.bonus - self.penalty
        return {
            "Final Score": max(final_score, 0),  # Prevent negative scores
            "Base Score": self.score.get_total_score(),
            "Bonus": self.bonus,
            "Penalty": self.penalty
        }

    def reset_calculator(self):
        """Resets the calculator for a new game session."""
        self.bonus = 0
        self.penalty = 0
        self.score.reset_score()
        return {"message": "Score calculator has been reset."}
