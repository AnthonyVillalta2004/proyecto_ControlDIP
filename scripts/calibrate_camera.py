import cv2
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.camera.v4l2_config import V4L2Configurator
from src.processing.calibrator import PlateCalibrator

# Variables globales para los clics del mouse
clicked_points = []

def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(clicked_points) < 4:
            clicked_points.append((x, y))
            print(f"Punto registrado: ({x}, {y})")

def main():
    print("Iniciando Calibración...")
    # 1. Configurar Hardware (igual que en el benchmark)
    cam_config = V4L2Configurator("/dev/video0")
    cam_config.disable_auto_features()
    cam_config.set_exposure(157) # Reemplaza por tu valor ideal

    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("Error al abrir la cámara.")
        return

    # Leer un frame estabilizado (descartamos los primeros 10)
    for _ in range(10):
        cap.read()
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("Error al capturar imagen.")
        return

    # 2. Interfaz gráfica para hacer clic
    clone = frame.copy()
    cv2.namedWindow("Calibracion")
    cv2.setMouseCallback("Calibracion", mouse_callback)

    print("\nINSTRUCCIONES:")
    print("Haz clic en las 4 marcas (esquinas) del plato en este orden exacto:")
    print("1. Superior Izquierda")
    print("2. Superior Derecha")
    print("3. Inferior Derecha")
    print("4. Inferior Izquierda")
    print("Presiona 'c' para confirmar o 'r' para reiniciar los puntos.")

    while True:
        img_display = clone.copy()
        
        # Dibujar los puntos seleccionados
        for i, pt in enumerate(clicked_points):
            cv2.circle(img_display, pt, 5, (0, 255, 0), -1)
            cv2.putText(img_display, str(i+1), (pt[0]+10, pt[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            # Dibujar lineas conectando
            if i > 0:
                cv2.line(img_display, clicked_points[i-1], clicked_points[i], (255, 0, 0), 2)
            if len(clicked_points) == 4:
                cv2.line(img_display, clicked_points[3], clicked_points[0], (255, 0, 0), 2)

        cv2.imshow("Calibracion", img_display)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('r'):
            clicked_points.clear()
            print("Puntos reiniciados.")
        elif key == ord('c') and len(clicked_points) == 4:
            break
        elif key == ord('q'):
            cv2.destroyAllWindows()
            return

    cv2.destroyAllWindows()

    # 3. Calcular y guardar
    calibrator = PlateCalibrator(plate_size_mm=300.0)
    calibrator.calculate_homography(clicked_points)
    calibrator.save_calibration("calibration_matrix.npy")
    print("¡Calibración exitosa! La matriz ha sido guardada.")

if __name__ == "__main__":
    main()