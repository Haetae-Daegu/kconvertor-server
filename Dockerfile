FROM python:3.10

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y postgresql-client && apt-get clean

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .
COPY migrations/ ./migrations/
COPY alembic.ini ./
COPY .env ./

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

EXPOSE 5000

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]