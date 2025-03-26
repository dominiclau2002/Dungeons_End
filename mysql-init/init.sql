-- Drop databases if they exist
DROP DATABASE IF EXISTS player_db;
DROP DATABASE IF EXISTS room_db;
DROP DATABASE IF EXISTS character_db;
DROP DATABASE IF EXISTS enemy_db;
DROP DATABASE IF EXISTS item_db;
DROP DATABASE IF EXISTS inventory_db;
DROP DATABASE IF EXISTS score_db;
DROP DATABASE IF EXISTS activity_log_db;

-- Create all your service databases
CREATE DATABASE IF NOT EXISTS player_db;
CREATE DATABASE IF NOT EXISTS room_db;
CREATE DATABASE IF NOT EXISTS character_db;
CREATE DATABASE IF NOT EXISTS enemy_db;
CREATE DATABASE IF NOT EXISTS item_db;
CREATE DATABASE IF NOT EXISTS inventory_db;
CREATE DATABASE IF NOT EXISTS score_db;
CREATE DATABASE IF NOT EXISTS activity_log_db;

-- Grant permissions to 'user'@'%'
GRANT ALL PRIVILEGES ON player_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON room_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON character_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON enemy_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON item_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON inventory_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON score_db.* TO 'user'@'%';
GRANT ALL PRIVILEGES ON activity_log_db.* TO 'user'@'%';
