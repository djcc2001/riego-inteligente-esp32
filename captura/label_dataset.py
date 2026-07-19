#!/usr/bin/env python3
"""
label_dataset.py

Carga dataset, grafica clusters, etiqueta por umbral
en 3 clases: SECO, OPTIMO, SATURADO.

Uso:
    python3 label_dataset.py
    python3 label_dataset.py --input dataset_completo_etiquetado.csv
    python3 label_dataset.py --dry 1950 --wet 1100 --no-plot
"""

import argparse
import csv
import sys

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

DRY_THRESHOLD = 1950
WET_THRESHOLD = 1100
INPUT_FILE = "dataset_completo_prueba.csv"
OUTPUT_FILE = "dataset_riego_etiquetado.csv"

CLASES = ["SECO", "OPTIMO", "SATURADO"]
COLORES_MAPA = {"SECO": "red", "OPTIMO": "gold", "SATURADO": "blue"}
# Mapeo de etiquetas reales del CSV a las 3 clases del modelo
MAPEO_REAL = {"seco": "SECO", "humedo": "OPTIMO", "humedo-mojado": "OPTIMO", "mojado": "SATURADO"}

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=INPUT_FILE)
    parser.add_argument("--output", default=OUTPUT_FILE)
    parser.add_argument("--dry", type=int, default=DRY_THRESHOLD)
    parser.add_argument("--wet", type=int, default=WET_THRESHOLD)
    parser.add_argument("--no-plot", action="store_true")
    return parser.parse_args()

def load_csv(filepath):
    rows = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def label_umbral(row, dry_th, wet_th):   # Umbral fijo: SECO≥dry / SATURADO≤wet / OPTIMO
    sr = int(row["soil_raw"])
    if sr >= dry_th:
        return "SECO"
    elif sr <= wet_th:
        return "SATURADO"
    else:
        return "OPTIMO"

def plot_clusters(rows, dry_th, wet_th):
    if plt is None:
        return

    tiene_estado = "estado" in rows[0]
    indices = list(range(len(rows)))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    if tiene_estado:
        for cl in CLASES:
            idxs = [i for i, r in enumerate(rows) if MAPEO_REAL.get(r.get("estado", "")) == cl]
            vals = [int(rows[i]["soil_raw"]) for i in idxs]
            ax1.scatter(idxs, vals, c=COLORES_MAPA[cl], label=cl, alpha=0.7, s=30)
    else:
        ax1.scatter(indices, [int(r["soil_raw"]) for r in rows], c="gray", alpha=0.7, s=30)

    ax1.axhline(y=dry_th, color="red", linestyle="--", linewidth=1.5, label=f"Umbral SECO (>= {dry_th})")
    ax1.axhline(y=wet_th, color="blue", linestyle="--", linewidth=1.5, label=f"Umbral SATURADO (<= {wet_th})")
    ax1.axhspan(wet_th, dry_th, alpha=0.08, color="green", label="OPTIMO")
    ax1.set_xlabel("Muestra #")
    ax1.set_ylabel("soil_raw (ADC)")
    ax1.set_title("Serie de tiempo - soil_raw coloreado por estado real")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    if tiene_estado:
        for cl in CLASES:
            pts = [(float(r["temp"]), int(r["soil_raw"])) for r in rows if MAPEO_REAL.get(r.get("estado", "")) == cl]
            if pts:
                temps, soils = zip(*pts)
                ax2.scatter(temps, soils, c=COLORES_MAPA[cl], label=cl, alpha=0.7, s=30)
        ax2.axhline(y=dry_th, color="red", linestyle="--", linewidth=1, alpha=0.5)
        ax2.axhline(y=wet_th, color="blue", linestyle="--", linewidth=1, alpha=0.5)
        ax2.set_xlabel("Temperatura (°C)")
        ax2.set_ylabel("soil_raw (ADC)")
        ax2.set_title("soil_raw vs Temperatura - coloreado por estado real")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

def matriz_confusion(rows, dry_th, wet_th):   # Matriz: umbral vs estado real
    predichos = [label_umbral(r, dry_th, wet_th) for r in rows]
    reales = [MAPEO_REAL.get(r.get("estado", "")) for r in rows]

    matriz = {r: {p: 0 for p in CLASES} for r in CLASES}
    for real, pred in zip(reales, predichos):
        if real and real in matriz:
            matriz[real][pred] += 1
    return matriz, reales, predichos

def mostrar_matriz(matriz, total):
    print(f"\n--- Matriz de confusion (umbral vs etiqueta real) ---")
    print(f"{'':>12} |", end="")
    for p in CLASES:
        print(f" {p:>8}", end="")
    print(f" | {'aciertos':>8}")
    print("-" * 60)
    aciertos = 0
    for real in CLASES:
        row = matriz[real]
        ok = row[real]
        aciertos += ok
        print(f"{real:>12} | {row['SECO']:>8} {row['OPTIMO']:>8} {row['SATURADO']:>8} | {ok:>4}/{sum(row.values()):<3}")
    print("-" * 60)
    print(f"{'Total':>12} | {'':>8} {'':>8} {'':>8} | {aciertos}/{total} ({aciertos*100//total}%)")

def main():
    args = parse_args()

    try:
        rows = load_csv(args.input)
    except FileNotFoundError:
        print(f"ERROR: No se encuentra {args.input}")
        sys.exit(1)

    if not rows:
        print(f"ERROR: El archivo {args.input} esta vacio.")
        sys.exit(1)

    print(f"Datos cargados: {len(rows)} lecturas desde {args.input}")

    soil_vals = [int(r["soil_raw"]) for r in rows]
    print(f"  soil_raw -> min: {min(soil_vals)}  max: {max(soil_vals)}  "
          f"promedio: {sum(soil_vals)//len(soil_vals)}")

    temp_vals = [float(r["temp"]) for r in rows]
    print(f"  temp     -> min: {min(temp_vals):.1f}  max: {max(temp_vals):.1f}  "
          f"promedio: {sum(temp_vals)/len(temp_vals):.1f}")

    if "estado" in rows[0]:
        print(f"\nEstadisticas por estado real (mapeado a 3 clases):")
        for cl in CLASES:
            soils = [int(r["soil_raw"]) for r in rows if MAPEO_REAL.get(r.get("estado", "")) == cl]
            if soils:
                print(f"  {cl:>10}: min={min(soils):>5} max={max(soils):>5} "
                      f"prom={sum(soils)//len(soils):>5} n={len(soils)}")

    if not args.no_plot:
        plot_clusters(rows, args.dry, args.wet)

    print(f"\nEtiquetando por umbral: SECO >= {args.dry}, SATURADO <= {args.wet}")
    labeled = []
    label_counts = {c: 0 for c in CLASES}
    for row in rows:
        label = label_umbral(row, args.dry, args.wet)
        row["label"] = label
        label_counts[label] += 1
        labeled.append(row)

    fieldnames = list(rows[0].keys())
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(labeled)

    print(f"\nDistribucion por umbral:")
    for lbl in CLASES:
        cnt = label_counts[lbl]
        print(f"  {lbl}: {cnt} ({cnt*100//len(rows)}%)")

    if "estado" in rows[0]:
        matriz, _, _ = matriz_confusion(rows, args.dry, args.wet)
        mostrar_matriz(matriz, len(rows))

    print(f"\nGuardado en {args.output}")

if __name__ == "__main__":
    main()
