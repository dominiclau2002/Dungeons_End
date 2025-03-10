#atomic_services\item\app.py


from flask import Flask,jsonify, request
from item import Item

app = Flask(__name__)

@app.route('/item', methods=['POST'])
def create_item():
    data = request.json
    if not data or "id" not in data or "name" not in data or "item_type" not in data:
        return jsonify({"error": "Missing item data"}), 400

    item = Item(data["id"],data["name"], data["item_type"])
    return jsonify({"id":item.id,"name": item.name, "item_type": item.item_type})

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5002,debug=True)