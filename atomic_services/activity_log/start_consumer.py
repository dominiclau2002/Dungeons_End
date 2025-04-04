# atomic_services/activity_log/start_consumer.py
import threading
import logging
from rabbitmq_consumer import consume_messages
from app import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Start the consumer in a separate thread
    logger.info("Starting RabbitMQ consumer thread...")
    consumer_thread = threading.Thread(target=consume_messages)
    consumer_thread.daemon = True
    consumer_thread.start()
    
    logger.info("Starting Flask app...")
    app.run(host="0.0.0.0", port=5013, debug=True)