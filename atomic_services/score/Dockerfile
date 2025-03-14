# Use Python official image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy files
COPY app.py score.py requirements.txt ./

# Install dependencies
RUN pip install -r requirements.txt

# Expose port
EXPOSE 5008

# Run the Flask app
CMD ["python", "app.py"]
