# atomic_services/activity_log/rabbitmq_consumer.py
import pika, json
from models import db, ActivityLog
from datetime import datetime
import logging
import time
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def consume_messages():
    # Add delay to ensure RabbitMQ is fully started
    logger.info("Waiting for RabbitMQ to be fully available...")
    time.sleep(10)
    
    rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    logger.info(f"Connecting to RabbitMQ at {rabbitmq_host}")
    
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
            channel = connection.channel()
            channel.queue_declare(queue='activity_log_queue', durable=True)
            
            logger.info("Connected to RabbitMQ, waiting for messages...")
            
            def callback(ch, method, properties, body):
                try:
                    logger.info(f"Received message: {body}")
                    data = json.loads(body)
                    player_id = data.get("player_id")
                    action = data.get("action")
                    timestamp = data.get("timestamp")
                    
                    if not player_id or not action:
                        logger.error("Message missing required fields (player_id, action)")
                        # Negative acknowledge, message will be requeued
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                        return
                    
                    if timestamp:
                        try:
                            timestamp = datetime.fromisoformat(timestamp)
                        except ValueError:
                            logger.warning(f"Invalid timestamp format: {timestamp}, using current time")
                            timestamp = datetime.utcnow()
                    else:
                        timestamp = datetime.utcnow()
                    
                    # Create new log entry
                    from app import app
                    with app.app_context():
                        new_log = ActivityLog(
                            PlayerID=player_id,
                            Action=action,
                            Timestamp=timestamp
                        )
                        db.session.add(new_log)
                        db.session.commit()
                        logger.info(f"Logged activity: {action} for player {player_id}")
                    
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Negative acknowledge, message will be requeued
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            
            # Only fetch one message at a time
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='activity_log_queue', on_message_callback=callback)
            
            # Start consuming
            channel.start_consuming()
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Connection to RabbitMQ failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error: {e}. Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    consume_messages()