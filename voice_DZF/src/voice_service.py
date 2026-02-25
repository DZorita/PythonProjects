import speech_recognition as sr
import sounddevice as sd
import soundfile as sf
import numpy as np
import scipy.io.wavfile as wav_io
import tempfile
import time
import os

# Parámetros de grabación
SAMPLE_RATE = 16000   # 16 kHz — óptimo para reconocimiento de voz
CHANNELS    = 1       # Mono
DURACION_SEC = 6      # Segundos máximos de grabación por intento


class VoiceService:
    """
    Patrón Facade: Oculta la complejidad del manejo del micrófono
    y la conexión con el motor de reconocimiento de Google Web Speech.

    Usa 'sounddevice' como backend de audio (compatible con Python 3.14)
    en lugar de PyAudio, que aún no tiene wheels para Python 3.14.
    """

    def __init__(self):
        self.reconocedor = sr.Recognizer()
        self.reconocedor.energy_threshold = 300
        self.reconocedor.dynamic_energy_threshold = True

    def capturar_frase(self, duracion: float = DURACION_SEC) -> dict:
        """
        Graba audio con sounddevice, lo convierte a WAV temporal y
        lo envía al motor de Google Speech API.

        Devuelve un diccionario con:
            - texto (str): Frase reconocida
            - confianza (float): Grado de confianza del motor (0.0 – 1.0)
            - latencia_ms (int): Tiempo de respuesta en milisegundos
            - error (str | None): Mensaje de error si ocurrió alguno
        """
        resultado = {
            "texto": "",
            "confianza": 0.0,
            "latencia_ms": 0,
            "error": None
        }

        tmp_path = None
        try:
            print(f"[Voz] Grabando {duracion} segundos… habla ahora.")
            inicio = time.time()

            # ── Grabar con sounddevice ──────────────────────────────────────
            grabacion = sd.rec(
                int(duracion * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16"
            )
            sd.wait()  # Bloquea hasta que termina la grabación

            # ── Guardar en WAV temporal ─────────────────────────────────────
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_path = tmp.name
            tmp.close()
            wav_io.write(tmp_path, SAMPLE_RATE, grabacion)

            # ── Enviar a Google Speech API ──────────────────────────────────
            with sr.AudioFile(tmp_path) as fuente:
                audio = self.reconocedor.record(fuente)

            respuesta_raw = self.reconocedor.recognize_google(
                audio,
                language="es-ES",
                show_all=True
            )

            fin = time.time()
            resultado["latencia_ms"] = int((fin - inicio) * 1000)

            if respuesta_raw and "alternative" in respuesta_raw:
                mejor = respuesta_raw["alternative"][0]
                resultado["texto"]     = mejor.get("transcript", "").strip().lower()
                resultado["confianza"] = round(mejor.get("confidence", 0.85), 4)
            elif isinstance(respuesta_raw, str) and respuesta_raw:
                resultado["texto"]     = respuesta_raw.strip().lower()
                resultado["confianza"] = 0.85
            else:
                resultado["error"] = "No se pudo reconocer ninguna frase"

        except sr.UnknownValueError:
            resultado["error"] = "No se pudo entender el audio (habla más claro)"
        except sr.RequestError as e:
            resultado["error"] = f"Error de conexión con Google: {e}"
        except sd.PortAudioError as e:
            resultado["error"] = f"Error de micrófono (PortAudio): {e}"
        except Exception as e:
            resultado["error"] = f"Error inesperado: {e}"
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

        return resultado
