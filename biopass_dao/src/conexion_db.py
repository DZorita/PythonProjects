import sqlite3
import os

class DBConnection:
    _connection = None
    DB_FILE = "biopass.db"

    @classmethod
    def get_connection(cls):
        if cls._connection is None:
            try:
                # Conectar a SQLite (crea el archivo si no existe)
                cls._connection = sqlite3.connect(cls.DB_FILE, check_same_thread=False)
                # check_same_thread=False para permitir acceso desde hilos (GUI + Video)
                
            except Exception as e:
                print(f"Error de conexión SQLite: {e}")
                raise e
        
        return cls._connection
