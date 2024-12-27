# PharmaInsights

A data pipeline and API service for fetching, processing, and searching clinical trial data from ClinicalTrials.gov.

## Features

- ETL pipeline for clinical trials data using Celery
- FastAPI-based REST API with OAuth2 authentication
- Full-text search capabilities using Elasticsearch
- Data persistence with PostgreSQL
- Asynchronous task processing with Redis and Celery

## Tech Stack

- **Python 3.12+**
- **FastAPI** - Modern web framework for building APIs
- **PostgreSQL** - Primary database for storing structured data
- **Elasticsearch** - Search engine for efficient querying of clinical trials
- **Redis** - Message broker for Celery tasks
- **Celery** - Distributed task queue
- **SQLAlchemy** - SQL toolkit and ORM
- **JWT** - Token-based authentication

## Prerequisites

- Python 3.12 or higher
- PostgreSQL 14 or higher
- Elasticsearch 7.17.0
- Redis 6.0+

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd pharma_insights
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up PostgreSQL:
   ```sql
   CREATE USER "user" WITH PASSWORD 'password';
   CREATE DATABASE pharma_db;
   GRANT ALL PRIVILEGES ON DATABASE pharma_db TO "user";
   \c pharma_db
   GRANT ALL ON SCHEMA public TO "user";
   ```

5. Start services:
   - Ensure PostgreSQL service is running
   - Start Elasticsearch
   - Start Redis server

## Configuration

Create environment variables or update the configuration in the code:

```python
# Database configuration
DATABASE_URL = "postgresql://user:password@localhost:5432/pharma_db"

# Elasticsearch configuration
ELASTICSEARCH_URL = "http://localhost:9200"

# Redis configuration
REDIS_URL = "redis://localhost:6379/0"

# JWT configuration
SECRET_KEY = "your-secret-key-here"
```

## Running the Application

1. Start the FastAPI server:
   ```bash
   uvicorn api:app --reload --port 8000
   ```

2. Start the Celery worker:
   ```bash
   celery -A etl_pipeline:celery_app worker --pool=solo --loglevel=info
   ```

## API Endpoints

### Authentication
- `POST /token` - Get JWT token

### Pipeline Operations
- `POST /pipeline/trigger` - Trigger ETL pipeline for clinical trials
- `GET /pipeline/status/{task_id}` - Check pipeline task status

### Search Operations
- `POST /search/trials` - Search clinical trials
- `GET /trials/comparison` - Compare multiple trials

## Usage Examples

1. Get authentication token:
```bash
curl -X POST "http://localhost:8000/token" \
     -F "username=test_user" \
     -F "password=password"
```

2. Trigger data pipeline:
```bash
curl -X POST "http://localhost:8000/pipeline/trigger?condition=breast%20cancer" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json"
```

3. Search trials:
```bash
curl -X POST "http://localhost:8000/search/trials?query=breast%20cancer%20phase%203" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json"
```

## Error Handling

The application includes comprehensive error handling:
- Authentication errors (401)
- Not found errors (404)
- Internal server errors (500)
- Custom error messages for pipeline failures

## Development

For local development:
1. Use the `--reload` flag with uvicorn
2. Set log level to debug for more detailed output
3. Use the Swagger UI at `http://localhost:8000/docs`

## Docker Deployment

Use the provided docker-compose file:

```bash
docker compose up -d
```

This will start all required services:
- FastAPI application
- Celery worker
- PostgreSQL
- Elasticsearch
- Redis

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact
mail: kale.rahulc@gmail.com

[Insert Contact Information]
