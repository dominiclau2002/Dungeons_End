from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/roll_dice', methods=['GET'])

def roll_dice():
    """Rolls a 6-sided dice (1-6)."""
    import random
    result = random.randint(1, 6)
    return jsonify({"dice_roll": result})

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5002, debug=True)
