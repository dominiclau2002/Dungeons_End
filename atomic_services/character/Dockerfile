# character microservice dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 5003

CMD ["python", "app.py"]