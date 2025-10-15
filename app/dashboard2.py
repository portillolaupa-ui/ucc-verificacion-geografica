# ======================================================
# 📊 Verificación Geográfica de Visitas Domiciliarias – UCC (v8.4)
# ======================================================

import streamlit as st
import pandas as pd
import numpy as np
import io
import base64
import os

# ======================
# CONFIGURACIÓN GENERAL
# ======================
st.set_page_config(page_title="Verificación Geográfica – UCC", layout="wide")

COLOR_PRINCIPAL = "#004C97"
COLOR_BORDE = "#E8EEF5"

# ======================================================
# 📂 CARGA DE DATOS (sin dependencias externas)
# ======================================================
@st.cache_data(show_spinner=True)
def cargar_datos():
    ruta_archivo = os.path.join("data", "processed", "df_seguro.csv.gz")

    if not os.path.exists(ruta_archivo):
        st.error("❌ No se encontró el archivo 'df_seguro.csv.gz' en la carpeta 'data/processed'.")
        st.stop()

    with st.spinner("Cargando datos, por favor espera..."):
        df = pd.read_csv(ruta_archivo, compression="gzip")

    # Limpieza básica
    df["CATEGORIA"] = df["CATEGORIA"].str.upper().str.strip()
    if not pd.api.types.is_datetime64_any_dtype(df["FECHA_REGISTRO_ATENCION"]):
        df["FECHA_REGISTRO_ATENCION"] = pd.to_datetime(df["FECHA_REGISTRO_ATENCION"], errors="coerce")

    st.caption(f"✅ Datos cargados correctamente: {len(df):,} registros.")
    return df

df = cargar_datos()

# ======================================================
# 📅 PERIODOS OPERATIVOS
# ======================================================
PERIODOS = {
    "DICIEMBRE_2024": ("2024-12-18", "2025-01-15"),
    "ENERO_2025": ("2025-01-16", "2025-02-12"),
    "FEBRERO_2025": ("2025-02-13", "2025-03-19"),
    "MARZO_2025": ("2025-03-20", "2025-04-15"),
    "ABRIL_2025": ("2025-04-16", "2025-05-14"),
    "MAYO_2025": ("2025-05-15", "2025-06-11"),
    "JUNIO_2025": ("2025-06-12", "2025-07-07"),
    "JULIO_2025": ("2025-07-08", "2025-08-12"),
    "AGOSTO_2025": ("2025-08-13", "2025-09-16"),
}

# ======================================================
# 🎛️ ENCABEZADO Y FILTROS
# ======================================================
st.markdown(f"""
<h1 style="text-align:center;color:{COLOR_PRINCIPAL};margin-bottom:6px;">
Verificación Geográfica de Visitas Domiciliarias – UCC
</h1>
<p style="text-align:center;color:gray;margin-top:0;">
<b>Herramienta de validación geográfica</b> de las visitas domiciliarias para fortalecer la verificación territorial.
</p>
""", unsafe_allow_html=True)

colf1, colf2, colf3 = st.columns([1.2, 1, 1.1])
with colf1:
    periodo_sel = st.selectbox("📆 Periodo operativo", ["-- Selecciona --"] + list(PERIODOS.keys()))
with colf2:
    ut_sel = st.selectbox("🏙️ Unidad Territorial (UT)", ["-- Todas --"] + sorted(df["UT"].unique()))

# ✅ Filtro dinámico de distritos según la UT seleccionada
if ut_sel != "-- Todas --":
    distritos_filtrados = sorted(df[df["UT"] == ut_sel]["DISTRITO"].unique())
else:
    distritos_filtrados = sorted(df["DISTRITO"].unique())

with colf3:
    dist_sel = st.selectbox("📍 Distrito", ["-- Todos --"] + distritos_filtrados)

if periodo_sel == "-- Selecciona --":
    st.info("Selecciona un periodo operativo para visualizar los resultados.")
    st.stop()

fecha_inicio_str, fecha_fin_str = PERIODOS[periodo_sel]
fecha_inicio = pd.to_datetime(fecha_inicio_str)
fecha_fin = pd.to_datetime(fecha_fin_str)

# ======================================================
# 🧮 FILTRADO BASE
# ======================================================
@st.cache_data(show_spinner=False)
def filtrar_periodo_prioridad(df, fi, ff, ut, dist):
    dfp = df[
        (df["FECHA_REGISTRO_ATENCION"] >= fi)
        & (df["FECHA_REGISTRO_ATENCION"] <= ff)
        & (df["ESCALA_PRIORIZACION"].isin([4, 5]))
    ].copy()
    if ut != "-- Todas --":
        dfp = dfp[dfp["UT"] == ut]
    if dist != "-- Todos --":
        dfp = dfp[dfp["DISTRITO"] == dist]
    return dfp

df_periodo = filtrar_periodo_prioridad(df, fecha_inicio, fecha_fin, ut_sel, dist_sel)

# ======================================================
# 🚨 VALIDACIÓN DE UBICACIÓN
# ======================================================
def marcar_alerta(row):
    try:
        categoria = str(row["CATEGORIA"]).upper().strip()
        distancia = float(row["DISTANCIA_KM"])
        if categoria == "URBANO" and distancia > 0.5:
            return "🔴 Ubicación no válida"
        elif categoria == "ANDINO" and distancia > 2:
            return "🔴 Ubicación no válida"
        elif categoria == "AMAZONICO" and distancia > 5:
            return "🔴 Ubicación no válida"
        else:
            return "🟢 Ubicación válida"
    except Exception:
        return "❌ Error de datos"

df_periodo["DISTANCIA_KM"] = pd.to_numeric(df_periodo["DISTANCIA_KM"], errors="coerce")
df_periodo["ALERTA"] = df_periodo.apply(marcar_alerta, axis=1).astype(str)
df_rojo = df_periodo[df_periodo["ALERTA"].str.contains("no válida", case=False, na=False)].copy()

# ======================================================
# 📢 RESUMEN DE VALIDACIÓN (Ahora aparece primero)
# ======================================================
if len(df_periodo) > 0:
    total_visitas = len(df_periodo)
    porcentaje_fuera = round((len(df_rojo) / total_visitas * 100), 1)

    # Ranking preliminar para vincular niveles de riesgo
    den = df_periodo.groupby("GEL").size().rename("total")
    num = df_rojo.groupby("GEL").size().rename("no_valida")
    resumen = pd.concat([den, num], axis=1).fillna(0)
    resumen["%"] = (resumen["no_valida"] / resumen["total"] * 100).round(1)
    ranking_tmp = resumen.reset_index()
    ranking_tmp["nivel"] = ranking_tmp["%"].apply(
        lambda v: "critico" if v >= 70 else "alto" if v >= 50 else "medio" if v >= 30 else "bajo"
    )

    gestores_critico = ranking_tmp[ranking_tmp["nivel"] == "critico"]
    gestores_alto = ranking_tmp[ranking_tmp["nivel"] == "alto"]
    gestores_medio = ranking_tmp[ranking_tmp["nivel"] == "medio"]

    if ut_sel == "-- Todas --":
        lugar = "en el programa"
    elif dist_sel == "-- Todos --":
        lugar = f"en la UT {ut_sel}"
    else:
        lugar = f"en el distrito de {dist_sel} (UT {ut_sel})"

    texto_base = f"""
    En el periodo **{periodo_sel.replace('_', ' ')}**, el **{porcentaje_fuera:.1f}%** de las visitas domiciliarias registradas {lugar} se realizaron **fuera del rango territorial permitido**  
    (urbano > 0.5 km, andino > 2 km, amazónico > 5 km).
    """

    if len(gestores_critico) > 0:
        texto_riesgo = f"🔴 **{len(gestores_critico)} gestores locales** registran más del **70 %** de sus visitas fuera del rango permitido (**riesgo crítico**)."
        color_fondo = "#FDEDEC"; color_borde = "#E74C3C"
    elif len(gestores_alto) > 0:
        texto_riesgo = f"🟠 **{len(gestores_alto)} gestores locales** presentan entre **50 % y 70 %** (**riesgo alto**)."
        color_fondo = "#FEF5E7"; color_borde = "#F39C12"
    elif len(gestores_medio) > 0:
        texto_riesgo = f"🟡 **{len(gestores_medio)} gestores locales** tienen entre **30 % y 50 %** (**riesgo medio**)."
        color_fondo = "#FCF3CF"; color_borde = "#F1C40F"
    else:
        texto_riesgo = "🟢 No se registran gestores con niveles altos o críticos. La mayoría presenta un **nivel de riesgo bajo**."
        color_fondo = "#E8F8F5"; color_borde = "#1ABC9C"

    texto_final = f"📊 *Basado en {total_visitas:,} visitas priorizadas (niveles 4 y 5).*"

    st.markdown(f"""
    <div style='background:{color_fondo};border-left:6px solid {color_borde};
                border-radius:10px;padding:18px 20px;margin-top:10px;
                font-size:16px;line-height:1.6;color:#1B2631;'>
        <b>📢 Resumen de validación territorial</b><br>
        <span style='font-size:14px;color:gray;'>Periodo: {periodo_sel.replace('_',' ')} | {lugar}</span><br><br>
        {texto_base}<br><br>
        {texto_riesgo}<br><br>
        <em style='color:gray;'>{texto_final}</em>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("No se registran visitas durante el periodo seleccionado.")

# ======================================================
# 🎯 TARJETAS KPI
# ======================================================
st.markdown("---")
st.subheader("📍 Indicadores principales")

total_no_valida = len(df_rojo)
gestores_involucrados = df_rojo["GEL"].nunique()
hogares_afectados = df_rojo["CO_HOGAR"].nunique()

kpi_style = f"""
background:linear-gradient(180deg,#F4F6F7,#E8EEF5);
border-left:6px solid {COLOR_PRINCIPAL};
padding:14px 16px;border-radius:10px;
text-align:center;line-height:1.3;
"""

def kpi_html(icono, texto, valor):
    return f"""
    <div style='{kpi_style}'>
        {icono}<br>
        <span style='font-size:16px;color:#555;'>{texto}</span><br>
        <span style='font-size:40px;font-weight:700;color:#2E4053;'>{valor:,}</span>
    </div>
    """

c1, c2, c3 = st.columns(3)
with c1: st.markdown(kpi_html("🔴", "Visitas con ubicación no válida", total_no_valida), unsafe_allow_html=True)
with c2: st.markdown(kpi_html("👤", "Gestores con registros no válidos", gestores_involucrados), unsafe_allow_html=True)
with c3: st.markdown(kpi_html("🏠", "Hogares con ubicación no válida", hogares_afectados), unsafe_allow_html=True)

# ======================================================
# 👥 GESTORES CON MAYOR INCIDENCIA
# ======================================================
st.markdown("---")
st.subheader("👥 Gestores con mayor proporción de visitas fuera de ubicación")
st.caption("ℹ️ Muestra los gestores con mayor incidencia de registros fuera del rango territorial permitido, para prioridad 4 y 5.")

if len(df_periodo) > 0:
    den = df_periodo.groupby("GEL").size().rename("total")
    num = df_rojo.groupby("GEL").size().rename("no_valida")
    resumen = pd.concat([den, num], axis=1).fillna(0)
    resumen["%"] = (resumen["no_valida"] / resumen["total"] * 100).round(1)

    ut_modal = df_periodo.groupby("GEL")["UT"].agg(lambda x: x.mode().iat[0] if not x.mode().empty else "")
    dist_modal = df_periodo.groupby("GEL")["DISTRITO"].agg(lambda x: x.mode().iat[0] if not x.mode().empty else "")
    resumen = resumen.join(ut_modal, on="GEL").join(dist_modal, on="GEL")
    resumen = resumen[resumen["total"] >= 5].sort_values(by=["%", "no_valida"], ascending=[False, False]).reset_index()

    ranking = resumen.rename(columns={
        "GEL": "Gestor Local",
        "UT": "UT",
        "DISTRITO": "Distrito",
        "total": "Total visitas (pri 4-5)",
        "no_valida": "Visitas fuera de ubicación",
        "%": "% fuera de ubicación"
    })

    ranking["nivel"] = ranking["% fuera de ubicación"].apply(
        lambda v: "critico" if v >= 70 else "alto" if v >= 50 else "medio" if v >= 30 else "bajo"
    )

    def color_riesgo(val):
        if val >= 70: return f"🔴 {val:.1f}"
        elif val >= 50: return f"🟠 {val:.1f}"
        elif val >= 30: return f"🟡 {val:.1f}"
        else: return f"🟢 {val:.1f}"

    ranking["% fuera de ubicación"] = ranking["% fuera de ubicación"].apply(color_riesgo)

    def color_fila(row):
        pct = float(row["% fuera de ubicación"][2:]) if len(row["% fuera de ubicación"]) > 2 else 0
        if pct >= 70: return ['background-color: #FADBD8'] * len(row)
        elif pct >= 50: return ['background-color: #FDEBD0'] * len(row)
        elif pct >= 30: return ['background-color: #FCF3CF'] * len(row)
        else: return ['background-color: #E8F8F5'] * len(row)

    st.dataframe(
        ranking[["Gestor Local", "UT", "Distrito",
                "Total visitas (pri 4-5)",
                "Visitas fuera de ubicación", "% fuera de ubicación"]]
        .style.apply(color_fila, axis=1),
        use_container_width=True
    )
else:
    ranking = pd.DataFrame()
    st.info("No hay registros disponibles para el periodo seleccionado.")

# ======================================================
# 🏠 REGISTROS DE VISITAS
# ======================================================
st.markdown("---")
st.subheader("🏠 Registros de visitas con ubicación no válida")
st.caption("ℹ️ Permite revisar y filtrar los registros específicos de hogares con visitas fuera del rango permitido, para prioridad 4 y 5.")

if df_rojo.empty:
    st.info("No se registran visitas con ubicación no válida en el periodo seleccionado.")
else:
    colf1, colf2 = st.columns([1.2, 1])

    # ✅ Filtro dinámico de gestores según UT/Distrito seleccionado
    if ut_sel != "-- Todas --":
        gestores_filtrados = sorted(df_rojo[df_rojo["UT"] == ut_sel]["GEL"].unique())
    elif dist_sel != "-- Todos --":
        gestores_filtrados = sorted(df_rojo[df_rojo["DISTRITO"] == dist_sel]["GEL"].unique())
    else:
        gestores_filtrados = sorted(df_rojo["GEL"].unique())

    with colf1:
        gestor_filter = st.selectbox("👤 Filtrar por Gestor Local", ["-- Todos --"] + gestores_filtrados)
    with colf2:
        hogar_filter = st.text_input("🏠 Buscar por Código de Hogar:")

    df_filtrado = df_rojo.copy().drop(columns=["ORDEN"], errors="ignore")

    if gestor_filter != "-- Todos --":
        df_filtrado = df_filtrado[df_filtrado["GEL"] == gestor_filter]
    if hogar_filter:
        df_filtrado = df_filtrado[df_filtrado["CO_HOGAR"].astype(str).str.contains(hogar_filter.strip(), case=False, na=False)]

    df_vista = df_filtrado[[
        "CO_HOGAR", "GEL", "DISTRITO", "CENTRO_POBLADO",
        "ESCALA_PRIORIZACION", "FECHA_REGISTRO_ATENCION",
        "DISTANCIA_KM", "ALERTA"
    ]].sort_values(by="DISTANCIA_KM", ascending=False)

    def color_dist(val):
        try:
            v = float(val)
        except Exception:
            return ""
        if v >= 10: return "color:#B03A2E;font-weight:700;"
        elif v >= 5: return "color:#D68910;font-weight:600;"
        elif v >= 2: return "color:#CA6F1E;"
        else: return "color:#196F3D;"

    st.dataframe(
        df_vista.reset_index(drop=True)
        .rename(columns={
            "CO_HOGAR": "Código del Hogar",
            "GEL": "Gestor Local",
            "DISTRITO": "Distrito",
            "CENTRO_POBLADO": "Centro Poblado",
            "ESCALA_PRIORIZACION": "Priorización",
            "FECHA_REGISTRO_ATENCION": "Fecha",
            "DISTANCIA_KM": "Distancia (km)",
            "ALERTA": "Alerta"
        })
        .style.format({
            "Distancia (km)": "{:.2f}",
            "Fecha": lambda x: x.strftime("%d/%m/%Y") if pd.notnull(x) else ""
        })
        .applymap(color_dist, subset=["Distancia (km)"]),
        use_container_width=True,
        height=480
    )

# ======================================================
# 💾 EXPORTACIÓN EXCEL
# ======================================================
towrite = io.BytesIO()
with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
    cols_listado = [
        "UT", "DISTRITO", "CENTRO_POBLADO", "CO_HOGAR",
        "GEL", "ESCALA_PRIORIZACION", "FECHA_REGISTRO_ATENCION",
        "DISTANCIA_KM", "ALERTA"
    ]
    df_out = df_rojo[cols_listado].copy()
    df_out.to_excel(writer, index=False, sheet_name="Casos_Criticos")

    resumen = pd.DataFrame({
        "Indicador": [
            "Periodo", "Fecha inicio", "Fecha fin",
            "Visitas con ubicación no válida", "Gestores con registros no válidos",
            "Hogares con ubicación no válida"
        ],
        "Valor": [
            periodo_sel,
            fecha_inicio.strftime("%d/%m/%Y"),
            fecha_fin.strftime("%d/%m/%Y"),
            total_no_valida, gestores_involucrados, hogares_afectados
        ]
    })
    resumen.to_excel(writer, index=False, sheet_name="Resumen")

    (ranking if not ranking.empty else pd.DataFrame(
        columns=["Gestor Local","UT","Distrito",
                 "Total visitas (pri 4-5)",
                 "Visitas fuera de ubicación","% fuera de ubicación"])
    ).to_excel(writer, index=False, sheet_name="Ranking_Gestores")

towrite.seek(0)
b64 = base64.b64encode(towrite.read()).decode()
file_name = f"verificacion_geografica_{periodo_sel}.xlsx"

st.markdown(
    f"""
    <div style='text-align:center;margin-top:15px;'>
        <a href="data:application/octet-stream;base64,{b64}" download="{file_name}"
        style='background-color:{COLOR_PRINCIPAL};color:white;padding:10px 20px;
        border-radius:8px;text-decoration:none;font-weight:600;'>
        📥 Descargar reporte operativo (3 hojas)
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

# ======================================================
# 📌 PIE DE NOTA INSTITUCIONAL
# ======================================================
st.markdown(f"""
<hr>
<p style='font-size:12px;color:gray;margin-top:10px;text-align:center;'>
<b>Unidad de Cumplimiento de Corresponsabilidades – UCC · Ministerio de Desarrollo e Inclusión Social</b><br>
Umbrales de validez: ≤ 0.5 km (urbano), ≤ 2 km (andino), ≤ 5 km (amazónico).<br>
Las visitas con <b>“Ubicación no válida”</b> superan el límite permitido para su categoría geográfica.
</p>
""", unsafe_allow_html=True)