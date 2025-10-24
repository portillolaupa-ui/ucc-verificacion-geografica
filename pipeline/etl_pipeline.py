# ===============================================
# 🚀 Carga de datos y lectura desde YAML
# ===============================================

import pandas as pd
import yaml
from pathlib import Path

# === 1. Definir ruta base ===
BASE_DIR = Path(__file__).resolve().parents[1]

# === 2. Cargar archivo de configuración ===
with open(BASE_DIR / "pipeline" / "config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# === 3. Mostrar rutas de archivos detectadas ===
print("📂 Archivos configurados en el YAML:")
for k, v in config["paths"].items():
    print(f" - {k}: {v}")

# === 4. Intentar cargar cada dataset ===
dataframes = {}
for key, path_str in config["paths"].items():
    path = BASE_DIR / path_str
    if path.exists():
        try:
            df = pd.read_excel(path)
            dataframes[key] = df
            print(f"✅ {key} cargado correctamente con {len(df):,} filas y {len(df.columns)} columnas.")
        except Exception as e:
            print(f"❌ Error al leer {key}: {e}")
    else:
        print(f"⚠️ No se encontró el archivo: {path}")

# === 5. Resumen final ===
print("\nResumen de datasets cargados:")
for k, df in dataframes.items():
    print(f" - {k}: {df.shape[0]} filas × {df.shape[1]} columnas")

# ===============================================
# 📊 Reporte exploratorio 
# ===============================================

def reporte_rapido(df_dict):
    """Genera reporte exploratorio de cada DataFrame cargado"""
    for key, df in df_dict.items():
        print(f"\n📘 {key.upper()}")
        print("-" * 50)
        print(f"Filas: {len(df):,} | Columnas: {len(df.columns)}")
        print(f"Columnas: {list(df.columns)[:8]} ...")
        
        # Buscar columna de fecha
        col_fecha = next((c for c in df.columns if "FECHA" in c.upper()), None)
        if col_fecha:
            df[col_fecha] = pd.to_datetime(df[col_fecha], errors="coerce")
            print(f"Rango de fechas ({col_fecha}): {df[col_fecha].min()} → {df[col_fecha].max()}")
        else:
            print("No se encontró columna de fecha.")
        
        # Tipos de datos
        print("\nTipos de datos (primeras columnas):")
        print(df.dtypes.head(10))
        
        # Primeras filas
        print("\nVista previa (head):")
        print(df.head(3))
        print("\n" + "=" * 80)

# Ejecutar el reporte solo sobre los dataframes que ya cargaste
reporte_rapido(dataframes)