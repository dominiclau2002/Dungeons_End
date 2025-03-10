#atomic_services\player\app.py
from flask import Flask,jsonify
from player import Player

app = Flask(__name__)

@app.route("/player")
def create_player():
    player = Player()
    return jsonify({"Player Info": player.get_player_info()})
    
if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000,debug=True)