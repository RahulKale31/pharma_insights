# PharmaInsights

A scalable data pipeline and search platform for pharmaceutical data analysis.

## Features
- ETL pipeline for clinical trials data
- FastAPI backend with authentication
- Elasticsearch for efficient searching
- Distributed task processing with Celery
- Docker containerization

## Setup
1. Clone the repository:
\\\ash
git clone https://github.com/YOUR_USERNAME/pharma_insights.git
cd pharma_insights
\\\

2. Start the services:
\\\ash
docker-compose up --build
\\\

## Services
- FastAPI: http://localhost:8000
- Elasticsearch: http://localhost:9200
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## API Documentation
Access the API documentation at http://localhost:8000/docs
