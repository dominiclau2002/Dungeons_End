from flask import Blueprint, jsonify, request
from atomic_services.player import Player #Import player service

api = Blueprint('api', __name__)

#Create a single instance of Player
player = Player()

@api.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the Text-Based Game API!"})

@api.route('/player', methods=['GET'])
def get_player():
    """Returns player information."""
    return jsonify(player.get_player_info())

@api.route('/player/health', methods=['POST'])
def update_health():
    """Updates player health based on a given amount."""
    data = request.get_json()
    amount = data.get("amount", 0)
    return jsonify(player.update_health(amount))

def init_routes(app):
    app.register_blueprint(api)

