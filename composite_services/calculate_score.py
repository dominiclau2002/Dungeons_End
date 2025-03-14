from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

# ✅ Microservice URL for fetching scores
SCORE_SERVICE_URL = os.getenv("SCORE_SERVICE_URL", "http://score_service:5015")

@app.route('/calculate_score/<int:player_id>', methods=['GET'])
def calculate_final_score(player_id):
    """
    Fetches all scores from the score microservice and calculates the final score.
    """
    # ✅ Get all scores for the player
    score_response = requests.get(f"{SCORE_SERVICE_URL}/score/{player_id}")
    if score_response.status_code != 200:
        return jsonify({"error": "Could not fetch scores"}), 500

    scores = score_response.json().get("scores", [])
    
    # ✅ Sum up all points
    final_score = sum(score["Points"] for score in scores)

    return jsonify({
        "player_id": player_id,
        "final_score": final_score
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5016, debug=True)
