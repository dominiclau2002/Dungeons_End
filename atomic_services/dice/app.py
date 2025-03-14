from flask import Flask, jsonify, request
from dice import Dice

app = Flask(__name__)

@app.route("/roll", methods=["GET"])
def roll():
    """
    Rolls dice dynamically and returns the results.
    """
    sides = request.args.get("sides", default=6, type=int)
    count = request.args.get("count", default=1, type=int)

    if sides < 2 or count < 1:
        return jsonify({"error": "Invalid dice parameters"}), 400

    dice = Dice(sides)
    result = dice.roll(count)

    return jsonify({"sides": sides, "count": count, "results": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5007, debug=True)
