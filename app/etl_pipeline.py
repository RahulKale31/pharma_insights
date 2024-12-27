from typing import List, Dict
import pandas as pd
import requests
from datetime import datetime
from celery import Celery
from sqlalchemy import create_engine
from elasticsearch import Elasticsearch

# Initialize Celery with explicit configuration
celery_app = Celery('pharma_tasks')
# celery_app.conf.update(
#     broker_url='redis://localhost:6379/0',
#     result_backend='redis://localhost:6379/0',
#     task_serializer='json',
#     accept_content=['json'],
#     result_serializer='json',
#     timezone='UTC',
#     enable_utc=True,
# ) #When Redis is running on WSL

celery_app.conf.update(
    broker_transport_options = {'visibility_timeout': 3600},
    result_expires = 3600,
    worker_max_tasks_per_child = 100,
    worker_prefetch_multiplier = 1
) #WHen Redis is running locally on windows machine

class PharmaDataPipeline:
    def __init__(self, db_url: str, elastic_url: str):
        """Initialize the ETL pipeline with database and elasticsearch connections"""
        self.db_engine = create_engine(db_url)
        self.es = Elasticsearch([elastic_url])
     
    def fetch_clinical_trials(self, condition: str) -> List[Dict]:
        """Fetch clinical trials data from ClinicalTrials.gov Beta API"""
        base_url = "https://clinicaltrials.gov/api/v2/studies"
        params = {
            "query.cond": condition,
            "pageSize": 100,
            "fields": "NCTId,BriefTitle,Condition,Phase,StartDate,CompletionDate,LeadSponsorName"
        }
        
        headers = {
            "accept": "application/json"
        }
        
        try:
            print(f"Fetching trials for condition: {condition}")
            response = requests.get(base_url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                studies = data.get('studies', [])
                print(f"Successfully fetched {len(studies)} studies")
                return studies
            else:
                print(f"Error response from API: {response.text}")
                return []
                
        except Exception as e:
            print(f"Error fetching trials: {str(e)}")
            return []

    def transform_trial_data(self, raw_trials: List[Dict]) -> pd.DataFrame:
        """Transform clinical trials data into structured format"""
        transformed_data = []
        
        for trial in raw_trials:
            protocol_section = trial.get('protocolSection', {})
            identification = protocol_section.get('identificationModule', {})
            status = protocol_section.get('statusModule', {})
            sponsor = protocol_section.get('sponsorCollaboratorsModule', {}).get('leadSponsor', {})
            conditions = protocol_section.get('conditionsModule', {}).get('conditions', [])
            design = protocol_section.get('designModule', {})
            
            transformed_trial = {
                'trial_id': identification.get('nctId'),
                'title': identification.get('briefTitle'),
                'condition': conditions[0] if conditions else None,  # Taking first condition
                'phase': design.get('phases', [None])[0],  # Taking first phase
                'start_date': status.get('startDateStruct', {}).get('date'),
                'completion_date': status.get('completionDateStruct', {}).get('date'),
                'sponsor': sponsor.get('name'),
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

@celery_app.task(bind=True)
def process_condition(self, condition: str):
    """Process clinical trials data for a specific condition"""
    print(f"Starting to process condition: {condition}")  # Debug log
    
    config = {
        'db_url': 'postgresql://<your_user>:<your_password>@localhost:5432/pharma_db',
        'elastic_url': 'http://localhost:9200'
    }
    
    try:
        pipeline = PharmaDataPipeline(**config)
        
        # Extract
        print("Fetching data from ClinicalTrials.gov...")  # Debug log
        raw_trials = pipeline.fetch_clinical_trials(condition)
        print(f"Fetched {len(raw_trials) if raw_trials else 0} trials")  # Debug log
        
        # Transform
        print("Transforming data...")  # Debug log
        transformed_df = pipeline.transform_trial_data(raw_trials)
        print(f"Transformed {len(transformed_df)} records")  # Debug log
        
        # Load
        print("Loading to database...")  # Debug log
        pipeline.load_to_database(transformed_df, 'clinical_trials')
        print("Loading to elasticsearch...")  # Debug log
        pipeline.index_in_elasticsearch(transformed_df, 'trials_index')
        
        return {
            'status': 'success',
            'condition': condition,
            'records_processed': len(transformed_df)
        }
        
    except Exception as e:
        print(f"Error in pipeline: {str(e)}")  # Debug log
        return {
            'status': 'error',
            'condition': condition,
            'error': str(e)
        }

# Only needed if running the file directly
if __name__ == "__main__":
    celery_app.start()