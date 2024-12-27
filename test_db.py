from sqlalchemy import create_engine

# Create engine
engine = create_engine('postgresql://user:password@localhost:5432/pharma_db')

try:
    # Test connection
    with engine.connect() as conn:
        print("Successfully connected to PostgreSQL!")
except Exception as e:
    print(f"Error connecting to PostgreSQL: {str(e)}")