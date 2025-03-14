# Use official Python image
FROM python:3.12

# Set working directory inside the container
WORKDIR /app

# Copy the project-wide requirements file 
COPY requirements.txt /app/


# Install dependencies
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

# Copy only necessary files for the player microservice
COPY app.py /app/
COPY player.py /app/

# Expose Flask Port
EXPOSE 5000

# Set the command to run the player service
CMD ["python", "/app/app.py"]