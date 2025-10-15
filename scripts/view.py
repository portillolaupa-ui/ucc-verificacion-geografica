import gdown
import pandas as pd

# URL de tu archivo público
url = "https://drive.google.com/uc?id=1F6XB759srLuTmF1xB4uhKnrVwGQEbTD4"
output = "df_seguro.pkl"

# Descargar archivo
gdown.download(url, output, quiet=False)

# Leerlo con pandas
df = pd.read_pickle(output)

pd.set_option('display.max_columns', None)   # muestra todas las columnas
pd.set_option('display.width', None)         # usa todo el ancho disponible
pd.set_option('display.max_colwidth', None)  # muestra el texto completo en celdas

print(df.columns.tolist())

# Ver estructura y columnas
print("Columnas:", df.columns.tolist())
print("Filas:", len(df))
print("Vista previa:")
print(df.head())