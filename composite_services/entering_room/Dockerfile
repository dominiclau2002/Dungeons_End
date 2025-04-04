#entering_room composite dockerfile
FROM python:3.12

WORKDIR /app
ENV PYTHONPATH=/app
# Copy service script
COPY composite_services/entering_room/app.py /app/app.py

COPY composite_services/entering_room/wait-for-it.sh /app/wait-for-it.sh
# Include shared logging module
COPY composite_services/utilities /app/composite_services/utilities


# Install dependencies (use the global `requirements.txt`)
COPY requirements.txt /app/

RUN apt-get update && apt-get install -y netcat-openbsd && apt-get clean && rm -rf /var/lib/apt/lists/*



RUN python -m pip install --no-cache-dir --timeout=120 -i https://pypi.org/simple -r /app/requirements.txt

# Add wait-for-it script permissions
RUN chmod +x /app/wait-for-it.sh

EXPOSE 5011

# Wait for MySQL before starting Flask
CMD ["/app/wait-for-it.sh", "mysql:3306", "--", "python", "app.py"]

