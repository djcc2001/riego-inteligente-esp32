# entrenamiento/ — Entrenamiento del modelo

Notebook de Google Colab y datasets para entrenar el clasificador de humedad de suelo.

## Dataset

El conjunto de datos consolidado contiene **5178 muestras** distribuidas equitativamente:

| Clase | Muestras |
|---|---|
| SECO | 1726 |
| OPTIMO | 1726 |
| SATURADO | 1726 |

**Composición:** 180 muestras reales capturadas en Cusco (Julio 2026) + ~5000 muestras sintéticas generadas con aumentación por deriva térmica.

## Arquitectura

```
Input(3) → Dense(8, ReLU) → Dense(3, Softmax)
```

Variables de entrada: `soil_raw`, `temperatura`, `humedad ambiental`.

## Resultados

**Exactitud global: 99.42 %** sobre 1036 muestras de prueba.

| Clase | Precisión | Recall | F1-score | Soporte |
|---|---|---|---|---|
| OPTIMO | 1.00 | 0.98 | 0.99 | 351 |
| SATURADO | 0.98 | 1.00 | 0.99 | 343 |
| SECO | 1.00 | 1.00 | 1.00 | 342 |

## Archivos

| Archivo | Descripción |
|---|---|
| `entrenamiento.ipynb` | Notebook Colab con carga, entrenamiento, cuantización y exportación |
| `dataset_riego_etiquetado_entrenar.csv` | Dataset de entrenamiento (80 %) |
| `dataset_riego_etiquetado_prueba.csv` | Dataset de prueba (20 %) |

## Modelo exportado

El modelo cuantizado se encuentra en `riego_inferencia_esp32/include/modelo_riego.h` como arreglo C de 2280 bytes.
