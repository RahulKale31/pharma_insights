from celery import Celery

# Initialize Celery
# celery_app = Celery('pharma_tasks',
#                     broker='redis://localhost:6379/0',
#                     backend='redis://localhost:6379/0',  
#                     include=['etl_pipeline']) #When Redis running on WSL

celery_app = Celery('pharma_tasks',
                    broker='redis://localhost:6379/0',
                    backend='redis://localhost:6379/0',
                    broker_connection_retry_on_startup=True,
                    broker_connection_max_retries=10,
                    include=['etl_pipeline']) #When Redis runnning locally on windows