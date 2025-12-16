import os

class Config:
    # Definimos la URI de la base de datos (SQLite en este caso)
    DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///books.db')
    SECRET_KEY = 'tu_clave_secreta_aqui' # [cite: 234]