#activitylog dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 5013

# Run app.py and RabbitMQ consumer at the same time
CMD ["sh", "-c", "python rabbitmq_consumer.py & python app.py"]
