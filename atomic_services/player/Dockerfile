# Use official Python image
FROM python:3.12

# Set working directory inside the container
WORKDIR /app

# Copy the project-wide requirements file 
COPY ./requirements.txt /app/

# Install dependencies
RUN python -m pip install --no-cache-dir -r requirements.txt

#Copy the necessary files for player microservice
COPY ./atomic_services/player/app.py /app/
COPY ./atomic_services/player/player.py /app/

#Expose Flask Port
EXPOSE 5000

# Set the command to run the player service
CMD ["python", "app.py"]
