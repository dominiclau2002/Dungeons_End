# Use official Python image
FROM python:3.12

# Set working directory inside the container
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt /app/
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

# Copy necessary files
COPY app.py /app/
COPY activity_log.py /app/

# Expose Flask port
EXPOSE 5013

# Start the activity log service
CMD ["python", "/app/app.py"]
