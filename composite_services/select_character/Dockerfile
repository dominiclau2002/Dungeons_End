#Select_character composite dockerfile
FROM python:3.12

WORKDIR /app

# Copy service script
COPY . /app/

# Install dependencies (use the global `requirements.txt`)
COPY ../../requirements.txt /app/

RUN python -m pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 5017

CMD ["python", "/app/<service_name>.py"]  # Replace <service_name>.py