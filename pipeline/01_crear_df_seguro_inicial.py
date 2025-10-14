import pandas as pd
from pathlib import Path

# ========= CONFIGURA AQUÍ el nombre de tu archivo original =========
INPUT_FILE = Path("data/incoming/df_distancia_2025_09.pkl")
OUTPUT_FILE = Path("data/df_seguro.pkl")

# ========= Columnas mínimas que necesita tu dashboard =========
COLS_SEGURAS = [
    "UT", "DISTRITO", "CENTRO_POBLADO", "CATEGORIA",
    "GEL", "CO_HOGAR", "ESCALA_PRIORIZACION",
    "FECHA_REGISTRO_ATENCION", "DISTANCIA_KM"
]

def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"No encuentro el archivo de entrada: {INPUT_FILE}")

    print(f"📥 Cargando: {INPUT_FILE}")
    df = pd.read_pickle(INPUT_FILE)

    # 1) Verificación básica
    faltantes = [c for c in COLS_SEGURAS if c not in df.columns]
    if faltantes:
        raise KeyError(f"Faltan columnas necesarias para el dashboard: {faltantes}")

    # 2) Quedarnos SOLO con las columnas necesarias
    df_seguro = df[COLS_SEGURAS].copy()

    # 3) Normalizaciones suaves (mejor experiencia visual, sin tocar datos críticos)
    df_seguro["UT"] = df_seguro["UT"].astype(str).str.strip().str.upper()
    df_seguro["DISTRITO"] = df_seguro["DISTRITO"].astype(str).str.strip().str.title()
    df_seguro["CENTRO_POBLADO"] = df_seguro["CENTRO_POBLADO"].astype(str).str.strip().str.title()
    df_seguro["CATEGORIA"] = df_seguro["CATEGORIA"].astype(str).str.strip().str.upper()
    df_seguro["GEL"] = df_seguro["GEL"].astype(str).str.strip().str.title()
    df_seguro["CO_HOGAR"] = df_seguro["CO_HOGAR"].astype(str).str.strip()

    # 4) Tipos seguros
    df_seguro["FECHA_REGISTRO_ATENCION"] = pd.to_datetime(
        df_seguro["FECHA_REGISTRO_ATENCION"], errors="coerce"
    )
    # Forzar numérico DISTANCIA_KM (por si llega con coma)
    df_seguro["DISTANCIA_KM"] = (
        df_seguro["DISTANCIA_KM"]
        .astype(str).str.replace(",", ".", regex=False)
        .astype(float)
    )

    # 5) Guardar
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_seguro.to_pickle(OUTPUT_FILE)

    # 6) Resumen útil
    print("✅ df_seguro.pkl creado correctamente.")
    print(f"   Ruta: {OUTPUT_FILE}")
    print(f"   Filas: {len(df_seguro):,}  |  Columnas: {len(df_seguro.columns)}")
    print("   Columnas:", ", ".join(df_seguro.columns))

if __name__ == "__main__":
    main()
