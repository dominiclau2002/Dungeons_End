import os
import logging
import pika
import json
from datetime import datetime
from flask import Flask, jsonify, request, render_template, send_from_directory
from models import db, ActivityLog

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+mysqlconnector://user:password@mysql/activity_log_db"
)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# RabbitMQ configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
ACTIVITY_LOG_QUEUE = "activity_log_queue"

db.init_app(app)

with app.app_context():
    db.create_all()

def send_to_rabbitmq(player_id, action):
    """
    Helper function to send messages to RabbitMQ
    """
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=ACTIVITY_LOG_QUEUE, durable=True)
        
        message = {
            "player_id": player_id,
            "action": action,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        channel.basic_publish(
            exchange='',
            routing_key=ACTIVITY_LOG_QUEUE,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        
        connection.close()
        logger.info(f"Message sent to RabbitMQ: Player {player_id} - {action}")
        return True
    except Exception as e:
        logger.error(f"Failed to send message to RabbitMQ: {str(e)}")
        return False

def create_log_entry(player_id, action):
    """
    Creates a log entry directly in the database
    """
    try:
        new_log = ActivityLog(
            PlayerID=player_id,
            Action=action
        )
        db.session.add(new_log)
        db.session.commit()
        logger.info(f"Created log entry directly: {new_log.to_dict()}")
        return new_log
    except Exception as e:
        logger.error(f"Failed to create log entry directly: {str(e)}")
        return None

# API to create a new log entry using RabbitMQ
@app.route("/api/log", methods=["POST"])
def log_activity():
    data = request.get_json()
    if not data or 'player_id' not in data or 'action' not in data:
        return jsonify({"error": "Missing required fields (player_id, action)"}), 400
    
    player_id = data['player_id']
    action = data['action']
    
    # First try to send to RabbitMQ
    rabbitmq_success = send_to_rabbitmq(player_id, action)
    
    # If RabbitMQ fails, create the log entry directly as a fallback
    if not rabbitmq_success:
        logger.warning("RabbitMQ send failed, creating log entry directly")
        log_entry = create_log_entry(player_id, action)
        if log_entry:
            return jsonify(log_entry.to_dict()), 201
        else:
            return jsonify({"error": "Failed to create log entry"}), 500
    
    return jsonify({
        "message": "Activity logged successfully",
        "player_id": player_id,
        "action": action,
        "timestamp": datetime.utcnow().isoformat()
    }), 201

# API to create a new log entry directly (legacy endpoint)
@app.route("/log", methods=["POST"])
def create_log():
    data = request.get_json()
    if not data or 'player_id' not in data or 'action' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    new_log = ActivityLog(
        PlayerID=data['player_id'],
        Action=data['action']
    )
    db.session.add(new_log)
    db.session.commit()
    
    logger.info(f"Created log entry: {new_log.to_dict()}")
    return jsonify(new_log.to_dict()), 201

# API to get logs by player ID
@app.route("/log/<int:player_id>", methods=["GET"])
def get_logs(player_id):
    logs = ActivityLog.query.filter_by(PlayerID=player_id).all()
    logger.info(f"Retrieved {len(logs)} logs for player {player_id}")
    return jsonify([log.to_dict() for log in logs]), 200

# API to get all logs with pagination
@app.route("/log", methods=["GET"])
def get_all_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    pagination = ActivityLog.query.order_by(ActivityLog.Timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    logs = pagination.items
    
    response = {
        "logs": [log.to_dict() for log in logs],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page
    }
    
    logger.info(f"Retrieved {len(logs)} logs (page {page}/{pagination.pages})")
    return jsonify(response), 200

# API to clear all logs
@app.route("/log", methods=["DELETE"])
def clear_logs():
    count = ActivityLog.query.count()
    ActivityLog.query.delete()
    db.session.commit()
    logger.info(f"Cleared {count} log entries")
    return jsonify({"message": f"Activity logs cleared! ({count} entries removed)"}), 200

# Simple HTML page to view logs
@app.route("/")
def log_viewer():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Activity Log Viewer</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            .log-table { width: 100%; border-collapse: collapse; }
            .log-table th, .log-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            .log-table th { background-color: #f2f2f2; }
            .log-table tr:nth-child(even) { background-color: #f9f9f9; }
            .controls { margin: 20px 0; }
            .btn { padding: 8px 16px; margin-right: 10px; cursor: pointer; }
            .filter { margin: 10px 0; }
        </style>
    </head>
    <body>
        <h1>Activity Log Viewer</h1>
        
        <div class="controls">
            <button class="btn" onclick="refreshLogs()">Refresh</button>
            <button class="btn" onclick="clearLogs()">Clear All Logs</button>
        </div>
        
        <div class="filter">
            <label for="player-id">Filter by Player ID:</label>
            <input type="number" id="player-id" value="1">
            <button onclick="filterByPlayer()">Filter</button>
            <button onclick="resetFilter()">Show All</button>
        </div>
        
        <table class="log-table">
            <thead>
                <tr>
                    <th>Log ID</th>
                    <th>Player ID</th>
                    <th>Action</th>
                    <th>Timestamp</th>
                </tr>
            </thead>
            <tbody id="logs-container">
                <tr><td colspan="4">Loading logs...</td></tr>
            </tbody>
        </table>
        
        <script>
            let currentFilter = null;
            
            // Load logs when page loads
            window.onload = function() {
                loadLogs();
            };
            
            function loadLogs() {
                let url = '/log';
                if (currentFilter) {
                    url = `/log/${currentFilter}`;
                }
                
                fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        const logsContainer = document.getElementById('logs-container');
                        logsContainer.innerHTML = '';
                        
                        // Handle both array response and paginated response
                        const logs = Array.isArray(data) ? data : (data.logs || []);
                        
                        if (logs.length === 0) {
                            logsContainer.innerHTML = '<tr><td colspan="4" style="text-align:center">No logs found</td></tr>';
                            return;
                        }
                        
                        logs.forEach(log => {
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td>${log.log_id}</td>
                                <td>${log.player_id}</td>
                                <td>${log.action}</td>
                                <td>${log.timestamp}</td>
                            `;
                            logsContainer.appendChild(row);
                        });
                    })
                    .catch(error => {
                        console.error('Error fetching logs:', error);
                        document.getElementById('logs-container').innerHTML = 
                            '<tr><td colspan="4" style="text-align:center;color:red;">Failed to load logs</td></tr>';
                    });
            }
            
            function refreshLogs() {
                loadLogs();
            }
            
            function clearLogs() {
                if (confirm('Are you sure you want to clear all logs? This cannot be undone.')) {
                    fetch('/log', { method: 'DELETE' })
                        .then(response => response.json())
                        .then(data => {
                            alert(data.message);
                            loadLogs();
                        })
                        .catch(error => {
                            console.error('Error clearing logs:', error);
                            alert('Error clearing logs');
                        });
                }
            }
            
            function filterByPlayer() {
                const playerId = document.getElementById('player-id').value;
                if (!playerId) {
                    alert('Please enter a player ID');
                    return;
                }
                
                currentFilter = playerId;
                loadLogs();
            }
            
            function resetFilter() {
                currentFilter = null;
                loadLogs();
            }
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5013, debug=True)