import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from models import Base


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing fron env file")

url = make_url(DATABASE_URL)
maintenance_url = url.set(database="postgres")

maintenance_engine = create_engine(maintenance_url)

with maintenance_engine.connect() as connection:
    exists = connection.execute(
        text("SELECT 1 FROM pg_database WHERE datname = :name"),
        {"name": url.database}
    ).scalar()
    
    if not exists:
        # CREATE DATABASE cannot run inside a transaction.

            connection.execution_options(
                isolation_level="AUTOCOMMIT"
            ).exec_driver_sql(
                f'CREATE DATABASE{url.database}'
            )
            
       
maintenance_engine.dispose()

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind = engine,
    autoflush=False,
    expire_on_commit=False
)       
   
def init_db() -> None:
    """Create missing tables without dropping existing tables."""  
    Base.metadata.create_all(bind=engine)
    
      
           
        
