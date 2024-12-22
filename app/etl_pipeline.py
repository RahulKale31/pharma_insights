from typing import List, Dict
import pandas as pd
import requests
from datetime import datetime
from celery import Celery
from sqlalchemy import create_engine
from elasticsearch import Elasticsearch

class PharmaDataPipeline:
    def __init__(self, db_url: str, elastic_url: str):
        """Initialize the ETL pipeline with database and elasticsearch connections"""
        self.db_engine = create_engine(db_url)
        self.es = Elasticsearch([elastic_url])
        self.celery = Celery('pharma_tasks', broker='redis://localhost:6379/0')

    async def fetch_clinical_trials(self, condition: str) -> List[Dict]:
        """Fetch clinical trials data from ClinicalTrials.gov API"""
        base_url = "https://clinicaltrials.gov/api/query/study_fields"
        params = {
            "expr": condition,
            "fields": "NCTId,BriefTitle,Condition,Phase,StartDate,CompletionDate,Sponsor",
            "fmt": "json"
        }
        
        response = requests.get(base_url, params=params)
        return response.json()['StudyFieldsResponse']['StudyFields']

    def transform_trial_data(self, raw_trials: List[Dict]) -> pd.DataFrame:
        """Transform clinical trials data into structured format"""
        transformed_data = []
        
        for trial in raw_trials:
            transformed_trial = {
                'trial_id': trial['NCTId'][0] if trial.get('NCTId') else None,
                'title': trial['BriefTitle'][0] if trial.get('BriefTitle') else None,
                'condition': trial['Condition'][0] if trial.get('Condition') else None,
                'phase': trial['Phase'][0] if trial.get('Phase') else None,
                'start_date': trial['StartDate'][0] if trial.get('StartDate') else None,
                'completion_date': trial['CompletionDate'][0] if trial.get('CompletionDate') else None,
                'sponsor': trial['Sponsor'][0] if trial.get('Sponsor') else None,
                'processed_at': datetime.now()
            }
            transformed_data.append(transformed_trial)
        
        return pd.DataFrame(transformed_data)

    def load_to_database(self, df: pd.DataFrame, table_name: str):
        """Load transformed data into PostgreSQL database"""
        df.to_sql(
            table_name,
            self.db_engine,
            if_exists='append',
            index=False
        )

    def index_in_elasticsearch(self, df: pd.DataFrame, index_name: str):
        """Index the data in Elasticsearch for efficient searching"""
        for _, row in df.iterrows():
            doc = row.to_dict()
            self.es.index(
                index=index_name,
                document=doc,
                id=doc['trial_id']
            )

    @celery.task
    def process_condition(self, condition: str):
        """Process clinical trials data for a specific condition"""
        try:
            # Extract
            raw_trials = await self.fetch_clinical_trials(condition)
            
            # Transform
            transformed_df = self.transform_trial_data(raw_trials)
            
            # Load
            self.load_to_database(transformed_df, 'clinical_trials')
            self.index_in_elasticsearch(transformed_df, 'trials_index')
            
            return {
                'status': 'success',
                'condition': condition,
                'records_processed': len(transformed_df)
            }
        except Exception as e:
            return {
                'status': 'error',
                'condition': condition,
                'error': str(e)
            }

# Example configuration
config = {
    'db_url': 'postgresql://user:password@localhost:5432/pharma_db',
    'elastic_url': 'http://localhost:9200'
}

# Initialize pipeline
pipeline = PharmaDataPipeline(**config)
