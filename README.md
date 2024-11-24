
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
pip install
pip update
```

### 3. Start the server

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

## Environment Variables

- **`FLASK_APP`**: The main application file (e.g., `app.py`).
- **`FLASK_RUN_HOST`**: Set to `0.0.0.0` to allow external access.
- **`FLASK_RUN_PORT`**: Port for the application to run on, default is `5000`.

