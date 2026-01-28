import sqlite3
from src.conexion_db import DBConnection

class UsuarioDAO:
    
    @staticmethod
    def crear_tabla():
        """Crea la tabla usuarios si no existe."""
        conn = DBConnection.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                foto_cara BLOB NOT NULL
            );
            """
            cursor.execute(sql)
            conn.commit()
        except Exception as e:
            print(f"Error creando tabla: {e}")
        # No cerramos cursor/conn aquí para mantener la conexión viva en SQLite

    @staticmethod
    def registrar_usuario(nombre, cara_bytes):
        UsuarioDAO.crear_tabla() # Asegurar tabla
        conn = DBConnection.get_connection()
        cursor = conn.cursor()
        try:
            sql = "INSERT INTO usuarios (nombre, foto_cara) VALUES (?, ?)"
            # SQLite maneja bytes directamente con ?
            cursor.execute(sql, (nombre, cara_bytes))
            conn.commit()
            print("Usuario registrado con éxito.")
        except Exception as e:
            conn.rollback()
            print(f"Error al registrar: {e}")

    @staticmethod
    def obtener_todos():
        UsuarioDAO.crear_tabla() # Asegurar tabla
        conn = DBConnection.get_connection()
        cursor = conn.cursor()
        usuarios = []
        try:
            sql = "SELECT id, nombre, foto_cara FROM usuarios"
            cursor.execute(sql)
            usuarios = cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener usuarios: {e}")
        return usuarios
