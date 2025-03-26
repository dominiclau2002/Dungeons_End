-- Drop existing databases if they exist
DROP DATABASE IF EXISTS player_db;
DROP DATABASE IF EXISTS enemy_db;
DROP DATABASE IF EXISTS item_db;
DROP DATABASE IF EXISTS inventory_db;
DROP DATABASE IF EXISTS activity_log_db;
DROP DATABASE IF EXISTS score_db;
DROP DATABASE IF EXISTS calculator_db;
DROP DATABASE IF EXISTS room_db;

-- Create separate databases for microservices
CREATE DATABASE player_db;
CREATE DATABASE enemy_db;
CREATE DATABASE item_db;
CREATE DATABASE inventory_db;
CREATE DATABASE activity_log_db;
CREATE DATABASE calculator_db;
CREATE DATABASE score_db;
CREATE DATABASE room_db;

-- Grant permissions to the user for all databases
GRANT ALL PRIVILEGES ON player_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON enemy_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON item_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON inventory_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON activity_log_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON calculator_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON score_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON room_db.* TO 'user'@'%';
FLUSH PRIVILEGES;

-- ✅ Use `player_db`
USE player_db;
CREATE TABLE Player (
    PlayerID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(50) UNIQUE NOT NULL,
    CharacterClass ENUM('Warrior', 'Rogue', 'Cleric', 'Ranger') NOT NULL,
    Health INT NOT NULL DEFAULT 100,
    Damage INT NOT NULL DEFAULT 10,
    RoomID INT DEFAULT 1
);

-- ✅ Use `enemy_db`
USE enemy_db;
CREATE TABLE Enemy (
    EnemyID INT AUTO_INCREMENT PRIMARY KEY,
    -- RoomID INT UNIQUE NOT NULL,
    Description TEXT NOT NULL,
    Name VARCHAR(50) UNIQUE NOT NULL,
    Health INT NOT NULL,
    Damage INT NOT NULL, 
    Attack INT NOT NULL, -- Stores attacks in JSON format
    Points INT NOT NULL,
    Loot JSON DEFAULT NULL -- Stores loot as JSON
);

-- ✅ Use `item_db`
USE item_db;
CREATE TABLE Item (
    ItemID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(50) UNIQUE NOT NULL,
    Description VARCHAR(200) NOT NULL,
    Points INT NOT NULL
);

-- ✅ Use `inventory_db`
USE inventory_db;
CREATE TABLE Inventory (
    InventoryID INT AUTO_INCREMENT PRIMARY KEY,
    PlayerID INT NOT NULL,
    ItemID INT NOT NULL,
    FOREIGN KEY (PlayerID) REFERENCES player_db.Player(PlayerID),
    FOREIGN KEY (ItemID) REFERENCES item_db.Item(ItemID)
);

-- ✅ Use `activity_log_db`
USE activity_log_db;
CREATE TABLE ActivityLog (
    LogID INT AUTO_INCREMENT PRIMARY KEY,
    PlayerID INT NOT NULL,
    Action VARCHAR(255) NOT NULL,
    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ✅ Use `calculator_db`
USE score_db;
CREATE TABLE Score (
    ScoreID INT AUTO_INCREMENT PRIMARY KEY,
    PlayerID INT NOT NULL,
    Points INT NOT NULL,
    Reason ENUM('combat', 'item_collection') NOT NULL,
    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

USE room_db;
CREATE TABLE Room (
    RoomID INT AUTO_INCREMENT,
    Description VARCHAR(200),
    ItemIDs JSON,  -- Stores array of ItemIDs (e.g., [1, 2, 3])
    EnemyIDs JSON, -- Stores array of EnemyIDs (e.g., [1, 2, 3])
    DoorLocked BIT,
    PRIMARY KEY (RoomID)
);

-- ✅ Sample Data for Items
USE item_db;
INSERT INTO Item (Name, Description, Points) VALUES
('Golden Sword', 'A shiny golden sword with high damage', 100),
('Leather Armor', 'Basic protective armor', 50),
('Small Shield', 'A small wooden shield', 40),
('Health Potion', 'Restores 50 health', 30),
('Lockpick', 'Unlocks most doors', 40),
('Magic Amulet', 'Grants resistance to magic', 80);

-- Insert data into Enemy table
USE enemy_db; 
INSERT INTO Enemy (Name, Description, Health, Damage, Points)
VALUES
('Goblin', 'A small green creature with a dagger', 50, 10, 20),
('Orc Warrior', 'A strong orc with an axe', 100, 20, 50),
('Skeleton Archer', 'A skeleton with a bow', 70, 15, 35),
('Dark Mage', 'A powerful mage casting spells', 80, 25, 60),
('Troll', 'A large troll with regeneration', 150, 30, 90);

-- Insert data into Room table
USE room_db;
INSERT INTO Room (Description, ItemIDs, EnemyIDs, DoorLocked)
VALUES
('A dark room with a treasure chest', '[1, 2]', '[]', b'0'),
('A bright room with a fountain', '[3, 5]', '[1]', b'0'),
('A mysterious cave', '[4]', '[2]', b'1');


-- Insert data into Player table
USE player_db;
INSERT INTO Player (Name, Health, Damage, RoomID)
VALUES
('Player1', 100, 10, 1);

