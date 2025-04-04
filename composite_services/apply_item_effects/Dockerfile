FROM python:3.12

WORKDIR /app
ENV PYTHONPATH=/app

# Copy the current service's code
COPY composite_services/apply_item_effects/app.py /app/app.py

COPY composite_services/apply_item_effects/wait-for-it.sh /app/wait-for-it.sh
# Include shared logging module
COPY composite_services/utilities /app/composite_services/utilities

# Install dependencies
COPY requirements.txt /app/
RUN apt-get update && apt-get install -y netcat-openbsd && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

# Make wait-for-it executable
RUN chmod +x /app/wait-for-it.sh

EXPOSE 5025

CMD ["/app/wait-for-it.sh", "mysql:3306", "--", "python", "app.py"]

