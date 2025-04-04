# atomic_services/activity_log/test_sending_logs.py
import pika
import json
from datetime import datetime
import logging
import time
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_test_log(player_id, action):
    """
    Send a test log message to RabbitMQ
    """
    try:
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()
        
        # Ensure queue exists
        channel.queue_declare(queue='activity_log_queue', durable=True)
        
        # Create message
        message = {
            "player_id": player_id,
            "action": action,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send message
        channel.basic_publish(
            exchange='',
            routing_key='activity_log_queue',
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
        )
        
        logger.info(f"Sent message: {message}")
        connection.close()
        return True
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return False

def main():
    # Number of test logs to send
    num_logs = 5
    if len(sys.argv) > 1:
        try:
            num_logs = int(sys.argv[1])
        except ValueError:
            logger.warning(f"Invalid number of logs specified: {sys.argv[1]}. Using default of 5.")
    
    player_id = 1
    
    logger.info(f"Sending {num_logs} test messages to RabbitMQ...")
    
    for i in range(num_logs):
        action = f"Test log message #{i+1} sent at {datetime.utcnow().isoformat()}"
        success = send_test_log(player_id, action)
        
        if success:
            logger.info(f"Successfully sent test log {i+1}/{num_logs}")
        else:
            logger.error(f"Failed to send test log {i+1}/{num_logs}")
        
        # Small delay to avoid flooding
        time.sleep(0.5)
    
    logger.info("Test complete! You can check for these messages in the activity log database.")
    logger.info("Visit http://localhost:5013 to view the logs in the browser.")

if __name__ == "__main__":
    main()