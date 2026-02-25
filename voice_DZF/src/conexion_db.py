import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

class ConexionDB:
    """Patrón Singleton: garantiza una única conexión a la base de datos."""
    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super(ConexionDB, cls).__new__(cls)
            try:
                cls._instancia.conexion = psycopg2.connect(
                    host=os.getenv('DB_HOST'),
                    database=os.getenv('DB_NAME'),
                    user=os.getenv('DB_USER'),
                    password=os.getenv('DB_PASS'),
                    port=os.getenv('DB_PORT')
                )
                cls._instancia.conexion.autocommit = False
                print("[DB] Conexión exitosa a PostgreSQL (voice_audit_DZF_db)")
            except Exception as e:
                print(f"[DB] Error al conectar: {e}")
                cls._instancia = None
        return cls._instancia

    def get_conexion(self):
        """Devuelve la conexión activa."""
        return self.conexion

    def cerrar(self):
        """Cierra la conexión y resetea el Singleton."""
        if self.conexion:
            self.conexion.close()
        ConexionDB._instancia = None
