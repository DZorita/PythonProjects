from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config.config import Config

# Creamos el motor utilizando la URI de la configuración
engine = create_engine(Config.DATABASE_URI)

# Creamos la sesión para interactuar con la BBDD
Session = sessionmaker(bind=engine)
session = Session()

# Clase base para nuestros modelos
Base = declarative_base()