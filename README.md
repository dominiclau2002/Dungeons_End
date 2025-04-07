# Dungeon's End
A microservices-based text adventure game where players navigate through a dungeon, fight enemies, collect items, and manage their inventory.

## Overview
Dungeon's End is built using a microservices architecture with services that communicate via REST APIs and asynchronous messaging through RabbitMQ. The game features:

- Room exploration with descriptions
- Turn-based combat system
- Inventory management
- Activity logging
- Score tracking

## Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop) — **must be running**
- [Docker Compose](https://docs.docker.com/compose/install/)
- [WAMP](https://www.wampserver.com/en/) or [MAMP](https://www.mamp.info/en/) if you're running on Windows/macOS — **must be started before the game**
- At least **4GB of available RAM**
- Open ports: `3307`, `5672`, `8080`, `15672`, `5000-5050`

## Setup and Installation

### 0. Start Required Services
Before doing anything else, **make sure these services are running**:

- 🐳 **Docker Desktop**
- **WAMP** (Windows) or **MAMP** (macOS) server (if applicable)

This ensures that the MySQL database and Docker containers will initialize correctly.

### 1. Clone the repository
```bash
git clone https://github.com/dominiclau2002/Dungeons_End.git
cd Dungeons_End
```
Make sure that the application folder is called **Dungeons_End** and not **Dungeons_End-main**

### 2. Start the application

From the project root directory, run:

```bash
docker-compose up -d
```

This command will:
- Build all necessary Docker images
- Create and start all containers
- Initialize the MySQL databases
- Set up RabbitMQ for messaging

The first run may take 5-10 minutes as it needs to build all the images.

### 3. Access the game

Once all services are running, navigate to:

```
http://localhost:5050
```

### 4. Login/Create a character

- Enter a name for your character
- Select a character class (Warrior, Rogue, Cleric, or Ranger)
- Click "BEGIN ADVENTURE"

## Database Information

The application uses MySQL for data storage. Default credentials:

- **Host**: localhost
- **Port**: 3307 (mapped from container port 3306)
- **Username**: user
- **Password**: password
- **Databases**: Multiple databases (player_db, item_db, enemy_db, etc.)

You can access phpMyAdmin at `http://localhost:8080` with these credentials to manage the databases.

## RabbitMQ Information

The application uses RabbitMQ for asynchronous messaging. Default credentials:

- **Host**: localhost
- **Port**: 5672 (AMQP), 15672 (Management UI)
- **Username**: guest
- **Password**: guest

You can access the RabbitMQ Management UI at `http://localhost:15672` to monitor message queues.

## Service Endpoints

The main services run on the following ports:

- **Web UI**: 5050
- **Player Service**: 5000
- **Inventory Service**: 5001
- **Item Service**: 5002
- **Enemy Service**: 5005
- **Room Service**: 5016
- **Activity Log Service**: 5013
- **Fight Enemy Service**: 5009
- **Enter Room Service**: 5011
- **Pick Up Item Service**: 5019
- **Manage Game Service**: 5014
- **Apply Item Effects Service**: 5025
- **Open Inventory Service**: 5010

## Game Controls

- **Enter Next Room**: Move to the next room in the dungeon
- **Inventory**: View your collected items
- **Stats**: View your character stats
- **Reset Game**: Reset your progress to the beginning
- **Logout**: End your session
- **Hard Reset**: Completely reset your game data (use with caution)
- **Activity Logs**: View the activity log for debugging

## Troubleshooting

### Services not starting properly

If some services fail to start:

1. Check container logs:
   ```bash
   docker-compose logs <service-name>
   ```

2. Restart a specific service:
   ```bash
   docker-compose restart <service-name>
   ```

3. Rebuild and restart all services:
   ```bash
   docker-compose down --remove-orphans
   docker-compose down
   docker-compose up --build -d
   ```

### Database issues

If you encounter database connection issues:

1. Ensure MySQL container is running:
   ```bash
   docker-compose ps mysql
   ```

2. Check MySQL logs:
   ```bash
   docker-compose logs mysql
   ```

3. Reset the database (this will erase all data):
   ```bash
   docker-compose down --remove-orphans
   docker-compose down -v
   docker-compose up -d
   ```

## Shutdown

To stop all services:

```bash
docker-compose down
```

To stop all services and remove all data (volumes):

```bash
docker-compose down -v
```

## Architecture

The application follows a microservices architecture:

### Atomic Services
- **player_service**: Manages player data (health, stats, etc.)
- **enemy_service**: Handles enemy information
- **item_service**: Manages item data
- **inventory_service**: Tracks player inventory
- **room_service**: Controls room descriptions and contents
- **activity_log_service**: Records player actions
- **score_service**: Tracks player scores

### Composite Services
- **entering_room_service**: Manages room entry logic
- **fight_enemy_service**: Manages combat between players and enemies
- **pick_up_item_service**: Handles item collection logic
- **apply_item_effects_service**: Processes special item effects
- **manage_game_service**: Provides game state management
- **open_inventory_service**: Manages inventory display and interactions
### Messaging System
- Uses RabbitMQ for asynchronous activity logging
- Messages are published to "activity_log_queue"

## Notes

- If you make code changes, rebuild the affected services:
  ```bash
  docker-compose down --remove-orphans
  docker-compose build <service-name>
  docker-compose up -d <service-name>
  ```

- The `docker-compose.yaml` file contains all configuration for the services and their dependencies.

- The game state is persisted in the MySQL database, so your progress will be saved even if you stop the containers.
