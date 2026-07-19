# captura/ — Recolección y etiquetado de datos

Scripts para capturar datos seriales del ESP32, etiquetarlos con el estado real del sustrato y generar el dataset de entrenamiento.

## Scripts

### `log_raw_data.py`

Lee el puerto serial del ESP32, valida las lecturas y las guarda en `dataset_riego_raw.csv`.

```bash
# Seco en la mañana, 20 muestras
python3 log_raw_data.py --estado seco --momento dia --muestras 20

# Humedo en la tarde, infinito hasta Ctrl+C
python3 log_raw_data.py --estado humedo --momento tarde

# Mojado en la noche, 15 muestras
python3 log_raw_data.py --estado mojado --momento noche --muestras 15
```

**Flags:**
| Flag | Valores |
|---|---|
| `--estado` | `seco`, `humedo`, `mojado` |
| `--momento` | `dia`, `tarde`, `noche` |
| `--muestras` | N (0 = infinito) |
| `--port` | Puerto serial (auto-detecta) |

### `label_dataset.py`

Carga el CSV crudo, aplica umbrales fijos para etiquetar en 3 clases y genera gráficos de dispersión.

```bash
python3 label_dataset.py --dry 1950 --wet 1100
```

**Salida:** `dataset_riego_etiquetado.csv` con columna `label` adicional.

### `parametros_augmentacion.txt`

Parámetros de deriva térmica por clase usados para aumentar el dataset sintético:

| Clase | Drift (pts/°C) |
|---|---|
| SECO | 110 |
| OPTIMO | 80 |
| SATURADO | 30 |

## Archivos generados

| Archivo | Contenido |
|---|---|
| `dataset_riego_raw.csv` | Lecturas crudas con estado y momento |
| `dataset_riego_etiquetado.csv` | Mismo dataset con etiqueta de umbral |
| `dataset_completo_etiquetado.csv` | Dataset real de 180 muestras |
