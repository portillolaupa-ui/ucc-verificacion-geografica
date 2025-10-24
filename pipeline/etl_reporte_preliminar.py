# ===============================================================
# 🧾 REPORTE EXPLORATORIO PREVIO A LIMPIEZA (v. final)
# ===============================================================

import pandas as pd
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

# === Configurar visualización en consola ===
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

# === 1️⃣ Cargar configuración ===
with open(BASE_DIR / "pipeline" / "config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# === 2️⃣ Cargar datasets ===
dataframes = {}
for key, path_str in config["paths"].items():
    path = BASE_DIR / path_str
    try:
        df = pd.read_excel(path)
        dataframes[key] = df
        print(f"✅ {key} cargado correctamente ({df.shape[0]:,} filas × {df.shape[1]} columnas)")
    except Exception as e:
        print(f"❌ Error al leer {key}: {e}")

# ===============================================================
# 1️⃣ Periodos de registros
# ===============================================================
print("\n📅 Periodos de registros (FECHA_REGISTRO_ATENCION):")
for name, df in dataframes.items():
    if "FECHA_REGISTRO_ATENCION" in df.columns:
        df["FECHA_REGISTRO_ATENCION"] = pd.to_datetime(df["FECHA_REGISTRO_ATENCION"], errors="coerce")
        print(f" - {name}: Min → {df['FECHA_REGISTRO_ATENCION'].min()} | Max → {df['FECHA_REGISTRO_ATENCION'].max()}")
    else:
        print(f" - {name}: (no tiene columna FECHA_REGISTRO_ATENCION)")

# ===============================================================
# 2️⃣ Resumen de forma
# ===============================================================
print("\n📏 Resumen de forma de cada DataFrame:")
for name, df in dataframes.items():
    print(f" - {name}: {df.shape[0]:,} filas × {df.shape[1]} columnas")

# ===============================================================
# 3️⃣ Comparación de tipos de datos
# ===============================================================
print("\n🧩 Comparación de tipos de datos entre DataFrames:")
all_cols = sorted(set().union(*[df.columns for df in dataframes.values()]))

comparacion = []
for col in all_cols:
    fila = {"columna": col}
    for name, df in dataframes.items():
        fila[f"{name}_dtype"] = str(df[col].dtype) if col in df.columns else "-"
    comparacion.append(fila)

df_types = pd.DataFrame(comparacion)
df_types.to_excel(BASE_DIR / "data/processed/resumen_tipos_columnas.xlsx", index=False)
print("📁 Exportado: resumen_tipos_columnas.xlsx")

# ===============================================================
# 4️⃣ Diccionario de columnas
# ===============================================================
print("\n📖 Generando diccionario de columnas...")

dict_frames = []
for name, df in dataframes.items():
    info = pd.DataFrame({
        "columna": df.columns,
        "dtype": df.dtypes.astype(str),
        "%_nulos": (df.isna().sum() / len(df) * 100).round(2),
        "valores_unicos": df.nunique()
    })
    info.insert(0, "dataframe", name)
    dict_frames.append(info)

df_diccionario = pd.concat(dict_frames, ignore_index=True)
output_dict_path = BASE_DIR / "data/processed/diccionario_columnas.xlsx"
df_diccionario.to_excel(output_dict_path, index=False)
print(f"📁 Exportado: diccionario_columnas.xlsx")

# ===============================================================
# 5️⃣ Valores únicos en columnas clave
# ===============================================================
cols_clave = ["TIPO_SEGUIMIENTO", "TIPO_MO", "TIPO_MO_1"]
for col in cols_clave:
    print(f"\n🔍 Valores únicos en '{col}':")
    for name, df in dataframes.items():
        if col in df.columns:
            uniques = df[col].dropna().unique()
            print(f"  {name}: {uniques}")
        else:
            print(f"  {name}: (no existe)")

# ===============================================================
# 6️⃣ Muestra visual (primeras 50 filas)
# ===============================================================
print("\n📘 Exportando muestras de las primeras 50 filas por DataFrame...")

sample_dir = BASE_DIR / "data/processed/muestras"
sample_dir.mkdir(parents=True, exist_ok=True)

for name, df in dataframes.items():
    sample_path = sample_dir / f"muestra_{name}.xlsx"
    df.head(50).to_excel(sample_path, index=False)
    print(f"📁 Guardado: {sample_path.name}")

print("\n✅ Reporte exploratorio completo. Archivos generados en 'data/processed/' y 'data/processed/muestras/'")