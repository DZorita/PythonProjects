#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Asistente Virtual para Panadería "La Miga Mágica"
Interfaz mejorada con Tkinter - UI atractiva con colores y emojis
"""

import os
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
from dotenv import load_dotenv

# Carga variables de entorno
load_dotenv()

# Intenta cargar API de Google Gemini con fallbacks
try:
    from google import genai
except Exception:
    try:
        import google.generativeai as genai
    except Exception:
        genai = None

# ==============================================================================
# CONFIGURACIÓN Y CONSTANTES
# ==============================================================================

API_KEY = os.getenv("API_KEY")
USE_API = API_KEY is not None and genai is not None
model = None

# Esquema de colores profesional para panadería
COLOR_BG = "#2c3e50"          # Gris azulado oscuro (fondo principal)
COLOR_ACCENT = "#e74c3c"      # Rojo/Naranja (acentos, botones)
COLOR_SUCCESS = "#27ae60"     # Verde (estatus positivo)
COLOR_TEXT = "#ecf0f1"        # Gris claro (texto principal)
COLOR_SECONDARY_BG = "#34495e"  # Gris un poco más claro (marcos)
COLOR_WARM = "#f39c12"        # Naranja cálido (asistente)
COLOR_COOL = "#3498db"        # Azul frío (usuario)

# Tipografías mejoradas
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_TEXT = ("Segoe UI", 11)
FONT_BUTTON = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 9)

# Emojis temáticos
EMOJI_BREAD = "🥐"
EMOJI_BAGUETTE = "🥖"
EMOJI_CROISSANT = "🥐"
EMOJI_CAKE = "🍰"
EMOJI_GREETING = "👋"
EMOJI_TIME = "⏰"
EMOJI_PRICE = "💰"
EMOJI_INFO = "ℹ️"

# ==============================================================================
# FUNCIONES DE CONTEXTO Y RESPUESTA
# ==============================================================================

def load_context(filename="productos_panaderia.txt"):
    """Carga el archivo de contexto con productos de la panadería."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Información de la panadería no disponible."

def try_init_api():
    """Inicializa la API de Google Gemini."""
    global model, USE_API
    
    if not genai or not API_KEY:
        USE_API = False
        return False
    
    try:
        genai.configure(api_key=API_KEY)
        
        # Intenta encontrar un modelo disponible
        models = genai.list_models()
        
        # Busca modelos con palabras clave
        keywords = ["gemini-2", "gemini-1.5", "gemini-1", "chat", "bison", "text"]
        for m in models:
            if any(kw.lower() in m.name.lower() for kw in keywords):
                try:
                    model = genai.GenerativeModel(m.name)
                    USE_API = True
                    return True
                except Exception:
                    continue
        
        # Si encuentra al menos un modelo, úsalo
        if models:
            try:
                model = genai.GenerativeModel(models[0].name)
                USE_API = True
                return True
            except Exception:
                pass
            
    except Exception as e:
        print(f"Error al inicializar API: {e}")
    
    USE_API = False
    return False

def local_response(q):
    """Genera una respuesta local usando el contexto sin API."""
    q = q.lower().strip()
    context = load_context()
    
    # Saludos
    if any(word in q for word in ["hola", "buenos", "buenas", "hoy", "¿qué tal?"]):
        return f"{EMOJI_GREETING} ¡Hola! Bienvenido a 'La Miga Mágica'. ¿Qué puedo ofrecerte hoy?"
    
    # Horarios
    if any(word in q for word in ["hora", "abierto", "cierra", "abres", "abrir", "horario", "atención"]):
        if "Horarios:" in context:
            idx = context.find("Horarios:")
            horarios = context[idx:idx+300]
            return f"{EMOJI_TIME} **Nuestros horarios:**\n{horarios}"
        return f"{EMOJI_TIME} Consulta nuestros horarios visitando la panadería."
    
    # Productos/Catálogo
    if any(word in q for word in ["compr", "servi", "ofrec", "tiene", "hay", "menu", "catálogo", "qué vend", "qué hace"]):
        if "Panes Artesanales:" in context:
            lines = context.split('\n')
            products = [line for line in lines if line.strip() and not line.startswith('**') and '€' in line][:8]
            return f"{EMOJI_BREAD} **Nuestros mejores productos:**\n" + '\n'.join(products)
        return f"{EMOJI_BREAD} Tenemos deliciosos panes, bollería y especialidades."
    
    # Precios
    if any(word in q for word in ["preci", "cuánto", "cuesta", "vale", "costo", "tarifa", "precio"]):
        if "€" in context:
            lines = context.split('\n')
            products = [line for line in lines if '€' in line][:8]
            return f"{EMOJI_PRICE} **Precios especiales:**\n" + '\n'.join(products)
        return f"{EMOJI_PRICE} Nuestros precios son muy competitivos. ¡Pregunta en la tienda!"
    
    # Recomendaciones
    if any(word in q for word in ["recomienda", "qué me", "sugerir", "mejor", "popular", "especial", "favorit"]):
        return f"{EMOJI_CAKE} Recomendamos nuestro **Croissant Luna de Mantequilla** (2.00€) o la **Tarta Queso Celestial** (4.50€ la porción).\n¡Son nuestras especialidades! {EMOJI_CROISSANT}"
    
    # Alergias/Ingredientes
    if any(word in q for word in ["alerg", "gluten", "lactosa", "fruto seco", "ingredient", "sin gluten", "celí"]):
        return f"{EMOJI_INFO} Nuestros productos pueden contener trazas de frutos secos, gluten y lactosa. Para opciones sin gluten, consulta con el personal."
    
    # Encargos personalizados
    if any(word in q for word in ["encargo", "personali", "custom", "event", "cumpleaño", "boda", "fiesta"]):
        return f"{EMOJI_CAKE} Aceptamos encargos de tartas personalizadas con 48h de antelación. ¡Contacta con nosotros para más detalles!"
    
    # Respuesta por defecto
    return f"{EMOJI_BREAD} Soy el asistente de 'La Miga Mágica'. Puedo ayudarte con productos, precios, horarios y más. ¿Qué necesitas?"

def api_response(q):
    """Genera una respuesta usando la API de Google Gemini."""
    if not USE_API or model is None:
        return None
    
    try:
        context = load_context()
        prompt = f"""Eres un asistente amable para la panadería 'La Miga Mágica'. 
Usa la siguiente información para responder preguntas:

{context}

Pregunta del cliente: {q}

Responde de manera amigable y concisa, en máximo 150 palabras."""
        
        # Usa el método generate_content del modelo
        response = model.generate_content(prompt)
        
        # Extrae el texto de la respuesta
        if hasattr(response, 'text') and response.text:
            return response.text
        elif isinstance(response, str):
            return response
        
        return None
        
    except Exception as e:
        print(f"Error en API: {e}")
        return None

def generate(q):
    """Decide entre usar API o respuesta local."""
    if USE_API:
        try:
            ans = api_response(q)
            if ans:
                return ans
        except Exception as e:
            print(f"API error, fallback a local: {e}")
            globals()["USE_API"] = False
    
    return local_response(q)

# ==============================================================================
# INTERFAZ GRÁFICA
# ==============================================================================

class BakeryAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🥐 Panadería 'La Miga Mágica' - Asistente Virtual")
        self.root.geometry("700x800")
        self.root.config(bg=COLOR_BG)
        self.root.resizable(True, True)
        
        # Estilos personalizados
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz gráfica."""
        
        # ---- ENCABEZADO ----
        header_frame = tk.Frame(self.root, bg=COLOR_ACCENT, height=70)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text=f"{EMOJI_BREAD} La Miga Mágica {EMOJI_BAGUETTE}",
            font=("Segoe UI", 20, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_ACCENT
        )
        title_label.pack(pady=10)
        
        subtitle_label = tk.Label(
            header_frame,
            text="Asistente Virtual - Aquí para servirte 👨‍🍳",
            font=("Segoe UI", 10),
            fg="#ecf0f1",
            bg=COLOR_ACCENT
        )
        subtitle_label.pack()
        
        # ---- ÁREA DE CHAT ----
        chat_frame = tk.Frame(self.root, bg=COLOR_SECONDARY_BG)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.chat = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=FONT_TEXT,
            bg=COLOR_BG,
            fg=COLOR_TEXT,
            insertbackground=COLOR_ACCENT,
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.chat.pack(fill=tk.BOTH, expand=True)
        
        # Configurar tags para estilos de texto
        self.chat.tag_config("user", foreground=COLOR_COOL, font=("Segoe UI", 11, "bold"))
        self.chat.tag_config("user_msg", foreground=COLOR_COOL)
        self.chat.tag_config("assistant", foreground=COLOR_WARM, font=("Segoe UI", 11, "bold"))
        self.chat.tag_config("assistant_msg", foreground=COLOR_WARM)
        self.chat.tag_config("system", foreground=COLOR_SUCCESS, font=("Segoe UI", 9, "italic"))
        
        # Mensaje inicial
        self.chat.insert(tk.END, f"{EMOJI_GREETING} ", "system")
        self.chat.insert(tk.END, "¡Bienvenido a La Miga Mágica!\n", "system")
        self.chat.insert(tk.END, "Pregunta sobre nuestros productos, precios, horarios o lo que necesites.\n\n", "system")
        self.chat.config(state=tk.DISABLED)
        
        # ---- MARCO DE ENTRADA ----
        input_frame = tk.Frame(self.root, bg=COLOR_BG)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Campo de texto para entrada
        self.entry = tk.Entry(
            input_frame,
            font=FONT_TEXT,
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT,
            insertbackground=COLOR_ACCENT,
            relief=tk.FLAT
        )
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.entry.bind("<Return>", lambda e: self.on_send())
        
        # Botón Enviar
        send_button = tk.Button(
            input_frame,
            text="Enviar 📤",
            command=self.on_send,
            font=FONT_BUTTON,
            bg=COLOR_ACCENT,
            fg=COLOR_TEXT,
            activebackground="#c0392b",
            activeforeground=COLOR_TEXT,
            relief=tk.FLAT,
            padx=20,
            pady=5,
            cursor="hand2"
        )
        send_button.pack(side=tk.LEFT)
        
        # ---- BARRA DE ESTADO ----
        status_frame = tk.Frame(self.root, bg=COLOR_SECONDARY_BG)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        mode_text = f"API: {EMOJI_PRICE}" if USE_API else f"Local: {EMOJI_INFO}"
        self.status_label = tk.Label(
            status_frame,
            text=f"Estado: {mode_text}",
            font=FONT_SMALL,
            fg=COLOR_SUCCESS if USE_API else COLOR_TEXT,
            bg=COLOR_SECONDARY_BG
        )
        self.status_label.pack(side=tk.LEFT, padx=5)
        
    def add_message(self, sender, text):
        """Añade un mensaje al chat."""
        self.chat.config(state=tk.NORMAL)
        
        if sender == "user":
            self.chat.insert(tk.END, "Tú: ", "user")
            self.chat.insert(tk.END, f"{text}\n\n", "user_msg")
        else:  # assistant
            self.chat.insert(tk.END, "🥐 Asistente: ", "assistant")
            self.chat.insert(tk.END, f"{text}\n\n", "assistant_msg")
        
        self.chat.config(state=tk.DISABLED)
        self.chat.see(tk.END)  # Auto-scroll al final
    
    def on_send(self):
        """Maneja el envío de mensajes (en un hilo separado para no congelar la UI)."""
        user_input = self.entry.get().strip()
        if not user_input:
            return
        
        # Limpiar entrada
        self.entry.delete(0, tk.END)
        
        # Mostrar mensaje del usuario inmediatamente
        self.add_message("user", user_input)
        
        # Generar respuesta en un hilo para no bloquear la UI
        def worker():
            response = generate(user_input)
            # Actualizar GUI desde el hilo principal
            self.root.after(0, lambda: self.add_message("assistant", response))
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

# ==============================================================================
# PUNTO DE ENTRADA
# ==============================================================================

if __name__ == "__main__":
    # Inicializa la API
    try_init_api()
    
    # Crea la ventana principal
    root = tk.Tk()
    app = BakeryAssistantApp(root)
    
    # Inicia la interfaz
    root.mainloop()


