#\text-game\atomic_services\inventory.py
import requests
class Inventory:
    def __init__(self, player_id):
        self.player_id = player_id

    def add_to_inventory(self, item_id):
        """Send API request to app.py to add an item to the database."""
        response = requests.post("http://inventory:5001/inventory", json={
            "player_id": self.player_id,
            "item_id": item_id
        })
        return response.json()

    def remove_from_inventory(self, item_id):
        """Send API request to app.py to remove an item from the database."""
        response = requests.post("http://inventory:5001/inventory/remove", json={
            "player_id": self.player_id,
            "item_id": item_id
        })
        return response.json()

    def view_inventory_items(self):
        """Fetch player inventory from app.py"""
        response = requests.get(f"http://inventory:5001/inventory/{self.player_id}")
        return response.json()
        
        
