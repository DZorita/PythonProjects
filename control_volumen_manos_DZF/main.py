import cv2
import time
from dao.mongodb_dao import MongoDAO
from models.session import Session
from models.volume_event import VolumeEvent
from HandTrackingModule import HandDetector
from VolumeHandControl import VolumeController
from CameraCapture import CameraCapture

def main():
    print("Iniciando aplicación...")
    
    # 1. Initialize DB Connection
    dao = MongoDAO()
    db_ok = dao.client is not None
    if db_ok:
        print("DB: OK")
    else:
        print("Error al conectar con la base de datos.")

    # 2. Start Session
    session = Session()
    session_dict = session.to_dict()
    session_id = None
    if db_ok:
        result = dao.insert_session(session_dict)
        if result:
            session_id = result.inserted_id

    # 3. Setup Camera and Modules
    # Utilizando la nueva arquitectura robusta con hilos, fallbacks y locks
    cap = CameraCapture()
    if not cap.start():
        print("No se pudo iniciar la cámara. Saliendo...")
        return
    
    detector = HandDetector(detectionCon=0.7, maxHands=1)
    
    try:
        volume_ctrl = VolumeController()
    except Exception as e:
        print(f"Error initializing VolumeController: {e}")
        return

    vol = 0
    volBar = 400
    volPer = 0
    last_vol_per = -1

    # 4. Main Loop
    frame_count = 0
    while True:
        success, img = cap.read()
        if not success:
            print("Error: No se pudo capturar el frame de la cámara. Verifica lo siguiente:")
            print("1. Tu cámara está bien conectada y no está ocupada por otra app (Zoom, OBS, etc.).")
            print("2. Permisos de Privacidad de Windows: Configuración > Privacidad > Cámara > 'Permitir que las aplicaciones de escritorio accedan a la cámara'.")
            cv2.waitKey(3000)
            break
            
        frame_count += 1
        if frame_count % 30 == 0:
            print(f"Captured frame {frame_count}")
        
        img = detector.findHands(img)
        lmList, bbox = detector.findPosition(img, draw=False)
        
        # Check if frame is too dark (average pixel value < 10)
        mean_brightness = img.mean()
        if mean_brightness < 10:
            cv2.putText(img, "Camara oscura. Comprueba tu privacidad/tapa.", (10, 80), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.putText(img, "Permisos Windows OK? App de terceros usando cam?", (10, 110), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                        
        if len(lmList) != 0:
            fingers = detector.fingersUp()
            
            # El volumen cambiará usando la distancia entre el pulgar y el índice en todo momento
            if len(fingers) >= 2:
                # Calculate distance between thumb (4) and index (8)
                length, img, lineInfo = detector.findDistance(4, 8, img)
                
                # Set volume based on distance
                vol, volBar, volPer = volume_ctrl.set_volume(length, min_length=50, max_length=250)
                
                # Check for volume change to record it
                current_vol_per = int(volPer)
                if current_vol_per != last_vol_per:
                    if db_ok and last_vol_per != -1:
                        # Register volume event if it changed
                        event = VolumeEvent(previous_volume=last_vol_per, new_volume=current_vol_per, finger_distance=length, session_id=session_id)
                        dao.insert_volume_event(event.to_dict())
                    last_vol_per = current_vol_per

        # 5. UI Elements
        # Draw DB Status
        cv2.putText(img, f'DB: {"OK" if db_ok else "ERR"}', (10, 30), cv2.FONT_HERSHEY_COMPLEX, 1, 
                    (0, 255, 0) if db_ok else (0, 0, 255), 3)

        # Draw Volume Bar
        cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
        cv2.rectangle(img, (50, int(volBar)), (85, 400), (255, 0, 0), cv2.FILLED)
        cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX,
                    1, (255, 0, 0), 3)

        cv2.imshow("Hand Volume Control", img)
        
        # Check if window was closed by the user (clicking the X)
        if cv2.getWindowProperty("Hand Volume Control", cv2.WND_PROP_VISIBLE) < 1:
            break
        
        # Press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 6. Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    # End Session
    if session_id and db_ok:
        session.end_session()
        dao.update_session(session_id, session.to_dict())
        
    print("Aplicación terminada.")

if __name__ == "__main__":
    main()
