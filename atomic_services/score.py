# \text-game\atomic_services\score.py

class Score:
    """Handles score calculation based on player actions."""

    def __init__(self):
        self.total_score = 0
        self.action_log = []  # Stores (action, points) tuples

    def add_score(self, action, points):
        """Adds score based on a specific action."""
        self.total_score += points
        self.action_log.append((action, points))
        return {"message": f"Action '{action}' earned {points} points. Total score: {self.total_score}"}

    def get_total_score(self):
        """Returns the player's total score."""
        return self.total_score

    def get_action_log(self):
        """Returns a history of actions and points earned."""
        return self.action_log

    def reset_score(self):
        """Resets the score for a new game session."""
        self.total_score = 0
        self.action_log = []
        return {"message": "Score has been reset."}
