import pandas as pd

ruta1 = "data/raw/Data_Acompanamiento_2025_SET.xlsx"
dfprueba = pd.read_excel(ruta1, parse_dates=["FECHA_REGISTRO_ATENCION"])
print(dfprueba['FECHA_REGISTRO_ATENCION'].min())
print(dfprueba['FECHA_REGISTRO_ATENCION'].max())