import cv2
import numpy as np
import os

class CameraUtils:
    
    # Rutas a los modelos ONNX
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DETECTOR_PATH = os.path.join(BASE_DIR, "face_detection_yunet_2023mar.onnx")
    RECOGNIZER_PATH = os.path.join(BASE_DIR, "face_recognition_sface_2021dec.onnx")
    
    detector = None
    recognizer = None

    @classmethod
    def initialize_models(cls):
        """Inicializa los modelos DNN si no se han cargado."""
        if cls.detector is None:
            # YuNet Detector
            # Input size se actualiza dinámicamente, pero iniciamos con uno default
            try:
                cls.detector = cv2.FaceDetectorYN.create(
                    cls.DETECTOR_PATH,
                    "",
                    (320, 320),
                    0.9, # Score threshold
                    0.3, # NMS threshold
                    5000 
                )
                print("✅ Detector YuNet cargado.")
            except Exception as e:
                print(f"❌ Error cargando Detector YuNet: {e}")

        if cls.recognizer is None:
            try:
                cls.recognizer = cv2.FaceRecognizerSF.create(
                   cls.RECOGNIZER_PATH,
                   ""
                )
                print("✅ Recognizer SFace cargado.")
            except Exception as e:
                print(f"❌ Error cargando Recognizer SFace: {e}")

    @classmethod
    def detectar_rostro(cls, imagen):
        """
        Detecta rostros usando YuNet.
        Retorna la data del PRIMER rostro encontrado (coords + landmarks) o None.
        """
        if cls.detector is None: cls.initialize_models()
        if cls.detector is None: return None

        h, w, _ = imagen.shape
        cls.detector.setInputSize((w, h))
        
        # faces[1] es la lista de rostros. faces[0] es el status.
        _, faces = cls.detector.detect(imagen)
        
        if faces is not None and len(faces) > 0:
            # Retorna el primer rostro (array de 15 valores)
            return faces[0]
        return None

    @classmethod
    def obtener_encoding(cls, imagen, face_data):
        """
        Obtiene el vector de características (encoding) del rostro (128D).
        Requiere la imagen y la data del rostro (detectado por YuNet).
        """
        if cls.recognizer is None: cls.initialize_models()
        if cls.recognizer is None: return None
        
        # Alinear y recortar usando los landmarks
        aligned_face = cls.recognizer.alignCrop(imagen, face_data)
        
        # Extraer características
        encoding = cls.recognizer.feature(aligned_face)
        return encoding

    @classmethod
    def comparar_rostro_con_bd(cls, known_encodings, known_names, target_encoding, threshold=0.363):
        """
        Compara un encoding con una lista.
        Para Cosine Similarity (SFace), el threshold recomendado es ~0.363.
        Si score es MAYOR o IGUAL al threshold, es match positivo.
        """
        if cls.recognizer is None: cls.initialize_models()
        if not known_encodings: return "Sin usuarios"
        
        mejor_score = 0.0
        nombre_mejor = "Desconocido"

        for i, known_enc in enumerate(known_encodings):
            # match devuelve: 0 (mismo), 1 (diferente). 
            # Pero podemos usar la distancia cosenoidal manual si queremos, 
            # o usar recognizer.match(). SFace.match devuelve score de similitud (mayor es mejor) con FR_COSINE
            
            score = cls.recognizer.match(known_enc, target_encoding, cv2.FaceRecognizerSF_FR_COSINE)
            
            if score > mejor_score:
                mejor_score = score
                nombre_mejor = known_names[i]
        
        if mejor_score >= threshold:
            return nombre_mejor
            
        return "Desconocido"

    @staticmethod
    def convertir_a_bytes(imagen_cv2):
        """Para guardar el recorte del rostro (solo visual) en BD."""
        exito, buffer = cv2.imencode('.jpg', imagen_cv2)
        if exito:
            return buffer.tobytes()
        return None

    @staticmethod
    def bytes_a_imagen(imagen_bytes):
        nparr = np.frombuffer(imagen_bytes, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    @staticmethod
    def recortar_rostro_visual(imagen, face_data):
        """Recorta un cuadrado alrededor del rostro para guardar en BD (visual)."""
        # face_data = [x, y, w, h, ...]
        x, y, w, h = map(int, face_data[:4])
        # Añadir un poco de margen si es posible
        h_img, w_img, _ = imagen.shape
        x = max(0, x)
        y = max(0, y)
        w = min(w, w_img - x)
        h = min(h, h_img - y)
        return imagen[y:y+h, x:x+w]
