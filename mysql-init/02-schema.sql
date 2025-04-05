-- ✅ Use `player_db`
USE player_db;
CREATE TABLE Player (
    PlayerID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(50) UNIQUE NOT NULL,
    CharacterClass ENUM('Warrior', 'Rogue', 'Cleric', 'Ranger') NOT NULL,
    Health INT NOT NULL DEFAULT 100,
    Damage INT NOT NULL DEFAULT 10,
    RoomID INT DEFAULT 0
);

-- ✅ Use `enemy_db`
USE enemy_db;
CREATE TABLE Enemy (
    EnemyID INT AUTO_INCREMENT PRIMARY KEY,
    Description TEXT NOT NULL,
    Name VARCHAR(50) UNIQUE NOT NULL,
    Health INT NOT NULL,
    Damage INT NOT NULL, 
    Attack INT NOT NULL,
    Loot JSON DEFAULT NULL
);

-- ✅ Use `item_db`
USE item_db;
CREATE TABLE Item (
    ItemID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(50) UNIQUE NOT NULL,
    Description VARCHAR(200) NOT NULL
);

-- ✅ Use `inventory_db`
USE inventory_db;
CREATE TABLE Inventory (
    PlayerID INT NOT NULL,
    ItemID INT NOT NULL,
    PRIMARY KEY (PlayerID, ItemID)
);

-- ✅ Use `activity_log_db`
USE activity_log_db;
DROP TABLE IF EXISTS ActivityLog;
CREATE TABLE ActivityLog (
    LogID INT AUTO_INCREMENT PRIMARY KEY,
    PlayerID INT NOT NULL,
    Action VARCHAR(255) NOT NULL,
    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);


-- ✅ Use `score_db`
USE score_db;
CREATE TABLE Score (
    ScoreID INT AUTO_INCREMENT PRIMARY KEY,
    Points INT NOT NULL,
    Reason ENUM('enemy_defeat', 'item_pickup', 'enter_room') NOT NULL,
    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ✅ Use `room_db`
USE room_db;
CREATE TABLE Room (
    RoomID INT AUTO_INCREMENT,
    Description VARCHAR(200),
    ItemIDs JSON,
    EnemyIDs JSON,
    DoorLocked BOOLEAN,
    PRIMARY KEY (RoomID)
);

-- ✅ Sample Data for Items
USE item_db;
INSERT INTO Item (Name, Description) VALUES
('Golden Sword', 'A shiny golden sword with high damage'),
('Leather Armor', 'Basic protective armor'),
('Small Shield', 'A small wooden shield'),
('Seaweed', 'Smells like seaweed'),
('Lockpick', 'Unlocks most doors'),
('Magic Amulet', 'Grants resistance to magic');

-- Insert data into Enemy table
USE enemy_db; 
INSERT INTO Enemy (Name, Description, Health, Damage, Attack)
VALUES
('Goblin', 'A small green creature with a dagger', 50, 10, 1),
('Orc Warrior', 'A strong orc with an axe', 100, 20, 1),
('Skeleton Archer', 'A skeleton with a bow', 70, 15, 1),
('Dark Mage', 'A powerful mage casting spells', 80, 25, 1),
('Troll', 'A large troll with regeneration', 150, 30, 1);

-- Insert data into Room table
USE room_db;
INSERT INTO Room (Description, ItemIDs, EnemyIDs, DoorLocked)
VALUES
('A dark chamber with stone walls covered in ancient runes. A weathered treasure chest sits in the corner, its lock gleaming in the dim torchlight. There is a door to the north that beckons you forward.', '[1, 2]', '[]', FALSE),
('A sun-drenched room with a marble fountain at its center, water sparkling as it cascades down. Colorful tapestries adorn the walls depicting epic battles. There are doors to the south and east.', '[3, 5]', '[1]', FALSE),
('A mysterious cave with stalactites hanging from the ceiling, dripping water creating eerie echoes. Glowing mushrooms provide faint blue light. A heavy iron door to the west appears to be locked.', '[4]', '[2]', TRUE);

-- Insert data into Player table
USE player_db;
INSERT INTO Player (Name, CharacterClass, Health, Damage, RoomID)
VALUES
('Player1', 'Warrior', 200, 10, 0);

-- Insert sample score data
USE score_db;
INSERT INTO Score (Points, Reason) VALUES
(200, 'enemy_defeat'),
(150, 'item_pickup'),
(100, 'enter_room'); 