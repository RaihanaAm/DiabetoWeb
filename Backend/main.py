import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData , Table,Column ,Integer , String ,Float ,DateTime ,ForeignKey ,insert ,select
load_dotenv()
    
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)   

# Connexion et lecture
metadata = MetaData()
patients = Table('patients', metadata, autoload_with=engine)

# Faire la requête SELECT *
with engine.connect() as connection:
    query = select(patients)
    result = connection.execute(query)

    for row in result:
        print(row)  # Affiche chaque ligne sous forme de dictionnaire