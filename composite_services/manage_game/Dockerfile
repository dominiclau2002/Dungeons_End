FROM python:3.12

WORKDIR /app
ENV PYTHONPATH=/app

# Copy service files
COPY composite_services/manage_game/app.py /app/app.py

# Explicitly ensure wait-for-it is copied
COPY composite_services/manage_game/wait-for-it.sh /app/wait-for-it.sh

# Include shared logging module
COPY composite_services/utilities /app/composite_services/utilities

COPY requirements.txt /app/
RUN apt-get update && apt-get install -y netcat-openbsd && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-cache-dir --timeout=120 -i https://pypi.org/simple -r /app/requirements.txt

RUN chmod +x /app/wait-for-it.sh

EXPOSE 5014

CMD ["/app/wait-for-it.sh", "mysql:3306", "--", "python", "app.py"]

