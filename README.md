# Medium API Integration

A Flask-based web application that provides a secure API interface for fetching Medium blog posts. This application allows users to register, generate API keys, and fetch Medium RSS feeds through a RESTful API.

## Features

- User authentication (register/login)
- Secure API key generation and management
- Medium RSS feed integration
- CSRF protection
- CORS support
- Health check endpoint
- Environment-based configuration
- **Optimized dependency management with `uv`**
- **Production-ready deployment with `Uvicorn`**
- **Containerized deployment with Docker**

## Prerequisites

- Python 3.10+
- Docker (for containerized deployment)

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd API-Medium-Free
```

2. **Install `uv` (if you don't have it):**
   `uv` is a fast Python package installer and resolver.
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # Or using pipx: pipx install uv
   ```
   Ensure `uv` is in your PATH.

3. **Install Python dependencies:**
   ```bash
   uv pip install .
   ```

4. Set up environment variables:
```bash
cp .env.example .env
```
Edit the `.env` file with your configuration.

## Configuration

The application can be configured using environment variables in the `.env` file:

### Required Environment Variables:
- `SECRET_KEY`: Flask secret key for session management
- `FLASK_ENV`: Application environment (development/production)
- `DEBUG`: Enable/disable debug mode
- `HOST`: Server host (e.g., `0.0.0.0` for Docker)
- `PORT`: Server port (e.g., `9999`)
- `WORKERS`: Number of Uvicorn workers
- `TIMEOUT`: Uvicorn timeout (in seconds)
- `LOG_LEVEL`: Uvicorn log level (e.g., `info`, `debug`)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `CSRF_TRUSTED_ORIGINS`: Comma-separated list of trusted origins for CSRF
- `CSRF_COOKIE_SECURE`: Set to `True` for HTTPS
- `CSRF_COOKIE_HTTPONLY`: Set to `True` for HTTP-only cookies
- `SESSION_COOKIE_SECURE`: Set to `True` for HTTPS
- `WTF_CSRF_TIME_LIMIT`: CSRF token expiration time in seconds
- `WTF_CSRF_SSL_STRICT`: Set to `True` for strict SSL checking on CSRF

## Running the Application

### Development Mode (using `uv` and Flask's development server)
```bash
uv run flask run --host=0.0.0.0 --port=9999
```

### Production Mode (using `uv` and `Uvicorn`)
```bash
uv run uvicorn app:app --host 0.0.0.0 --port 8060 --workers 4 --timeout-keep-alive 60 --log-level info
```
*(Note: Adjust host, port, workers, timeout, and log level as needed.)*

### Docker Usage

You can build and run the application using Docker:

1.  **Build the Docker image:**
    ```bash
    docker build -t medium-api-service .
    ```
2.  **Run the Docker container:**
    ```bash
    docker run -p 8060:8060 medium-api-service
    ```
    *(Note: Adjust port mapping `-p host_port:container_port` as needed.)*

3.  **Using Docker Compose (recommended for local development):**
    ```bash
    docker-compose up --build
    ```
    This will build the image and start the service as defined in `docker-compose.yml`.

## API Endpoints

### Authentication Endpoints
- `POST /register`: Register a new user
- `POST /login`: User login
- `GET /logout`: User logout

### API Management
- `POST /generate-api`: Generate new API key
- `POST /delete-api/<api_key>`: Delete API key
- `POST /validate-username`: Validate Medium username
- `GET /test-api/<username>`: Test API functionality

### Feed Endpoints
- `GET /api/medium/<username>`: Get Medium RSS feed for a specific username (requires `api_key` query parameter)

### System
- `GET /health`: Health check endpoint

## Automated Builds with GitHub Actions & Docker Hub

This project can be configured for automated Docker image builds and pushes to Docker Hub using GitHub Actions.

1.  **Create a Docker Hub Repository:**
    *   Log in to [Docker Hub](https://hub.docker.com/).
    *   Create a new public or private repository (e.g., `your-dockerhub-username/medium-api-service`).

2.  **Set up GitHub Secrets:**
    *   In your GitHub repository, go to `Settings` > `Secrets and variables` > `Actions`.
    *   Click `New repository secret`.
    *   Add the following secrets:
        *   `DOCKER_USERNAME`: Your Docker Hub username.
        *   `DOCKER_PASSWORD`: Your Docker Hub Access Token (recommended over password for security). You can generate an access token in Docker Hub `Account Settings` > `Security` > `New Access Token`.

3.  **Create GitHub Actions Workflow:**
    *   Create a file named `.github/workflows/docker-image.yml` in your repository.
    *   Add the following content to the file:

    ```yaml
    name: Docker Image CI

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  build_and_push:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Log in to Docker Hub
      uses: docker/login-action@v3
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}

    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: ${{ secrets.DOCKER_USERNAME }}/medium-api-service:latest
    ```

    *   Replace `your-dockerhub-username/medium-api-service` with your actual Docker Hub repository path.
    *   This workflow will automatically build and push a new Docker image to Docker Hub whenever changes are pushed to the `main` branch.

## Security Features

- CSRF Protection
- Secure session management
- API key authentication
- Password hashing
- CORS configuration
- HTTP-only cookies
- SSL/TLS ready

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.