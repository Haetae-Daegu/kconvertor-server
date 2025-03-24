# Kconvertor-server

Backend server of Korean Convertor project

Using [ExchangeRateAPI](https://www.exchangerate-api.com/)

## Run Locally

### 1. Go to the project directory

```bash
  cd app
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Dependencies are updated regularly, so you may need to update them:
```bash
pip install --upgrade -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file at the root of the project with the following variables:

```
FLASK_APP=app.py
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000
DATABASE_URL=postgresql://user:password@host/dbname
EXCHANGE_RATE_API_KEY=your_api_key
```

Replace the placeholder values with your actual configuration.

### 4. Setup the database

```bash
# Initialize Alembic (if not already done)
alembic init migrations

# Create a new migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 5. Start the server

```bash
  flask run
```

## Run with Docker

To run the application using Docker, follow these steps:

### 1. Build and run the Docker container

At the root of the project (where the `Dockerfile` is located), run the following command to build and start the Docker container:

```bash
docker build -t kconvertor-server .
docker run -p 5000:5000 kconvertor-server
```

### 2. Access the application

Once the Docker container is running, access the application by visiting `http://localhost:5000` in your browser.

## Run with Docker Compose

If you want to use `docker-compose` to manage your application and any dependencies (e.g., a PostgreSQL database), follow these steps:

### 1. Create the services using Docker Compose

Make sure you're in the root directory where the `docker-compose.yml` file is located, then run:

```bash
docker-compose up
```

This will start both the Flask application and the PostgreSQL database container.

### 2. Access the application

Once the services are running, access the application by visiting `http://localhost:5000` in your browser.

### 3. Stop the services

To stop the services, run:

```bash
docker-compose down
```

## Database Migrations with Alembic

This project uses Alembic for database migrations.

### Configuration

1. Create an `alembic.ini` file based on the provided template (don't commit this file)
2. Update the `sqlalchemy.url` in alembic.ini or use environment variables

### Common Commands

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply all pending migrations
alembic upgrade head

# Revert to a previous migration
alembic downgrade -1
```

## Environment Variables

- **`FLASK_APP`**: The main application file (e.g., `app.py`).
- **`FLASK_RUN_HOST`**: Set to `0.0.0.0` to allow external access.
- **`FLASK_RUN_PORT`**: Port for the application to run on, default is `5000`.
- **`DATABASE_URL`**: PostgreSQL connection string (e.g., `postgresql://user:password@host/dbname`).
- **`EXCHANGE_RATE_API_KEY`**: Your API key for the Exchange Rate API.