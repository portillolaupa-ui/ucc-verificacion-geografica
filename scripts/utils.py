# scripts/utils.py
from haversine import haversine, Unit
import pandas as pd
import numpy as np

def calcular_distancia(row):
    """Calcula distancia en KM entre visita y hogar."""
    if pd.isna(row["LATITUD"]) or pd.isna(row["LONGITUD"]) \
       or pd.isna(row["X_LATITUD"]) or pd.isna(row["Y_LONGITUD"]):
        return np.nan
    return haversine(
        (row["LATITUD"], row["LONGITUD"]),
        (row["X_LATITUD"], row["Y_LONGITUD"]),
        unit=Unit.KILOMETERS
    )

def categoria_UT(ut):
    """Clasifica UT en Urbano, Andino o Amazónico."""
    urbano = ["LIMA", "LA LIBERTAD", "LAMBAYEQUE", "ICA","TACNA","MOQUEGUA","TUMBES","PIURA"]
    andino = ["CAJAMARCA","ANCASH","HUANCAVELICA","SAN MARTIN","AYACUCHO",
              "CUSCO","JUNIN","APURIMAC","PUNO","PASCO","AREQUIPA"]
    if ut in urbano: return "URBANO"
    elif ut in andino: return "ANDINO"
    else: return "AMAZONICO"

def clasificar_base(row):
    """Clasifica visita como válida o inconsistente según categoría."""
    cat = row["CATEGORIA"]
    dist = row["DISTANCIA_KM"]
    umbrales = {"URBANO": 0.5, "ANDINO": 2, "AMAZONICO": 5}
    return "VALIDA" if dist <= umbrales.get(cat, 5) else "INCONSISTENTE"