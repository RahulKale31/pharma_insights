from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from elasticsearch import Elasticsearch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import List, Optional
import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="PharmaInsights API")

# Secret key for JWT
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY environment variable set")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database and Elasticsearch setup
engine = create_engine('postgresql://user:password@postgres:5432/pharma_db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# es = Elasticsearch(['http://elasticsearch:9200']) #use when docker
es = Elasticsearch(['http://localhost:9200']) #use when local

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Mock user for demonstration (in production, use database)
DEMO_USER = {
    "username": "demo",
    "password": "demo123",  # In production, use hashed passwords
}

class Token(BaseModel):
    access_token: str
    token_type: str

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Check credentials (mock authentication)
    if form_data.username == DEMO_USER["username"] and form_data.password == DEMO_USER["password"]:
        access_token = create_access_token(data={"sub": form_data.username})
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(
        status_code=401,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return {"username": username}
    except jwt.PyJWTError:
        raise credentials_exception

# API Endpoints
@app.post("/search/trials")
async def search_trials(
    query: str,
    filters: Optional[dict] = None,
    current_user: dict = Depends(get_current_user)
):
    """Search clinical trials using natural language query"""
    try:
        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title", "condition", "sponsor"]
                }
            }
        }
        
        if filters:
            search_body["query"] = {
                "bool": {
                    "must": [search_body["query"]],
                    "filter": [{"term": {k: v}} for k, v in filters.items()]
                }
            }
        
        results = es.search(
            index="trials_index",
            body=search_body,
            size=20
        )
        
        return {
            "total": results["hits"]["total"]["value"],
            "results": [hit["_source"] for hit in results["hits"]["hits"]]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trials/comparison")
async def compare_trials(
    trial_ids: List[str],
    current_user: dict = Depends(get_current_user)
):
    """Generate comparison table for selected trials"""
    db = SessionLocal()
    try:
        query = """
            SELECT *
            FROM clinical_trials
            WHERE trial_id = ANY(:trial_ids)
        """
        result = db.execute(query, {"trial_ids": trial_ids})
        trials = result.fetchall()
        
        comparison = {
            "trials": [dict(trial) for trial in trials],
            "generated_at": datetime.now()
        }
        
        return comparison
    finally:
        db.close()

@app.post("/pipeline/trigger")
async def trigger_pipeline(
    condition: str,  # This makes it a query parameter
    current_user: dict = Depends(get_current_user)
):
    """Trigger ETL pipeline for a specific condition"""
    from etl_pipeline import process_condition
    
    task = process_condition.delay(condition)
    return {"task_id": task.id}

@app.get("/pipeline/status/{task_id}")
async def get_pipeline_status(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Check status of pipeline execution"""
    from etl_pipeline import celery_app  # Import celery_app instead of pipeline
    
    task = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
