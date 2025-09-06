# Order & Inventory API

A FastAPI-based e-commerce backend with PostgreSQL and Redis.

## Requirements

- Docker Desktop
- Python 3.11+
- pip

## Quick Start

```bash
# Clone repository
git clone <repository-url>
cd order-inventory-api

# Install Python dependencies
pip install -r requirements.txt

# Start application with Docker
docker-compose up --build

# Access API
# http://localhost:8000 - API
# http://localhost:8000/docs - Documentation
# http://localhost:8000/health - Health check