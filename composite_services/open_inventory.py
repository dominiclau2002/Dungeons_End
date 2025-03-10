from flask import Flask, jsonify
from atomic_services.player import Player
from atomic_services.item import Item

app = Flask(__name__)

# Simulated player instance (replace with real player management)
player = Player(name="Hero")

@app.route('/inventory', methods=['GET'])
def view_inventory():
    """
    Retrieves the player's current inventory along with item descriptions.
    """
    inventory_items = player.inventory.view_inventory_items()
    
    if "inventory" not in inventory_items:
        return jsonify(inventory_items)  # Return "Your inventory is empty!"

    # Define descriptions for items in the game
    item_descriptions = {
        "Rusty Sword": "An old sword with a dull edge. Still better than nothing.",
        "Health Potion": "A small vial filled with red liquid. Restores health when consumed.",
        "Lockpick": "A tool used for opening locked doors and chests.",
        "Iron Armor": "A sturdy armor that provides good protection against attacks."
    }

    # Add descriptions to the player's inventory items
    inventory_with_descriptions = {
        item: item_descriptions.get(item, "No description available.") for item in inventory_items["inventory"]
    }

    return jsonify({"inventory": inventory_with_descriptions})

if __name__ == '__main__':
    app.run(port=5010, debug=True)


# call
# GET http://127.0.0.1:5010/inventory 