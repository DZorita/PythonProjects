"""
VoiceAudit - Sistema de Acceso por Voz
Arquitectura: Singleton (ConexionDB) + DAO (AuthDAO) + Facade (VoiceService)
Base de datos: PostgreSQL con JSONB para logs dinámicos
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime, timedelta
import threading

from src.conexion_db import ConexionDB
from src.auth_dao import AuthDAO
from src.voice_service import VoiceService

# ─── Constantes ──────────────────────────────────────────────────────────────
MAX_INTENTOS = 3
BLOQUEO_MINUTOS = 2
UMBRAL_CONFIANZA = 0.6
COLOR_BG = "#1a1a2e"
COLOR_PANEL = "#16213e"
COLOR_ACCENT = "#0f3460"
COLOR_OK = "#4ade80"
COLOR_FAIL = "#f87171"
COLOR_WARN = "#facc15"
COLOR_TEXT = "#e2e8f0"
COLOR_MUTED = "#94a3b8"


# ─── Aplicación Principal ─────────────────────────────────────────────────────
class VoiceAuditApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VoiceAudit – Acceso por Voz con PostgreSQL JSONB")
        self.geometry("900x640")
        self.resizable(False, False)
        self.configure(bg=COLOR_BG)

        # Servicios (inicialización única)
        self.dao = AuthDAO()
        self.voice = VoiceService()

        self._build_ui()

    # ═══════════════════════════════════════════════════════════════════════════
    #  CONSTRUCCIÓN DE LA INTERFAZ
    # ═══════════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        # Cabecera
        header = tk.Frame(self, bg=COLOR_ACCENT, height=60)
        header.pack(fill="x")
        tk.Label(
            header,
            text="🎤  VoiceAudit  |  Sistema de Acceso por Voz",
            bg=COLOR_ACCENT, fg=COLOR_TEXT,
            font=("Segoe UI", 16, "bold")
        ).pack(pady=12)

        # Notebook (pestañas)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=COLOR_BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=COLOR_PANEL, foreground=COLOR_TEXT,
                        padding=[20, 8], font=("Segoe UI", 11))
        style.map("TNotebook.Tab", background=[("selected", COLOR_ACCENT)])

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_registro = tk.Frame(self.tabs, bg=COLOR_BG)
        self.tab_login    = tk.Frame(self.tabs, bg=COLOR_BG)
        self.tab_auditoria = tk.Frame(self.tabs, bg=COLOR_BG)

        self.tabs.add(self.tab_registro,  text="📝  Registro")
        self.tabs.add(self.tab_login,     text="🔐  Inicio de Sesión")
        self.tabs.add(self.tab_auditoria, text="🔍  Auditoría JSONB")

        self._build_registro()
        self._build_login()
        self._build_auditoria()

    # ═══════════════════════════════════════════════════════════════════════════
    #  PESTAÑA 1 – REGISTRO
    # ═══════════════════════════════════════════════════════════════════════════
    def _build_registro(self):
        frame = self.tab_registro
        self._label(frame, "Paso 1 – Registro de Usuario por Voz", 14, bold=True).pack(pady=(20, 5))
        self._label(frame, "Introduce tu nombre y luego di tu frase secreta al micrófono.", 10).pack()

        # Campo nombre
        row = tk.Frame(frame, bg=COLOR_BG)
        row.pack(pady=15)
        self._label(row, "Nombre de usuario:", 11).pack(side="left", padx=5)
        self.entry_reg_nombre = tk.Entry(row, width=25, font=("Segoe UI", 11),
                                         bg=COLOR_PANEL, fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
                                         relief="flat", bd=4)
        self.entry_reg_nombre.pack(side="left", padx=5)

        # Botón grabar
        self.btn_grabar_reg = self._boton(frame, "🎙️  Grabar Frase Secreta", self._registrar, COLOR_ACCENT)
        self.btn_grabar_reg.pack(pady=8)

        # Status
        self.lbl_reg_status = self._label(frame, "", 11)
        self.lbl_reg_status.pack(pady=5)

        # Frase reconocida (preview)
        self._label(frame, "Frase reconocida:", 10, muted=True).pack()
        self.txt_reg_frase = self._text_box(frame, height=3)
        self.txt_reg_frase.pack(padx=30, fill="x")

        # Log JSONB preview
        self._label(frame, "JSON guardado en log_accesos_voz:", 10, muted=True).pack(pady=(15, 2))
        self.txt_reg_json = self._text_box(frame, height=6)
        self.txt_reg_json.pack(padx=30, fill="x")

    def _registrar(self):
        nombre = self.entry_reg_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Campo vacío", "Escribe tu nombre de usuario primero.")
            return

        usuario_existente = self.dao.buscar_usuario(nombre)
        if usuario_existente:
            messagebox.showerror("Ya existe", f"El usuario '{nombre}' ya está registrado.")
            return

        self._status(self.lbl_reg_status, "Calibrando micrófono… habla cuando escuches el tono.", COLOR_WARN)
        self.btn_grabar_reg.config(state="disabled")
        threading.Thread(target=self._registrar_hilo, args=(nombre,), daemon=True).start()

    def _registrar_hilo(self, nombre):
        resultado = self.voice.capturar_frase()
        self.after(0, self._registrar_resultado, nombre, resultado)

    def _registrar_resultado(self, nombre, resultado):
        self.btn_grabar_reg.config(state="normal")

        if resultado["error"]:
            datos_json = {
                "status": "FAIL",
                "motivo": resultado["error"],
                "tipo_evento": "registro_error_hardware"
            }
            # Necesitamos un ID temporal; si no existe el usuario, usaremos id=-1 (no FK válida)
            # En su lugar, mostramos el JSON sin insertar en DB para no violar la FK
            self._status(self.lbl_reg_status, f"❌ Error: {resultado['error']}", COLOR_FAIL)
            self._set_text(self.txt_reg_frase, resultado["error"])
            self._set_text(self.txt_reg_json, self._fmt_json(datos_json))
            messagebox.showerror("Error de micrófono", resultado["error"])
            return

        passphrase = resultado["texto"]
        self._set_text(self.txt_reg_frase, passphrase)

        # Confirmar con el usuario
        confirmar = messagebox.askyesno(
            "Confirmar frase",
            f"¿Es correcta tu frase secreta?\n\n\"{passphrase}\""
        )
        if not confirmar:
            self._status(self.lbl_reg_status, "Registro cancelado. Intenta de nuevo.", COLOR_WARN)
            return

        # Guardar en DB
        user_id = self.dao.registrar_usuario(nombre, passphrase)
        if user_id is None:
            self._status(self.lbl_reg_status, "❌ Error al guardar en DB.", COLOR_FAIL)
            return

        # Log JSONB de registro exitoso
        datos_json = {
            "status": "OK",
            "tipo_evento": "registro",
            "confianza": resultado["confianza"],
            "latencia_ms": resultado["latencia_ms"],
            "frase_longitud": len(passphrase)
        }
        self.dao.insertar_log(user_id, datos_json)

        self._set_text(self.txt_reg_json, self._fmt_json(datos_json))
        self._status(self.lbl_reg_status, f"✅ Usuario '{nombre}' registrado con ID={user_id}", COLOR_OK)
        messagebox.showinfo("Registro exitoso", f"¡Bienvenido, {nombre}! Tu frase ha sido guardada.")

    # ═══════════════════════════════════════════════════════════════════════════
    #  PESTAÑA 2 – LOGIN
    # ═══════════════════════════════════════════════════════════════════════════
    def _build_login(self):
        frame = self.tab_login
        self._label(frame, "Paso 2 – Inicio de Sesión por Voz", 14, bold=True).pack(pady=(20, 5))
        self._label(frame, "Introduce tu nombre y di tu frase al micrófono.", 10).pack()

        row = tk.Frame(frame, bg=COLOR_BG)
        row.pack(pady=15)
        self._label(row, "Nombre de usuario:", 11).pack(side="left", padx=5)
        self.entry_log_nombre = tk.Entry(row, width=25, font=("Segoe UI", 11),
                                          bg=COLOR_PANEL, fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
                                          relief="flat", bd=4)
        self.entry_log_nombre.pack(side="left", padx=5)

        self.btn_login = self._boton(frame, "🎙️  Verificar Voz", self._login, COLOR_ACCENT)
        self.btn_login.pack(pady=8)

        self.lbl_login_status = self._label(frame, "", 11)
        self.lbl_login_status.pack(pady=5)

        # Barras de información
        info_frame = tk.Frame(frame, bg=COLOR_BG)
        info_frame.pack(pady=5, fill="x", padx=30)

        self._label(info_frame, "Frase escuchada:", 10, muted=True).grid(row=0, column=0, sticky="w")
        self.lbl_frase_escuchada = self._label(info_frame, "—", 10)
        self.lbl_frase_escuchada.grid(row=0, column=1, sticky="w", padx=10)

        self._label(info_frame, "Confianza IA:", 10, muted=True).grid(row=1, column=0, sticky="w")
        self.lbl_confianza = self._label(info_frame, "—", 10)
        self.lbl_confianza.grid(row=1, column=1, sticky="w", padx=10)

        self._label(info_frame, "Intentos restantes:", 10, muted=True).grid(row=2, column=0, sticky="w")
        self.lbl_intentos = self._label(info_frame, "—", 10)
        self.lbl_intentos.grid(row=2, column=1, sticky="w", padx=10)

        # JSON log
        self._label(frame, "JSON guardado en log_accesos_voz:", 10, muted=True).pack(pady=(15, 2))
        self.txt_login_json = self._text_box(frame, height=8)
        self.txt_login_json.pack(padx=30, fill="x")

    def _login(self):
        nombre = self.entry_log_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Campo vacío", "Escribe tu nombre de usuario.")
            return

        usuario = self.dao.buscar_usuario(nombre)
        if not usuario:
            messagebox.showerror("No encontrado", f"El usuario '{nombre}' no existe. Regístrate primero.")
            return

        # Verificar bloqueo
        if usuario["bloqueado_hasta"] and usuario["bloqueado_hasta"] > datetime.now():
            restante = (usuario["bloqueado_hasta"] - datetime.now()).seconds // 60 + 1
            messagebox.showwarning("Bloqueado", f"Usuario bloqueado. Espera {restante} min.")
            self._status(self.lbl_login_status, f"🔒 Bloqueado hasta las {usuario['bloqueado_hasta'].strftime('%H:%M')}", COLOR_FAIL)
            return

        self._status(self.lbl_login_status, "Calibrando micrófono… habla ahora.", COLOR_WARN)
        self.btn_login.config(state="disabled")
        threading.Thread(target=self._login_hilo, args=(usuario,), daemon=True).start()

    def _login_hilo(self, usuario):
        resultado = self.voice.capturar_frase()
        self.after(0, self._login_resultado, usuario, resultado)

    def _login_resultado(self, usuario, resultado):
        self.btn_login.config(state="normal")
        user_id = usuario["id"]

        if resultado["error"]:
            datos_json = {
                "status": "FAIL",
                "motivo": resultado["error"],
                "tipo_evento": "login_error_hardware",
                "confianza": 0.0
            }
            self.dao.insertar_log(user_id, datos_json)
            self._set_text(self.txt_login_json, self._fmt_json(datos_json))
            self._status(self.lbl_login_status, f"❌ {resultado['error']}", COLOR_FAIL)
            return

        frase_dicha    = resultado["texto"]
        frase_guardada = usuario["passphrase_text"].strip().lower()
        confianza      = resultado["confianza"]
        latencia       = resultado["latencia_ms"]
        intentos_act   = usuario["intentos_fallidos"]

        self.lbl_frase_escuchada.config(text=f'"{frase_dicha}"')
        color_conf = COLOR_OK if confianza >= UMBRAL_CONFIANZA else COLOR_FAIL
        self.lbl_confianza.config(text=f"{confianza:.0%}", fg=color_conf)

        if frase_dicha == frase_guardada:
            # ── LOGIN EXITOSO ──
            self.dao.resetear_intentos(user_id)
            datos_json = {
                "status": "OK",
                "tipo_evento": "login_exitoso",
                "confianza": confianza,
                "latencia_ms": latencia
            }
            self.dao.insertar_log(user_id, datos_json)
            self._set_text(self.txt_login_json, self._fmt_json(datos_json))
            self.lbl_intentos.config(text=f"{MAX_INTENTOS}/{MAX_INTENTOS}")
            self._status(self.lbl_login_status, f"✅ Acceso concedido a '{usuario['username']}'", COLOR_OK)
            messagebox.showinfo("Acceso concedido", f"¡Bienvenido, {usuario['username']}!")
        else:
            # ── FALLO DE LOGIN ──
            nuevos_intentos = intentos_act + 1
            restantes = MAX_INTENTOS - nuevos_intentos
            datos_json = {
                "status": "FAIL",
                "tipo_evento": "login_fallido",
                "confianza": confianza,
                "latencia_ms": latencia,
                "frase_dicha": frase_dicha,
                "intentos_rest": restantes
            }

            bloqueo = None
            if restantes <= 0:
                bloqueo = datetime.now() + timedelta(minutes=BLOQUEO_MINUTOS)
                datos_json["bloqueado_hasta"] = bloqueo.isoformat()
                datos_json["motivo"] = "max_intentos_alcanzado"

            self.dao.actualizar_intentos(user_id, nuevos_intentos, bloqueo)
            self.dao.insertar_log(user_id, datos_json)
            self._set_text(self.txt_login_json, self._fmt_json(datos_json))

            self.lbl_intentos.config(text=f"{max(0, restantes)}/{MAX_INTENTOS}", fg=COLOR_FAIL)

            if restantes <= 0:
                self._status(self.lbl_login_status,
                             f"🔒 Usuario bloqueado {BLOQUEO_MINUTOS} min por exceder intentos.", COLOR_FAIL)
                messagebox.showerror("Bloqueado",
                                     f"Demasiados intentos fallidos. Bloqueado {BLOQUEO_MINUTOS} minutos.")
            else:
                self._status(self.lbl_login_status,
                             f"❌ Frase incorrecta. Intentos restantes: {restantes}", COLOR_FAIL)
                messagebox.showwarning("Acceso denegado",
                                       f"Frase incorrecta.\nIntentos restantes: {restantes}")

    # ═══════════════════════════════════════════════════════════════════════════
    #  PESTAÑA 3 – AUDITORÍA JSONB
    # ═══════════════════════════════════════════════════════════════════════════
    def _build_auditoria(self):
        frame = self.tab_auditoria
        self._label(frame, "Paso 3 – Panel de Auditoría (Consultas JSONB)", 14, bold=True).pack(pady=(20, 5))
        self._label(frame, "Ejecuta consultas avanzadas sobre la columna resultado_json de PostgreSQL.", 10).pack()

        btn_frame = tk.Frame(frame, bg=COLOR_BG)
        btn_frame.pack(pady=12)
        self._boton(btn_frame, "⚠️ Ver Eventos Críticos (FAIL + confianza<0.6)",
                    self._mostrar_criticos, "#7c3aed").pack(side="left", padx=5)
        self._boton(btn_frame, "📋 Ver Todos los Logs",
                    self._mostrar_todos, COLOR_ACCENT).pack(side="left", padx=5)

        self._label(frame, "Resultados de la consulta JSONB:", 10, muted=True).pack(pady=(10, 2))
        self.txt_audit = scrolledtext.ScrolledText(
            frame, height=18, width=100,
            font=("Courier New", 9),
            bg=COLOR_PANEL, fg=COLOR_TEXT,
            insertbackground=COLOR_TEXT, relief="flat", bd=0
        )
        self.txt_audit.pack(padx=15, fill="both", expand=True)

    def _mostrar_criticos(self):
        logs = self.dao.obtener_logs_criticos()
        self._renderizar_logs(logs, titulo="=== EVENTOS CRÍTICOS (FAIL | confianza < 0.6) ===")

    def _mostrar_todos(self):
        logs = self.dao.obtener_todos_logs()
        self._renderizar_logs(logs, titulo="=== TODOS LOS LOGS DE ACCESO ===")

    def _renderizar_logs(self, logs, titulo):
        self.txt_audit.config(state="normal")
        self.txt_audit.delete("1.0", tk.END)
        self.txt_audit.insert(tk.END, f"{titulo}\n")
        self.txt_audit.insert(tk.END, f"{'─'*80}\n")

        if not logs:
            self.txt_audit.insert(tk.END, "  (Sin registros)\n")
        else:
            for fila in logs:
                fecha = fila["fecha_intento"].strftime("%Y-%m-%d %H:%M:%S") if fila.get("fecha_intento") else "—"
                self.txt_audit.insert(tk.END,
                    f"  Usuario:   {fila.get('username','—')}\n"
                    f"  Fecha:     {fecha}\n"
                    f"  Status:    {fila.get('status','—')}\n"
                    f"  Motivo:    {fila.get('motivo','—')}\n"
                    f"  Confianza: {fila.get('confianza','—')}\n"
                    f"  Latencia:  {fila.get('latencia_ms','—')} ms\n"
                    f"  Intentos restantes: {fila.get('intentos_restantes','—')}\n"
                    f"{'─'*80}\n"
                )
        self.txt_audit.config(state="disabled")

    # ═══════════════════════════════════════════════════════════════════════════
    #  UTILIDADES DE UI
    # ═══════════════════════════════════════════════════════════════════════════
    def _label(self, parent, texto, size, bold=False, muted=False):
        weight = "bold" if bold else "normal"
        color = COLOR_MUTED if muted else COLOR_TEXT
        return tk.Label(parent, text=texto, bg=COLOR_BG, fg=color,
                        font=("Segoe UI", size, weight))

    def _boton(self, parent, texto, comando, color):
        return tk.Button(parent, text=texto, command=comando,
                         bg=color, fg=COLOR_TEXT, font=("Segoe UI", 10, "bold"),
                         relief="flat", bd=0, padx=15, pady=8, cursor="hand2",
                         activebackground=COLOR_ACCENT, activeforeground=COLOR_TEXT)

    def _text_box(self, parent, height=4):
        return tk.Text(parent, height=height, font=("Courier New", 9),
                       bg=COLOR_PANEL, fg=COLOR_OK,
                       insertbackground=COLOR_TEXT, relief="flat", bd=4, state="disabled")

    def _status(self, label, texto, color):
        label.config(text=texto, fg=color)

    def _set_text(self, widget, texto):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", texto)
        widget.config(state="disabled")

    @staticmethod
    def _fmt_json(d: dict) -> str:
        import json
        return json.dumps(d, indent=2, ensure_ascii=False)


# ─── Punto de entrada ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = VoiceAuditApp()
    app.mainloop()
