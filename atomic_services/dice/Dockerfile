# Use Python official image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy files
COPY app.py dice.py requirements.txt ./

# Install dependencies
RUN pip install -r requirements.txt

# Expose port
EXPOSE 5007

# Run the Flask app
CMD ["python", "app.py"]
