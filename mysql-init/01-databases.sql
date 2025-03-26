-- Drop existing databases if they exist
DROP DATABASE IF EXISTS player_db;
DROP DATABASE IF EXISTS enemy_db;
DROP DATABASE IF EXISTS item_db;
DROP DATABASE IF EXISTS inventory_db;
DROP DATABASE IF EXISTS activity_log_db;
DROP DATABASE IF EXISTS score_db;
DROP DATABASE IF EXISTS calculator_db;
DROP DATABASE IF EXISTS room_db;
DROP DATABASE IF EXISTS character_db;

-- Create separate databases for microservices
CREATE DATABASE player_db;
CREATE DATABASE enemy_db;
CREATE DATABASE item_db;
CREATE DATABASE inventory_db;
CREATE DATABASE activity_log_db;
CREATE DATABASE calculator_db;
CREATE DATABASE score_db;
CREATE DATABASE room_db;
CREATE DATABASE character_db;

-- Grant permissions to the user for all databases
CREATE USER IF NOT EXISTS 'user'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON player_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON enemy_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON item_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON inventory_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON activity_log_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON calculator_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON score_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON room_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON character_db.* TO 'user'@'%';
FLUSH PRIVILEGES; 