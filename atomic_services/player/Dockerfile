# Use official Python image
FROM python:3.12

# Set working directory inside the container
WORKDIR /app

# Copy the project-wide requirements file 
COPY ./atomic_services/player/app.py /app/
COPY ./atomic_services/player/player.py /app/
COPY ./requirements.txt /app/

# Install dependencies
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy player-specific files into the container
COPY . .

# Set the command to run the player service
CMD ["python", "app.py"]
