#atomic_services\inventory\app.py

from flask import Flask,jsonify
from inventory import Inventory

app = Flask(__name__)

@app.route('/inventory')
def create_inventory():
    inventory = Inventory()
    return jsonify({"Inventory Status": inventory.view_inventory_items()})

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5001,debug=True)