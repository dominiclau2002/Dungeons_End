FROM python:3.12

WORKDIR /app
ENV PYTHONPATH=/app

# Copy your actual web app files
COPY web/app.py /app/app.py
COPY web/templates /app/templates
COPY web/requirements.txt /app/requirements.txt

# Include shared logging utilities (if needed)
COPY composite_services/utilities /app/composite_services/utilities

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5050

CMD ["python", "app.py"]
