import unittest
from atomic_services.player import Player
from atomic_services.inventory import Inventory
from atomic_services.item import Item

class TestItem(unittest.TestCase):
    """Test cases for the Item class"""
    
    def test_item_creation(self):
        """Test that items can be created with correct attributes"""
        sword = Item("Sword", "Weapon")
        self.assertEqual(sword.name, "Sword")
        self.assertEqual(sword.item_type, "Weapon")
    
    def test_item_str_representation(self):
        """Test the string representation of an item"""
        potion = Item("Health Potion", "Consumable")
        self.assertEqual(str(potion), "Health Potion: (Consumable)")
    
    def test_item_repr_representation(self):
        """Test the repr representation of an item"""
        shield = Item("Shield", "Defense")
        self.assertEqual(repr(shield), "Item(name='Shield',type='Defense')")

class TestInventory(unittest.TestCase):
    """Test cases for the Inventory class"""
    
    def setUp(self):
        """Set up a fresh inventory for each test"""
        self.inventory = Inventory()
        # Create some test items
        self.sword = Item("Sword", "Weapon")
        self.potion = Item("Health Potion", "Consumable")
        self.armour = Item("Chainmail", "Armour")
    
    def test_inventory_creation(self):
        """Test that a new inventory is empty with correct capacity"""
        self.assertEqual(len(self.inventory.contents), 0)
        self.assertEqual(self.inventory.capacity, 10)
        self.assertEqual(self.inventory.name, "Your Inventory")
        
        # Test custom name
        custom_inv = Inventory("Backpack")
        self.assertEqual(custom_inv.name, "Backpack")
    
    def test_add_to_inventory(self):
        """Test adding items to inventory"""
        # Add a single item
        result = self.inventory.add_to_inventory(self.sword)
        self.assertEqual(result, {"message": "Sword added to inventory"})
        self.assertEqual(len(self.inventory.contents), 1)
        
        # Check the item is in contents
        self.assertIn(self.sword, self.inventory.contents)
    
    def test_inventory_capacity(self):
        """Test that inventory respects capacity limits"""
        # Fill inventory to capacity
        for i in range(10):
            item = Item(f"Item{i}", "Test")
            self.inventory.add_to_inventory(item)
        
        # Try to add one more item
        result = self.inventory.add_to_inventory(self.sword)
        self.assertEqual(result, {"error": "Your inventory is full!"})
        self.assertEqual(len(self.inventory.contents), 10)
    
    def test_remove_from_inventory(self):
        """Test removing items from inventory"""
        # Add items first
        self.inventory.add_to_inventory(self.sword)
        self.inventory.add_to_inventory(self.potion)
        
        # Remove an item
        result = self.inventory.remove_from_inventory("Sword")
        self.assertEqual(result, {"message": "Sword removed from inventory"})
        self.assertEqual(len(self.inventory.contents), 1)
        
        # Try to remove an item that doesn't exist
        result = self.inventory.remove_from_inventory("Nonexistent Item")
        self.assertEqual(result, {"error": "Error! Nonexistent Item not found in inventory!"})
    
    def test_view_inventory_items(self):
        """Test viewing inventory contents"""
        # Empty inventory
        result = self.inventory.view_inventory_items()
        self.assertEqual(result, {"message": "Your inventory is empty!"})
        
        # Add some items
        self.inventory.add_to_inventory(self.sword)
        self.inventory.add_to_inventory(self.potion)
        
        # Check inventory list
        result = self.inventory.view_inventory_items()
        self.assertEqual(result, {"inventory": ["Sword", "Health Potion"]})

class TestPlayer(unittest.TestCase):
    """Test cases for the Player class"""
    
    def setUp(self):
        """Set up a fresh player for each test"""
        self.player = Player("TestHero")
        # Create some test items
        self.sword = Item("Sword", "Weapon")
        self.potion = Item("Health Potion", "Consumable")
        self.armour = Item("Chainmail", "Armour")
        self.non_weapon = Item("Book", "Misc")
        self.non_armour = Item("Map", "Misc")
    
    def test_player_creation(self):
        """Test player creation with default and custom values"""
        # Test custom name
        self.assertEqual(self.player.name, "TestHero")
        self.assertEqual(self.player.health, 100)
        self.assertIsInstance(self.player.inventory, Inventory)
        
        # Test default name
        default_player = Player()
        self.assertEqual(default_player.name, "Unknown Hero")
    
    def test_player_stats(self):
        """Test that player has valid random stats"""
        # Check ranges for stats
        self.assertTrue(5 <= self.player.stats["strength"] <= 10)
        self.assertTrue(5 <= self.player.stats["agility"] <= 10)
        self.assertTrue(5 <= self.player.stats["intelligence"] <= 10)
    
    def test_get_player_info(self):
        """Test player info retrieval"""
        info = self.player.get_player_info()
        self.assertEqual(info["Player Name"], "TestHero")
        self.assertEqual(info["Current Health"], 100)
        self.assertEqual(info["Current Inventory"], "You have 0 items in your inventory.")
        self.assertEqual(info["Weapon"], "None")
        self.assertEqual(info["Armour"], "None")
    
    def test_health_management(self):
        """Test increasing and decreasing player health"""
        # Test health increase
        result = self.player.increase_health(20)
        self.assertEqual(result, {"message": "You regained 20 health. Health increased to 120."})
        self.assertEqual(self.player.health, 120)
        
        # Test health decrease
        result = self.player.decrease_health(30)
        self.assertEqual(result, {"message": "You took 30 damage. Health decreased to 90."})
        self.assertEqual(self.player.health, 90)
    
    def test_room_navigation(self):
        """Test room navigation messages"""
        # Test entering a room
        result = self.player.player_enters_room("Dungeon")
        self.assertEqual(result, {"message": "Player entered Dungeon."})
        
        # Test exiting a room
        result = self.player.player_exits_room("Dungeon")
        self.assertEqual(result, {"message": "Player exited Dungeon."})
    
    def test_equip_weapon(self):
        """Test weapon equipping mechanism"""
        # Try to equip a weapon not in inventory
        result = self.player.equip_weapon("Sword")
        self.assertEqual(result, {"error": "Sword not found in inventory."})
        
        # Add a weapon to inventory
        self.player.inventory.add_to_inventory(self.sword)
        
        # Successfully equip a weapon
        result = self.player.equip_weapon("Sword")
        self.assertEqual(result, {"message": "Sword equipped as weapon."})
        self.assertEqual(self.player.weapon, "Sword")

        # Try to equip a non-weapon item as a weapon
        self.player.inventory.add_to_inventory(self.non_weapon)
        result = self.player.equip_weapon("Book")
        self.assertEqual(result, {"error": "Book is not a weapon and cannot be equipped as one."})
    
    def test_equip_armour(self):
        """Test armour equipping mechanism"""
        # Try to equip armour not in inventory
        result = self.player.equip_armour("Chainmail")
        self.assertEqual(result, {"error": "Chainmail not found in inventory."})
        
        # Add armour to inventory
        self.player.inventory.add_to_inventory(self.armour)
        
        # Successfully equip armour
        result = self.player.equip_armour("Chainmail")
        self.assertEqual(result, {"message": "Chainmail equipped as armour."})
        self.assertEqual(self.player.armour, "Chainmail")

        # Try to equip a non-armour item as armour
        self.player.inventory.add_to_inventory(self.non_armour)
        result = self.player.equip_armour("Map")
        self.assertEqual(result, {"error": "Map is not armour and cannot be equipped as one."})
    
    def test_use_consumable(self):
        """Test using consumable items"""
        # Try to use a consumable not in inventory
        result = self.player.use_consumable("Health Potion")
        self.assertEqual(result, {"error": "Health Potion not found in inventory."})
        
        # Add a consumable to inventory
        self.player.inventory.add_to_inventory(self.potion)
        self.player.health = 80  # Set health to 80 to test health increase
        
        # Successfully use a consumable
        result = self.player.use_consumable("Health Potion")
        self.assertEqual(result, {"message": "Used Health Potion. Health increased to 100."})
        self.assertEqual(self.player.health, 100)
        
        # Check that the item was removed from inventory
        inventory_view = self.player.inventory.view_inventory_items()
        self.assertEqual(inventory_view, {"message": "Your inventory is empty!"})
        
        # Try to use a non-consumable item
        self.player.inventory.add_to_inventory(self.sword)
        result = self.player.use_consumable("Sword")
        self.assertEqual(result, {"error": "Sword is not a consumable item."})

    def test_inventory_integration(self):
        """Test that player inventory works correctly"""
        # Add items to player inventory
        self.player.inventory.add_to_inventory(self.sword)
        self.player.inventory.add_to_inventory(self.potion)
        
        # Check inventory through player
        info = self.player.get_player_info()
        self.assertEqual(info["Current Inventory"], "You have 2 items in your inventory.")

if __name__ == "__main__":
    unittest.main()