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

## Prerequisites

- Python 3.x
- SQLite3
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd api_medium
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
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
- `HOST`: Server host
- `PORT`: Server port
- `WORKERS`: Number of Gunicorn workers
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `CSRF_TRUSTED_ORIGINS`: Comma-separated list of trusted origins for CSRF

## Running the Application

### Development Mode
```bash
python app.py
```

### Production Mode
```bash
gunicorn app:app --bind 0.0.0.0:5999 --workers 4
```

## API Endpoints

### Authentication Endpoints
- `POST /register`: Register a new user
- `POST /login`: User login
- `GET /logout`: User logout

### API Management
- `POST /generate-api`: Generate new API key
- `DELETE /delete-api/<api_key>`: Delete API key
- `GET /validate-username`: Validate Medium username
- `GET /test-api/<username>`: Test API functionality

### Feed Endpoints
- `GET /feed/<username>`: Get Medium RSS feed for a specific username

### System
- `GET /health`: Health check endpoint

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
