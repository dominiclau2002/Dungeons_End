#atomic_services\inventory\Dockerfile

FROM python:3.12

# Set working directory inside the container
WORKDIR /app

# Copy the project-wide requirements file 
COPY ./atomic_services/inventory/app.py /app/
COPY ./atomic_services/inventory/inventory.py /app/
COPY ./requirements.txt /app/

# Install dependencies
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy inventory-specific files into the container
COPY . .

# Set the command to run the inventory service
CMD ["python", "app.py"]
