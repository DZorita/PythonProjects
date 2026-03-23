import cv2
import time
import threading

class CameraCapture:
    """
    Clase que encapsula la cámara usando hilos, locks, fallbacks 
    y frame-warmup para un rendimiento fluido.
    """
    def __init__(self):
        self.cap = None
        self.frame = None
        # 5. Actualización segura sin colisiones (Locks)
        self.lock = threading.Lock()
        self.running = False
        self.thread = None

    def start(self):
        # 2. Búsqueda intensiva de la cámara (Fallbacks)
        configs = [
            (0, cv2.CAP_DSHOW),
            (0, cv2.CAP_MSMF),
            (0, cv2.CAP_ANY),
            (1, cv2.CAP_DSHOW),
            (1, cv2.CAP_ANY)
        ]
        
        for index, backend in configs:
            print(f"Intentando abrir cámara {index} con backend {backend}...")
            self.cap = cv2.VideoCapture(index, backend)
            if self.cap.isOpened():
                print(f"Cámara conectada exitosamente (Index: {index})")
                break
                
        if not self.cap or not self.cap.isOpened():
            print("ERROR: No se pudo abrir ninguna cámara.")
            return False
            
        # 3. "Despertar" la cámara forzando la resolución
        print("Forzando resolución para despertar el sensor...")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # 4. Frames de "Calentamiento"
        print("Calentando la cámara (descartando frames oscuros iniciales)...")
        for i in range(60):
            ret, tmp_frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = tmp_frame.copy()
            time.sleep(0.01)
            
        print("Calentamiento terminado.")
        
        self.running = True
        # 1. Dos cerebros trabajando a la vez (Hilos separados)
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        return True

    def _update(self):
        """Bucle que corre en un hilo separado para capturar imágenes continuamente."""
        while self.running:
            if self.cap is not None and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    with self.lock:
                        self.frame = frame.copy()
            # Un pequeño sleep ayuda a que el hilo no consuma 100% de CPU innecesariamente
            time.sleep(0.01)
            
    def read(self):
        """Lee el último frame capturado de forma segura."""
        with self.lock:
            if self.frame is not None:
                return True, self.frame.copy() # Devolvemos una copia por seguridad
            return False, None
            
    def release(self):
        """Detiene el hilo y libera el recurso de la cámara."""
        self.running = False
        if self.thread is not None:
            self.thread.join()
        if self.cap is not None:
            self.cap.release()
