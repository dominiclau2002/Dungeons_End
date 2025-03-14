from flask import Flask, jsonify, request
from dice import Dice

app = Flask(__name__)

@app.route("/roll", methods=["GET"])
def roll():
    sides = request.args.get("sides", default=6, type=int)
    count = request.args.get("count", default=1, type=int)

    dice = Dice(sides)
    result = dice.roll(count)

    return jsonify({
        "sides": sides,
        "count": count,
        "results": result
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5007, debug=True)
