# composite_services/utilities/activity_logger.py
import pika
import logging
import os
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# RabbitMQ configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
ACTIVITY_LOG_QUEUE = "activity_log_queue"

def log_activity(player_id, action):
    """
    Logs player activity by sending a message directly to RabbitMQ.
    
    Args:
        player_id (int): ID of the player performing the action
        action (str): Description of the action performed
        
    Returns:
        bool: True if logging was successful, False otherwise
    """
    if not player_id or not action:
        logger.error("Missing required parameters: player_id and action must be provided")
        return False
        
    try:
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        
        # Ensure the queue exists and is durable
        channel.queue_declare(queue=ACTIVITY_LOG_QUEUE, durable=True)
        
        # Create the message payload
        message = {
            "player_id": player_id,
            "action": action,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Publish the message to the queue
        channel.basic_publish(
            exchange='',
            routing_key=ACTIVITY_LOG_QUEUE,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2  # Make message persistent
            )
        )
        
        # Close the connection
        connection.close()
        logger.debug(f"Activity logged successfully via RabbitMQ: Player {player_id} - {action}")
        return True
        
    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error logging activity to RabbitMQ: {str(e)}")
        return False