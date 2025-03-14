# Use official Python image
FROM python:3.12

# Set working directory inside the container
WORKDIR /app

# Copy the project-wide requirements file first
COPY ./requirements.txt /app/

# Install dependencies
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy only the necessary files for the item microservice
COPY ./atomic_services/item/app.py /app/
COPY ./atomic_services/item/item.py /app/

# Expose Flask port
EXPOSE 5002

# Set the command to run the item service
CMD ["python", "app.py"]
