#open_inventory composite dockerfile
FROM python:3.12

WORKDIR /app

# Copy service script
COPY . /app/

# Copy necessary files
COPY . .

# Install dependencies (use the global `requirements.txt`)
COPY ./requirements.txt /app/

RUN apt-get update && apt-get install -y netcat-openbsd && apt-get clean && rm -rf /var/lib/apt/lists/*



RUN python -m pip install --no-cache-dir --timeout=120 -i https://pypi.org/simple -r /app/requirements.txt

# Add wait-for-it script permissions
RUN chmod +x /app/wait-for-it.sh

EXPOSE 5010

# Wait for MySQL before starting Flask
CMD ["/app/wait-for-it.sh", "mysql:3306", "--", "python", "-m", "app"]