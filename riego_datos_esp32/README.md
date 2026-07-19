# riego_datos_esp32/ — Firmware de captura de datos

Firmware ligero para ESP32 que **solo captura datos crudos** de los sensores y los envía por puerto serial en formato CSV. No tiene modelo de inferencia.

Usado durante la fase de recolección del dataset.

## Diferencia con `riego_inferencia_esp32`

| | riego_datos_esp32 | riego_inferencia_esp32 |
|---|---|---|
| Propósito | Capturar datos crudos | Inferencia TinyML |
| Modelo TFLite | No | Sí |
| Salida | Serial (CSV) | HTTP POST + Serial |
| Conexión WiFi | No | Sí (WiFiManager) |

## Uso

```bash
# 1. Flashear el firmware
cd riego_datos_esp32
pio run --target upload

# 2. Capturar datos desde la PC
python3 captura/log_raw_data.py --estado seco --momento dia --muestras 30
```

## Salida serial

Cada 10 segundos imprime una línea CSV:

```
ts,soil_raw,temp,hum
14235,2340,22.5,31.2
15236,2338,22.6,31.1
...
```

## Hardware

| Sensor | Pin |
|---|---|
| HW-390 | GPIO34 |
| AHT10 (SDA) | GPIO21 |
| AHT10 (SCL) | GPIO22 |

## Estructura

```
riego_datos_esp32/
├── src/main.cpp      # Código principal
└── platformio.ini    # Configuración del proyecto
```
