import requests

BASE_URL_PLAYER = "http://localhost:5000"
BASE_URL_INVENTORY = "http://localhost:5001"
BASE_URL_ITEM = "http://localhost:5002"

# Test Item Service
print("Creating an item...")
item_data = {"id": 1, "name": "Sword", "item_type": "Weapon"}
response = requests.post(f"{BASE_URL_ITEM}/item", json=item_data)
print(response.json())

# Test Inventory Service
print("\nChecking empty inventory...")
response = requests.get(f"{BASE_URL_INVENTORY}/inventory")
print(response.json())

print("\nAdding item to inventory...")
response = requests.post(f"{BASE_URL_INVENTORY}/inventory/add", json=item_data)
print(response.json())

print("\nChecking inventory again...")
response = requests.get(f"{BASE_URL_INVENTORY}/inventory")
print(response.json())

# Test Player Service
print("\nCreating player...")
response = requests.get(f"{BASE_URL_PLAYER}/player")
print(response.json())

print("\nEquipping weapon...")
response = requests.post(f"{BASE_URL_PLAYER}/equip_weapon", json={"id": 1})
print(response.json())

print("\nRemoving item from inventory...")
response = requests.post(f"{BASE_URL_INVENTORY}/remove", json={"id": 1})
print(response.json())

print("\nFinal inventory state...")
response = requests.get(f"{BASE_URL_INVENTORY}/inventory")
print(response.json())
