import pika, json
from models import db, ActivityLog
from datetime import datetime
from app import app

def consume_messages():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='activity_log_queue', durable=True)

    def callback(ch, method, properties, body):
        data = json.loads(body)
        player_id = data["player_id"]
        action = data["action"]
        timestamp = datetime.fromisoformat(data["timestamp"])

        with app.app_context():
            new_log = ActivityLog(player_id=player_id, action=action, timestamp=timestamp)
            db.session.add(new_log)
            db.session.commit()
            print("Logged activity:", action)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue='activity_log_queue', on_message_callback=callback, auto_ack=False)

    print("Waiting for messages...")
    channel.start_consuming()
