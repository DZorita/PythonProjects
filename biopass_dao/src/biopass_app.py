import sys
import os
import threading
import time

# Añadir el directorio raíz del proyecto al path para permitir imports absolutos (src.xxx)
# Esto soluciona "ModuleNotFoundError: No module named 'src'"
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
from src.usuario_dao import UsuarioDAO
from src.utils.camera_utils import CameraUtils

# Configurar salida UTF-8 para Windows
sys.stdout.reconfigure(encoding='utf-8')


class BioPassApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BioPass - Control de Acceso")
        self.root.geometry("800x700")
        self.root.resizable(False, False)
        
        self.frame_actual = None
        self.lock = threading.Lock()
        self.running = True
        self.camara_iniciada = False
        
        self.photo = None  # Mantener referencia a la imagen
        
        # Cache de rostros conocidos
        self.known_face_encodings = []
        self.known_face_names = []
        
        # Inicializar modelos DNN
        CameraUtils.initialize_models()
        
        # Cargar usuarios al iniciar
        try:
            self.cargar_usuarios()
        except Exception as e:
            print(f"Error crítico de BD: {e}")
            messagebox.showerror("Error de Base de Datos", 
                "No se pudo conectar a la base de datos PostgreSQL.\n\n"
                "1. Asegúrate de que PostgreSQL esté ejecutándose.\n"
                "2. Revisa la configuración en .env.\n\n"
                f"Detalle: {str(e)[:100]}..."
            )
        
        # Frame principal
        main_frame = tk.Frame(root, bg="#2b2b2b")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Label para video con imagen
        self.label_video = tk.Label(main_frame, bg="black", width=640, height=480, bd=2, relief="solid")
        self.label_video.pack(pady=10)
        
        # Texto de estado inicial
        self.texto_estado = tk.Label(main_frame, text="Iniciando cámara...", bg="black", fg="white", font=("Arial", 14, "bold"))
        self.texto_estado.place(in_=self.label_video, relx=0.5, rely=0.5, anchor="center")
        
        # Frame para entrada de nombre
        entrada_frame = tk.Frame(main_frame, bg="#2b2b2b")
        entrada_frame.pack(pady=10, fill=tk.X)
        
        tk.Label(entrada_frame, text="Nombre:", bg="#2b2b2b", fg="white", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        self.entry_nombre = tk.Entry(entrada_frame, font=("Arial", 14), width=25)
        self.entry_nombre.pack(side=tk.LEFT, padx=5)
        
        # Frame para botones
        botones_frame = tk.Frame(main_frame, bg="#2b2b2b")
        botones_frame.pack(pady=15, fill=tk.X)
        
        btn_registro = tk.Button(
            botones_frame, text="📷 Registrar", command=self.registrar_usuario,
            width=18, height=2, font=("Arial", 12, "bold"),
            bg="#00aa00", fg="white", cursor="hand2"
        )
        btn_registro.pack(side=tk.LEFT, padx=15, expand=True)
        
        btn_login = tk.Button(
            botones_frame, text="🔓 Entrar (Login)", command=self.login_usuario,
            width=18, height=2, font=("Arial", 12, "bold"),
            bg="#0066cc", fg="white", cursor="hand2"
        )
        btn_login.pack(side=tk.RIGHT, padx=15, expand=True)
        
        # Registrar evento de cierre de ventana
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)
        
        # Iniciar hilo de video
        self.thread = threading.Thread(target=self.video_loop, daemon=True)
        self.thread.start()
        
        # Iniciar actualización de GUI
        self.actualizar_gui()

    def cargar_usuarios(self):
        """Pre-carga los encodings de usuarios de la BD."""
        print("Cargando usuarios existentes para caché...")
        usuarios = UsuarioDAO.obtener_todos()
        count = 0
        errores = 0
        
        for user in usuarios:
            user_id = user[0]
            nombre = user[1]
            foto_bytes = user[2]
            
            imagen = CameraUtils.bytes_a_imagen(foto_bytes)
            if imagen is not None:
                # Intentar detectar rostro en la imagen guardada para extraer features
                face_data = CameraUtils.detectar_rostro(imagen)
                if face_data is not None:
                    encoding = CameraUtils.obtener_encoding(imagen, face_data)
                    if encoding is not None:
                        self.known_face_encodings.append(encoding)
                        self.known_face_names.append(nombre)
                        count += 1
                else:
                    # Si no detecta en el recorte, es problemático.
                    errores += 1
                    
        print(f"✅ Se cargaron {count} usuarios. (Fallidos: {errores})")

    def video_loop(self):
        """Hilo dedicado a capturar frames de la cámara. Busca la mejor config."""
        print("Iniciando hilo de búsqueda de cámara...")
        
        configs = [
            (0, cv2.CAP_DSHOW, "Index 0 - DSHOW (Recomendado)"),
            (0, cv2.CAP_MSMF, "Index 0 - MSMF"),
            (0, cv2.CAP_ANY, "Index 0 - Automático"),
            (1, cv2.CAP_DSHOW, "Index 1 - DSHOW"),
            (1, cv2.CAP_ANY, "Index 1 - Automático"),
        ]
        
        for idx, backend, nombre in configs:
            if not self.running: break
            
            print(f"Probando configuración: {nombre}...")
            try:
                cap = cv2.VideoCapture(idx, backend)
                
                # Configurar resolución (COMENTADO: A veces fuerza pantalla negra en DSHOW)
                # try:
                #    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                #    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                # except:
                #    pass
                
                if not cap.isOpened():
                    print(f"❌ {nombre} no abrió.")
                    cap.release()
                    continue
                
                # Intentar "despertar" la cámara ajustando a HD (1280x720)
                # Muchas cámaras modernas fallan en 640x480 por defecto con DSHOW
                try:
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                except:
                    pass
                    
                # Intentar leer frames para estabilizar
                print(f"   Leyendo frames de calentamiento para {nombre}...")
                print(f"   Leyendo frames de calentamiento para {nombre}...")
                frames_leidos = 0
                for i in range(60):
                    if not self.running: break
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        frames_leidos += 1
                        # Debug cada 10 frames
                        if i % 10 == 0:
                            brillo = frame.mean()
                            print(f"      Frame {i}: Brillo={brillo:.2f} (0=Negro, 255=Blanco)")
                    time.sleep(0.05)
                
                # Si logramos leer frames, aceptamos la cámara (aunque se vea negra)
                if frames_leidos > 0:
                    print(f"✅ {nombre} ABIERTA CORRECTAMENTE. (Frames leídos: {frames_leidos})")
                    self.camara_iniciada = True
                    
                    while self.running:
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            with self.lock:
                                self.frame_actual = frame
                        else:
                            time.sleep(0.1)
                    
                    cap.release()
                    return 
                
                else:
                    print(f"⚠️ {nombre} dio video NEGRO o vacío.")
                    cap.release()
            
            except Exception as e:
                print(f"❌ Error probando {nombre}: {e}")
                
        print("❌ No se encontró ninguna cámara funcional.")
        self.root.after(0, lambda: self.texto_estado.config(text="❌ Error de Cámara\nNo detectada", fg="red"))

    def actualizar_gui(self):
        if self.camara_iniciada and self.texto_estado.winfo_viewable() and "Error" not in self.texto_estado.cget("text"):
             self.texto_estado.place_forget()
        
        frame_copy = None
        with self.lock:
            if self.frame_actual is not None:
                frame_copy = self.frame_actual.copy()
        
        if frame_copy is not None:
            # Dibujar rectangulo si detecta rostro (opcional, para feedback visual)
            # Solo para visualización en tiempo real puede ser costoso hacerlo en cada frame en python puro,
            # pero intentaremos detectar cada 5 frames o si no es muy lento.
            # Por rendimiento, NO detectamos en el loop de GUI. Solo mostramos video.
            
            frame_rgb = cv2.cvtColor(frame_copy, cv2.COLOR_BGR2RGB)
            imagen_pil = Image.fromarray(frame_rgb)
            self.photo = ImageTk.PhotoImage(image=imagen_pil)
            self.label_video.config(image=self.photo)
            self.label_video.image = self.photo
        
        if self.running:
            self.root.after(30, self.actualizar_gui)

    def registrar_usuario(self):
        frame_procesar = None
        with self.lock:
            if self.frame_actual is not None:
                frame_procesar = self.frame_actual.copy()
                
        if frame_procesar is None:
            messagebox.showerror("Error", "La cámara no está lista o no disponible")
            return
            
        nombre = self.entry_nombre.get().strip()
        if not nombre or nombre == "Nombre Usuario":
            messagebox.showwarning("Error", "Escribe un nombre válido")
            return

        print(f"Registrando usuario: {nombre}")
        
        # 1. Detectar rostro
        face_data = CameraUtils.detectar_rostro(frame_procesar)
        
        if face_data is not None:
            # 2. Obtener encoding
            encoding = CameraUtils.obtener_encoding(frame_procesar, face_data)
            
            if encoding is not None:
                # 3. Recortar imagen para guardar (solo visual)
                cara_recortada = CameraUtils.recortar_rostro_visual(frame_procesar, face_data)
                cara_bytes = CameraUtils.convertir_a_bytes(cara_recortada)
                
                if cara_bytes:
                    UsuarioDAO.registrar_usuario(nombre, cara_bytes)
                    self.known_face_encodings.append(encoding)
                    self.known_face_names.append(nombre)
                    
                    messagebox.showinfo("Éxito", f"✓ Usuario '{nombre}' registrado correctamente")
                    self.entry_nombre.delete(0, tk.END)
                else:
                     messagebox.showerror("Error", "Error al procesar la imagen.")
            else:
                 messagebox.showerror("Error", "No se pudo extraer características del rostro.")
        else:
            messagebox.showerror("Error", "No se detectó ningún rostro.\n\nAsegúrate de estar bien iluminado y frente a la cámara.")

    def login_usuario(self):
        frame_procesar = None
        with self.lock:
            if self.frame_actual is not None:
                frame_procesar = self.frame_actual.copy()

        if frame_procesar is None:
            messagebox.showerror("Error", "La cámara no está lista o no disponible")
            return
        
        if not self.known_face_encodings:
            messagebox.showwarning("Sin usuarios", "No hay usuarios registrados o cargados.")
            return

        print("Intentando login...")
        
        face_data = CameraUtils.detectar_rostro(frame_procesar)
        
        if face_data is not None:
            encoding_actual = CameraUtils.obtener_encoding(frame_procesar, face_data)
            
            if encoding_actual is not None:
                nombre = CameraUtils.comparar_rostro_con_bd(self.known_face_encodings, self.known_face_names, encoding_actual)
                
                if nombre != "Desconocido":
                    messagebox.showinfo("✓ Bienvenido", f"Acceso concedido:\n\n{nombre}")
                else:
                    messagebox.showerror("❌ Acceso Denegado", "Usuario no reconocido")
            else:
                 messagebox.showerror("Error", "No se pudo leer el rostro correctamente.")
        else:
            messagebox.showerror("Error", "No se detectó ningún rostro.\n\nAsegúrate de estar frente a la cámara.")
    
    def cerrar_aplicacion(self):
        print("Cerrando aplicación...")
        self.running = False
        self.root.after(500, self.root.destroy)


if __name__ == "__main__":
    root = tk.Tk()
    app = BioPassApp(root)
    root.mainloop()
