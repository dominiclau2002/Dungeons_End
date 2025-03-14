# Use official Python image
FROM python:3.12

# Set working directory inside the container
WORKDIR /app

# Copy the project-wide requirements file first
COPY ./requirements.txt /app/

# Install dependencies
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy only the necessary files for the inventory microservice
COPY ./atomic_services/inventory/app.py /app/
COPY ./atomic_services/inventory/inventory.py /app/

# Expose Flask port
EXPOSE 5001

# Set the command to run the inventory service
CMD ["python", "app.py"]
