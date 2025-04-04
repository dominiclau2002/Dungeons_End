#activity_log dockerfile
FROM python:3.12

WORKDIR /app

# Copy necessary files
COPY . .

# Install dependencies
RUN apt-get update && apt-get install -y netcat-openbsd && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-cache-dir --timeout=120 -i https://pypi.org/simple -r requirements.txt

# Add wait-for-it script permissions
RUN chmod +x wait-for-it.sh

# Expose Flask port
EXPOSE 5013

# Wait for MySQL and RabbitMQ before starting
CMD ["./wait-for-it.sh", "mysql:3306", "--", "./wait-for-it.sh", "rabbitmq:5672", "--", "python", "start_consumer.py"]