#!/usr/bin/env python3
"""
log_raw_data.py

Lectura del puerto serial del ESP32 con metadatos de sesion.
Guarda SIEMPRE en dataset_riego_raw.csv (append) con columnas estado y momento.
Filtra errores del sensor AHT10 en tiempo real.

Uso:
    python3 log_raw_data.py --estado seco --momento dia --muestras 20
    python3 log_raw_data.py --estado humedo --momento tarde --muestras 15
    python3 log_raw_data.py --estado mojado --momento noche

Flags:
    --estado   seco | humedo | mojado
    --momento  dia | tarde | noche
    --muestras N     (opcional, se detiene solo al llegar a N)
    --port     /dev/ttyUSB0 (auto-detect si no se especifica)
    --baud     115200 (default)
"""

import argparse
import csv
import os
import time
from datetime import datetime
import serial
import serial.tools.list_ports

ESTADOS_VALIDOS = ["seco", "humedo", "mojado"]
MOMENTOS_VALIDOS = ["dia", "tarde", "noche"]

def detect_port():     # Auto-deteccion del puerto USB del ESP32
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if "USB" in p.description or "CP210" in p.description or "CH340" in p.description:
            return p.device
    return None

def validar_lectura(soil_raw, temp, hum):   # Filtro: descarta sensores fuera de rango
    """Retorna True si la lectura es fisicamente valida."""
    try:
        sr = float(soil_raw)
        t = float(temp)
        h = float(hum)
        if sr < 0 or sr > 4095:
            return False
        if t < -10 or t > 60:
            return False
        if h < 0 or h > 100:
            return False
        return True
    except ValueError:
        return False

def parse_args():
    parser = argparse.ArgumentParser(description="Captura datos crudos del ESP32 con etiqueta de sesion")
    parser.add_argument("--estado", required=True, choices=ESTADOS_VALIDOS,
                        help="Estado del suelo en esta sesion")
    parser.add_argument("--momento", required=True, choices=MOMENTOS_VALIDOS,
                        help="Momento del dia")
    parser.add_argument("--muestras", type=int, default=0,
                        help="Detenerse automaticamente tras N muestras (0 = infinito)")
    parser.add_argument("--port", default=None, help="Puerto serial (ej: /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate")
    return parser.parse_args()

def main():
    args = parse_args()
    port = args.port or detect_port()

    if not port:
        print("ERROR: No se pudo detectar el puerto del ESP32.")
        print("Usa --port para especificarlo manualmente.")
        return

    filename = "dataset_riego_raw.csv"
    SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(SCRIPTS_DIR, filename)
    file_exists = os.path.isfile(filepath)

    print(f"Conectando a {port} a {args.baud} baud...")
    print(f"Estado: {args.estado} | Momento: {args.momento}")
    print(f"Guardando en: {filename}")
    if args.muestras > 0:
        print(f"Se detendra automaticamente tras {args.muestras} muestras.")
    print("Presiona Ctrl+C para detener antes.")

    HEADER = ["ts_real", "ts_esp32", "soil_raw", "temp", "hum", "estado", "momento"]

    with serial.Serial(port, args.baud, timeout=2) as ser, \
         open(filepath, "a", newline="") as f:

        writer = csv.writer(f)
        if not file_exists or os.path.getsize(filepath) == 0:
            writer.writerow(HEADER)
            print("Nuevo archivo, escribiendo encabezado.")

        f.flush()
        time.sleep(2)
        ser.reset_input_buffer()

        count = 0
        filtrados = 0
        try:                     # Bucle principal: lectura serial, validacion, escritura CSV
            while True:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                if line.startswith("ts") or line.startswith("ERROR") or line.startswith("Adafruit"):
                    continue

                parts = line.split(",")
                if len(parts) != 4:
                    continue

                ts_esp32, soil_raw, temp, hum = parts

                if not validar_lectura(soil_raw, temp, hum):
                    filtrados += 1
                    print(f"[FILTRADO] soil={soil_raw} temp={temp} hum={hum}")
                    continue

                ts_real = datetime.now().isoformat()
                writer.writerow([ts_real, ts_esp32, soil_raw, temp, hum, args.estado, args.momento])
                f.flush()
                count += 1
                print(f"[{count}] {ts_real} | soil={soil_raw} temp={temp} hum={hum} | {args.estado} {args.momento}")

                if args.muestras > 0 and count >= args.muestras:
                    print(f"\nAlcanzadas {args.muestras} muestras. Deteniendo.")
                    break

        except KeyboardInterrupt:
            print(f"\nInterrupcion manual.")

    print(f"Total: {count} guardadas, {filtrados} filtradas en {filename}.")

if __name__ == "__main__":
    main()
