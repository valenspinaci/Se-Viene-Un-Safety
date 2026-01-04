# Deployment Guide

This application is containerized using Docker, allowing for easy deployment to any platform that supports Docker (e.g., Render, Railway, DigitalOcean, Heroku, AWS).

## Prerequisites
- [Docker](https://www.docker.com/) installed on your machine.

## Architecture
The application uses a "Single Container" approach:
1.  **Build Stage**: Node.js is used to build the React frontend into static files (`/dist`).
2.  **Runtime Stage**: Python (FastAPI) serves both the API endpoints and the static frontend files.

## Local Testing via Docker

1.  **Build the image**:
    ```bash
    docker build -t fastf1-exporter .
    ```

2.  **Run the container**:
    ```bash
    docker run -p 8000:8000 fastf1-exporter
    ```

3.  **Access the app**:
    Open [http://localhost:8000](http://localhost:8000)

## Deploying to Render.com (Example)

1.  Connect your GitHub repository to Render.
2.  Create a new **Web Service**.
3.  Select "Docker" as the environment.
4.  Render will automatically detect the `Dockerfile` and build it.
5.  **Important**: Ensure the internal port is set to `8000` in Render settings if it doesn't detect it automatically.
6.  Deploy!

## Deploying to Railway.app (Example)

1.  Connect your GitHub repository.
2.  Railway will detect the `Dockerfile`.
3.  It will build and deploy automatically.
4.  The default port `8000` exposed in the Dockerfile should be picked up.

## Manual / Self-Hosted
Simply run the Docker command above on your server. Ensure port 8000 is exposed to the internet or proxied via Nginx.
