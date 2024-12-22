from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from elasticsearch import Elasticsearch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import List, Optional
import jwt
from datetime import datetime, timedelta

app = FastAPI(title="PharmaInsights API")

# Database and Elasticsearch setup
engine = create_engine('postgresql://user:password@localhost:5432/pharma_db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
es = Elasticsearch(['http://localhost:9200'])

# Authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = "your-secret-key"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid authentication")

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
    condition: str,
    current_user: dict = Depends(get_current_user)
):
    """Trigger ETL pipeline for a specific condition"""
    from etl_pipeline import pipeline
    
    task = pipeline.process_condition.delay(condition)
    return {"task_id": task.id}

@app.get("/pipeline/status/{task_id}")
async def get_pipeline_status(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Check status of pipeline execution"""
    from etl_pipeline import pipeline
    
    task = pipeline.process_condition.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
