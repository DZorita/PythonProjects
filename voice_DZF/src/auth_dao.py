import json
import psycopg2.extras
from src.conexion_db import ConexionDB

class AuthDAO:
    """
    DAO (Data Access Object): Separa la lógica de negocio de las consultas SQL.
    Maneja tanto datos relacionales (usuarios_voz) como JSONB (log_accesos_voz).
    """

    def __init__(self):
        db = ConexionDB()
        self.conn = db.get_conexion()

    # ─── USUARIOS ────────────────────────────────────────────────────────────

    def registrar_usuario(self, username: str, passphrase: str) -> int | None:
        """Inserta un usuario nuevo. Devuelve el ID generado."""
        try:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO usuarios_voz (username, passphrase_text) VALUES (%s, %s) RETURNING id",
                (username, passphrase)
            )
            user_id = cur.fetchone()[0]
            self.conn.commit()
            return user_id
        except Exception as e:
            self.conn.rollback()
            print(f"[DAO] Error al registrar usuario: {e}")
            return None

    def buscar_usuario(self, username: str) -> dict | None:
        """Devuelve el usuario como diccionario o None si no existe."""
        try:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT * FROM usuarios_voz WHERE username = %s", (username,))
            return cur.fetchone()
        except Exception as e:
            print(f"[DAO] Error al buscar usuario: {e}")
            return None

    def actualizar_intentos(self, user_id: int, intentos: int, bloqueado_hasta=None):
        """Actualiza los intentos fallidos y el bloqueo temporal."""
        try:
            cur = self.conn.cursor()
            cur.execute(
                "UPDATE usuarios_voz SET intentos_fallidos = %s, bloqueado_hasta = %s WHERE id = %s",
                (intentos, bloqueado_hasta, user_id)
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[DAO] Error al actualizar intentos: {e}")

    def resetear_intentos(self, user_id: int):
        """Resetea intentos fallidos tras login exitoso."""
        try:
            cur = self.conn.cursor()
            cur.execute(
                "UPDATE usuarios_voz SET intentos_fallidos = 0, bloqueado_hasta = NULL WHERE id = %s",
                (user_id,)
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[DAO] Error al resetear intentos: {e}")

    # ─── LOGS JSONB ──────────────────────────────────────────────────────────

    def insertar_log(self, usuario_id: int, datos_json: dict):
        """
        Inserta un registro en log_accesos_voz con datos dinámicos en JSONB.
        Recibe un diccionario Python y lo serializa a JSON para PostgreSQL.
        """
        try:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO log_accesos_voz (usuario_id, resultado_json) VALUES (%s, %s)",
                (usuario_id, json.dumps(datos_json))
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[DAO] Error al insertar log: {e}")

    def obtener_logs_criticos(self) -> list:
        """
        Consulta avanzada JSONB: devuelve eventos críticos.
        Filtra registros con status='FAIL' o confianza < 0.6.
        """
        try:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT
                    u.username,
                    l.fecha_intento,
                    l.resultado_json->>'status'         AS status,
                    l.resultado_json->>'motivo'         AS motivo,
                    l.resultado_json->>'confianza'      AS confianza,
                    l.resultado_json->>'intentos_rest'  AS intentos_restantes
                FROM log_accesos_voz l
                JOIN usuarios_voz u ON l.usuario_id = u.id
                WHERE l.resultado_json->>'status' = 'FAIL'
                   OR (l.resultado_json->>'confianza' IS NOT NULL
                       AND (l.resultado_json->>'confianza')::float < 0.6)
                ORDER BY l.fecha_intento DESC
            """)
            return cur.fetchall()
        except Exception as e:
            print(f"[DAO] Error al obtener logs críticos: {e}")
            return []

    def obtener_todos_logs(self) -> list:
        """Devuelve todos los logs de acceso para la auditoría completa."""
        try:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT
                    u.username,
                    l.fecha_intento,
                    l.resultado_json->>'status'         AS status,
                    l.resultado_json->>'motivo'         AS motivo,
                    l.resultado_json->>'confianza'      AS confianza,
                    l.resultado_json->>'latencia_ms'    AS latencia_ms,
                    l.resultado_json->>'intentos_rest'  AS intentos_restantes
                FROM log_accesos_voz l
                JOIN usuarios_voz u ON l.usuario_id = u.id
                ORDER BY l.fecha_intento DESC
            """)
            return cur.fetchall()
        except Exception as e:
            print(f"[DAO] Error al obtener logs: {e}")
            return []
