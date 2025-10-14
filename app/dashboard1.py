# ======================================================
# 📊 DASHBOARD DE ANÁLISIS GEOREFERENCIADO DE VISITAS DOMICILIARIAS
# ======================================================

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import geopandas as gpd
import folium
from branca.colormap import linear
from streamlit_folium import st_folium
import io
import base64

# ======================
# CONFIGURACIÓN DE PÁGINA
# ======================
st.set_page_config(page_title="Dashboard de Visitas", layout="wide")

# ======================
# CARGA DE DATOS
# ======================
@st.cache_data
def cargar_datos():
    df = pd.read_pickle("data/df_distancia.pkl")
    gdf = gpd.read_file("data/peru_departamental_simple.geojson")
    return df, gdf

df_distancia, gdf = cargar_datos()

# ======================================================
# FUNCIÓN UNIFICADA
# ======================================================
@st.cache_data
def calcular_resumen_mensual(df):
    df = df.copy()
    df['VALIDA_BASE'] = df['VALIDA_BASE'].str.upper().str.strip()
    df['MES'] = df['MES'].astype(str)
    df_filtrado = df[df['DISTANCIA_KM'] <= 50]
    resumen = df_filtrado.groupby(['MES', 'VALIDA_BASE']).size().unstack(fill_value=0)
    resumen_pct = resumen.div(resumen.sum(axis=1), axis=0) * 100
    return resumen_pct

# ======================================================
# ENCABEZADO
# ======================================================
st.markdown(
    """
    <h1 style="text-align:center;">Análisis Georreferenciado de Visitas Domiciliarias del Programa JUNTOS</h1>
    <p style="text-align:center; font-size:16px; color:gray;">
    Herramienta de monitoreo y supervisión para evaluar la correspondencia territorial de las visitas domiciliarias 
    registradas en campo y fortalecer el seguimiento operativo.
    </p>
    """,
    unsafe_allow_html=True
)

# ======================================================
# PESTAÑAS PRINCIPALES
# ======================================================
tabs = st.tabs([
    "📈 Resumen General",
    "🏙️ UT Priorizadas",
    "🗺️ Mapeo de Hogares",
    "👤 Gestor Local"
])

# ======================================================
# 📈 TAB 1 – RESUMEN GENERAL
# ======================================================
with tabs[0]:
    resumen_pct = calcular_resumen_mensual(df_distancia)

    def safe_get_pct(df, mes): 
        return df.loc[mes, 'INCONSISTENTE'] if mes in df.index else 0

    porc_agosto = safe_get_pct(resumen_pct, '2025-08')
    porc_septiembre = safe_get_pct(resumen_pct, '2025-09')

    # ======================================================
    # ENCABEZADO PRINCIPAL
    # ======================================================
    st.markdown(
        """
        <div style="text-align:center; margin-bottom:5px;">
            <h2 style="font-size:30px; color:#2E4053; margin-bottom:2.5px;">
                Porcentaje de visitas fuera del rango de ubicación del hogar - Nacional
        </div>
        """,
        unsafe_allow_html=True
    )

    # ======================================================
    # TARJETAS DE INDICADORES
    # ======================================================
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #E74C3C, #C0392B);
                padding: 25px; border-radius: 12px; text-align: center;
                box-shadow: 0 3px 10px rgba(0,0,0,0.15);
            ">
                <h3 style="color:white; margin-bottom:6px;">Agosto 2025</h3>
                <h1 style="color:white; font-size:46px; margin:0;">{porc_agosto:.2f}%</h1>
                <p style="color:#FDEDEC; margin-top:5px; font-size:14px;">
                    Visitas fuera del rango permitido
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #F39C12, #D68910);
                padding: 25px; border-radius: 12px; text-align: center;
                box-shadow: 0 3px 10px rgba(0,0,0,0.15);
            ">
                <h3 style="color:white; margin-bottom:6px;">Septiembre 2025</h3>
                <h1 style="color:white; font-size:46px; margin:0;">{porc_septiembre:.2f}%</h1>
                <p style="color:#FEF5E7; margin-top:5px; font-size:14px;">
                    Visitas fuera del rango permitido
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        """
        <p style='font-size:12px;color:gray; text-align:center; margin-top:15px;'>
        *Nota: Se excluyen del análisis los registros con distancias mayores a 50 km por considerarse valores atípicos.  
        Los umbrales de validez territorial son: ≤ 0.5 km (urbano), ≤ 2 km (andino), ≤ 5 km (amazónico).*
        </p>
        """,
        unsafe_allow_html=True
    )

    # ======================================================
    # 📅 GRÁFICO DE TENDENCIA MENSUAL 
    # ======================================================
    st.markdown(
    """
    <h4 style="color:#2E4053; margin-top:35px;">
        Tendencia mensual de visitas fuera del rango de ubicación del hogar
    </h4>
    """,
    unsafe_allow_html=True
    )

    resumen_pct = calcular_resumen_mensual(df_distancia)
    fig3, ax3 = plt.subplots(figsize=(9, 4))

    ax3.plot(
        resumen_pct.index, 
        resumen_pct['INCONSISTENTE'], 
        marker='o', linewidth=3, 
        color='#E74C3C', label='Visitas fuera del rango'
    )

    ax3.fill_between(
        resumen_pct.index,
        resumen_pct['INCONSISTENTE'],
        color='#E74C3C', alpha=0.15
    )

    for x, y in zip(resumen_pct.index, resumen_pct['INCONSISTENTE']):
        ax3.text(x, y + 0.15, f"{y:.1f}%", color='#C0392B', fontsize=9, ha='center', fontweight='bold')

    y_min = max(0, resumen_pct['INCONSISTENTE'].min() - 1.5)
    y_max = resumen_pct['INCONSISTENTE'].max() + 1
    ax3.set_ylim(y_min, y_max)
    ax3.set_ylabel('% de visitas fuera del rango', fontsize=11, color='#555')
    ax3.set_xlabel('Mes', fontsize=11, color='#555')
    ax3.grid(alpha=0.3)
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    st.pyplot(fig3)

    st.markdown(
        """
        <p style='font-size:12px;color:gray; margin-top:-10px;'>
        El gráfico muestra la evolución mensual del porcentaje de visitas domiciliarias que superan los umbrales de validez territorial.
        </p>
        """,
        unsafe_allow_html=True
    )
# ======================================================
# 🏙️ TAB 2 – DISTRIBUCIÓN POR UT
# ======================================================
with tabs[1]:
    st.markdown("""
    <h3 style='line-height:1.1; margin-bottom:0;'>
    Porcentaje de visitas fuera del rango de ubicación del hogar,<br>
    según UT priorizadas (Septiembre 2025)
    </h3>
    """, unsafe_allow_html=True)            

    df_sep = df_distancia[df_distancia['MES'] == '2025-09']
    df_sep = df_sep[df_sep['DISTANCIA_KM'] <= 50]
    ut_priorizadas = [
        "CAJAMARCA", "HUANUCO", "LORETO - IQUITOS", "PUNO",
        "JUNIN", "LORETO - YURIMAGUAS", "AMAZONAS - CONDORCANQUI", "ICA"
    ]

    df_sep = df_sep[df_sep['UT'].isin(ut_priorizadas)]
    resumen_ut = df_sep.groupby(['UT', 'VALIDA_BASE']).size().unstack(fill_value=0)
    resumen_ut_pct = resumen_ut.div(resumen_ut.sum(axis=1), axis=0) * 100
    resumen_ut_pct = resumen_ut_pct.rename(columns={
        'VALIDA': 'Válida',
        'INCONSISTENTE': 'Fuera del rango'
    })[['Válida', 'Fuera del rango']]

    resumen_ut_pct = resumen_ut_pct.sort_values('Fuera del rango', ascending=True)
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    resumen_ut_pct.plot(kind='barh', stacked=True, ax=ax2, color=['#2E86C1', '#E74C3C'], edgecolor='white')

    for i, (valida, inconsistente) in enumerate(zip(resumen_ut_pct['Válida'], resumen_ut_pct['Fuera del rango'])):
        ax2.text(valida / 2, i, f"{valida:.1f}%", color='white', va='center', ha='center', fontsize=9)
        ax2.text(valida + inconsistente / 2, i, f"{inconsistente:.1f}%", color='black', va='center', ha='center', fontsize=9)

    ax2.set_xlabel("Porcentaje de visitas (%)")
    ax2.set_ylabel("Unidad Territorial (UT)")
    ax2.legend(title="Categoría de visita", loc='upper center', bbox_to_anchor=(0.5, 1.13), ncol=2)
    ax2.grid(axis='x', alpha=0.3)
    st.pyplot(fig2)

    st.markdown(
        """
        <p style='font-size:12px;color:gray;'>
        Nota: Se excluyen registros con distancia mayor a 50 km (valores atípicos). 
        </p>
        """,
        unsafe_allow_html=True
    )

# ======================================================
# 🗺️ TAB 3 – MAPA NACIONAL 
# ======================================================
with tabs[2]:
    st.markdown("### Porcentaje de hogares con visitas domiciliarias fuera del rango, según departamentos- 2025")

    def limpiar_nombre(dep):
        return dep.strip().upper().replace("Á","A").replace("É","E").replace("Í","I").replace("Ó","O").replace("Ú","U")

    df_distancia['DEPARTAMENTO'] = df_distancia['DEPARTAMENTO'].apply(limpiar_nombre)
    gdf['NOMBDEP'] = gdf['NOMBDEP'].apply(limpiar_nombre)

    df_small = df_distancia[df_distancia['DISTANCIA_KM'] <= 50][['CO_HOGAR','DEPARTAMENTO','VALIDA_BASE']]

    pct_incons_por_hogar = (
        df_small.groupby('CO_HOGAR')['VALIDA_BASE']
        .apply(lambda x: (x == 'INCONSISTENTE').mean() * 100)
        .reset_index()
        .rename(columns={'VALIDA_BASE': 'PctInconsistente'})
    )

    hogares_problematicos = pct_incons_por_hogar.copy()
    hogares_problematicos['EsProblematico'] = hogares_problematicos['PctInconsistente'] >= 50

    df_hogar_depto = df_small[['CO_HOGAR','DEPARTAMENTO']].drop_duplicates()
    df_merge = df_hogar_depto.merge(hogares_problematicos[['CO_HOGAR','EsProblematico']], on='CO_HOGAR')

    pct_hogar_problema_depto = (
        df_merge.groupby('DEPARTAMENTO')['EsProblematico'].mean() * 100
    ).reset_index().rename(columns={'EsProblematico':'PctHogaresProblematicos'})

    promedio_nacional = pct_hogar_problema_depto['PctHogaresProblematicos'].mean()
    top5 = pct_hogar_problema_depto.sort_values('PctHogaresProblematicos', ascending=False).head(7)

    p90 = pct_hogar_problema_depto['PctHogaresProblematicos'].quantile(0.9)
    deptos_altoriesgo = pct_hogar_problema_depto[
        pct_hogar_problema_depto['PctHogaresProblematicos'] >= p90
    ]['DEPARTAMENTO'].tolist()

    gdf_merged = gdf.merge(pct_hogar_problema_depto, left_on='NOMBDEP', right_on='DEPARTAMENTO', how='left')
    gdf_merged['PctHogaresProblematicos_fmt'] = gdf_merged['PctHogaresProblematicos'].apply(
        lambda x: f"{x:.1f}%" if pd.notnull(x) else "Sin dato"
    )

    m = folium.Map(
        location=[-9.19, -75.0152],
        zoom_start=5,
        tiles="CartoDB positron",
        zoom_control=False,
        dragging=False,
        scrollWheelZoom=False
    )

    folium.GeoJson(
        gdf.boundary,
        name="Borde nacional",
        style_function=lambda x: {'color': 'black', 'weight': 1.2, 'fillOpacity': 0}
    ).add_to(m)

    vmin = pct_hogar_problema_depto['PctHogaresProblematicos'].min()
    vmax = pct_hogar_problema_depto['PctHogaresProblematicos'].max()
    colormap = linear.YlOrRd_09.scale(vmin, vmax)
    colormap.caption = "% de hogares con visitas inconsistentes"

    def style_function(feature):
        value = feature['properties']['PctHogaresProblematicos']
        color = colormap(value) if value is not None else 'lightgray'
        line_color = 'black' if feature['properties']['NOMBDEP'] in deptos_altoriesgo else 'white'
        return {'fillColor': color, 'color': line_color, 'weight': 1.2, 'fillOpacity': 0.8}

    tooltip = folium.GeoJsonTooltip(
        fields=['NOMBDEP', 'PctHogaresProblematicos_fmt'],
        aliases=['Departamento:', '% Hogares con visitas inconsistentes:'],
        localize=True, sticky=True, labels=True,
        style=("background-color:white; color:#333; font-size:12px; padding:4px; border-radius:4px;"),
        tooltip_anchor=(0, -20)
    )

    folium.GeoJson(
        gdf_merged,
        name='Visitas inconsistentes',
        style_function=style_function,
        tooltip=tooltip,
        highlight_function=lambda x: {'weight':2, 'color':'black', 'fillOpacity':0.9}
    ).add_to(m)

    colormap.add_to(m)

    col1, col2 = st.columns([3, 1])

    with col1:
        st_folium(m, width=800, height=550)

    with col2:     
        st.markdown(
            """
            <div style="background-color:#fafafa;padding:10px;border-radius:8px;border:1px solid #ddd;">
                <b>🔝 Top 7 Departamentos</b><br>
            </div>
            """,
            unsafe_allow_html=True
        )

        top5_display = (
            top5.reset_index(drop=True)
                .rename(columns={
                    'DEPARTAMENTO': 'DEPARTAMENTO',
                    'PctHogaresProblematicos': '%'
                })
        )
        top5_display.index = top5_display.index + 1
        top5_display.index.name = "N°"

        st.table(
            top5_display.style
                .format({'%': '{:.1f}%'})
                .set_table_styles([
                    {'selector': 'th', 'props' : [('text-align', 'center')]}
                ])
                .set_properties(subset=['%'], **{'text-align': 'center'})
                .set_properties(subset=['DEPARTAMENTO'],**{'text-align': 'left'})
        )

    st.markdown(
        f"""
        <p style='font-size:12px;color:gray;line-height:1.4;'>
        <b>Periodo analizado:</b> 2025 Acumulado anual.<br>
        <b>Promedio nacional:</b> {promedio_nacional:.1f}% de hogares con ≥50% de visitas inconsistentes.<br>
        <b>Interpretación:</b> Los tonos rojos representan mayor concentración de hogares con registros de visitas fuera del rango de validez territorial.<br>
        <b>Nota metodológica:</b> Se excluyen del análisis los registros con distancias >50 km por considerarse valores atípicos.<br>
        Los umbrales de validez territorial son:  ≤ 0.5 km (urbano), ≤ 2 km (andino), ≤ 5 km (amazónico).
        </p>
        """,
        unsafe_allow_html=True
    )
# ======================================================
# 👤 TAB 4 – GESTOR LOCAL (Versión compacta tipo Power BI)
# ======================================================

# ======================================================
# 🧑‍💼 FUNCIÓN: mostrar_detalle_gestor(df)
# ======================================================
def mostrar_detalle_gestor(df):
    
    st.markdown("---")
    st.markdown("## 🧩 Detalle por Gestor Local")

    # 1️⃣ Selector de DNI
    dni_input = st.text_input("🔎 Ingrese DNI del Gestor Local:", "")

    if dni_input:
        df_gestor = df[df["DNI_GEL"].astype(str) == str(dni_input)]

        if df_gestor.empty:
            st.warning("⚠️ No se encontraron registros para el DNI ingresado.")
            return

        # 2️⃣ Nombre del gestor
        nombre = df_gestor["GEL"].iloc[0] if not df_gestor["GEL"].isna().all() else "No registrado"
        st.markdown(f"### 👤 {nombre}")

        # ---------------------------
        # 📊 Indicadores del Gestor
        # ---------------------------
        st.markdown("#### 📊 Indicadores del Gestor")

        col1, col2, col3, col4 = st.columns(4, gap="small")

        card_style_small = """
            border-radius:12px;
            padding:5px 10px;
            text-align:center;
            min-height:50px;
            display:flex;
            flex-direction:column;
            justify-content:center;
            align-items:center;
            box-shadow:0 2px 6px rgba(0,0,0,0.08);
            color:white;
            font-family:'Segoe UI', sans-serif;
            font-weight:600;
        """

        with col1:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg, #CA6F1E, #D68910); {card_style_small}">
                <h6 style="margin-bottom:-4px; font-size:15px; font-weight:600;">🏠 Hogares</h6>
                <h2 style="margin:0; font-size:40px; font-weight:500; line-height:0.1;">{df_gestor["CO_HOGAR"].nunique():,}</h2>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg, #B03A2E, #CD6155); {card_style_small}">
                <h6 style="margin-bottom:-4px; font-size:15px; font-weight:600;">🤰 Gestantes</h6>
                <h2 style="margin:0; font-size:40px; font-weight:500; line-height:0.1;">{df_gestor.loc[df_gestor["TIPO_MO"] == "GESTANTE", "DNI"].nunique():,}</h2>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg, #884EA0, #AF7AC5); {card_style_small}">
                <h6 style="margin-bottom:-4px; font-size:15px; font-weight:600;">👶 Niños</h6>
                <h2 style="margin:0; font-size:40px; font-weight:500; line-height:0.1;">{df_gestor.loc[df_gestor["TIPO_MO"] == "NIÑO", "DNI"].nunique():,}</h2>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg, #2471A3, #5499C7); {card_style_small}">
                <h6 style="margin-bottom:-4px; font-size:15px; font-weight:600;">🧒 Adolescentes</h6>
                <h2 style="margin:0; font-size:40px; font-weight:500; line-height:0.1;">{df_gestor.loc[df_gestor["TIPO_MO"] == "ADOLESCENTE", "DNI"].nunique():,}</h2>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_izq, col_der = st.columns([1.45, 1.55], vertical_alignment="top")

        # --- IZQUIERDA: TABLA DE VISITAS POR PERIODO ---
        with col_izq:
            st.markdown("#### 📅 Visitas fuera de rango por periodo operativo")

            visitas_periodo = (
                df_gestor.groupby("MES")["VALIDA_BASE"]
                .agg(
                    Total="count",
                    Validas=lambda x: (x == "VALIDA").sum(),
                    Inconsistentes=lambda x: (x == "INCONSISTENTE").sum()
                )
                .reset_index()
            )

            visitas_periodo["% Válidas"] = (
                visitas_periodo["Validas"] / visitas_periodo["Total"] * 100
            ).round(1)
            visitas_periodo["% Inconsistentes"] = (
                visitas_periodo["Inconsistentes"] / visitas_periodo["Total"] * 100
            ).round(1)
            visitas_periodo = visitas_periodo.rename(columns={"MES": "Periodo"})

            visitas_periodo["Visitas válidas"] = visitas_periodo["Validas"]
            visitas_periodo["Visitas fuera de rango"] = visitas_periodo["Inconsistentes"]
            visitas_periodo["Total de visitas"] = visitas_periodo["Total"]
            visitas_periodo["%"] = visitas_periodo["% Inconsistentes"]

            tabla_mostrar = visitas_periodo[
                ["Periodo", "Visitas válidas", "Visitas fuera de rango", "Total de visitas", "%"]
            ]

            st.table(
                tabla_mostrar.style.format({
                    "%": "{:.1f}",
                    "Visitas válidas": "{:,.0f}",
                    "Visitas fuera de rango": "{:,.0f}",
                    "Total de visitas": "{:,.0f}"
                }).set_properties(subset=["Visitas válidas", "Visitas fuera de rango", "Total de visitas", "%"], **{"text-align": "center"})
            )

        # --- DERECHA: GRÁFICO DE TENDENCIA ---
        with col_der:
            st.markdown("#### 📈 Tendencia de % visitas fuera de rango")

            df_trend = visitas_periodo.copy()
            df_trend["Periodo"] = df_trend["Periodo"].astype(str)

            fig, ax = plt.subplots(figsize=(7, 3.3))
            ax.plot(
                df_trend["Periodo"],
                df_trend["% Inconsistentes"],
                marker='o', linewidth=3, color='#E74C3C', label='% fuera de rango'
            )

            ax.fill_between(
                df_trend["Periodo"],
                df_trend["% Inconsistentes"],
                color='#E74C3C',
                alpha=0.15
            )

            for x, y in zip(df_trend["Periodo"], df_trend["% Inconsistentes"]):
                ax.text(x, y + 0.3, f"{y:.1f}%", color='#C0392B', fontsize=9, ha='center', fontweight='bold')

            ax.set_ylabel('% de visitas fuera de rango', fontsize=11, color='#555')
            ax.set_xlabel('Periodo (MES)', fontsize=11, color='#555')
            ax.grid(alpha=0.3)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            plt.xticks(rotation=45, ha='right')
            ax.legend()

            st.pyplot(fig)

        # ---------------------------
        # 🏠 Listado de hogares
        # ---------------------------
        st.markdown("#### 🏠 Hogares con mayor proporción de visitas fuera de rango")

        periodos = sorted(df_gestor["MES"].astype(str).unique())
        periodo_sel_hogar = st.selectbox("Selecciona un periodo:", ["-- Acumulado --"] + periodos)

        df_filtrado = df_gestor.copy()
        if periodo_sel_hogar != "-- Acumulado --":
            df_filtrado = df_filtrado[df_filtrado["MES"].astype(str) == periodo_sel_hogar]

        resumen_hogar = (
            df_filtrado.groupby("CO_HOGAR")
            .agg(
                Tipo_MO=("TIPO_MO", lambda x: ", ".join(sorted(set(x)))),
                Escala=("ESCALA_PRIORIZACION", lambda x: ", ".join(map(str, sorted(set(x))))),
                Visitas_validas=("VALIDA_BASE", lambda x: (x == "VALIDA").sum()),
                Visitas_inconsistentes=("VALIDA_BASE", lambda x: (x == "INCONSISTENTE").sum())
            )
            .reset_index()
        )

        resumen_hogar["Total_de_visitas"] = (
            resumen_hogar["Visitas_validas"] + resumen_hogar["Visitas_inconsistentes"]
        )
        resumen_hogar["%"] = (
            resumen_hogar["Visitas_inconsistentes"] / resumen_hogar["Total_de_visitas"] * 100
        ).round(1)

        resumen_hogar = resumen_hogar.sort_values(
            by=["%", "Visitas_inconsistentes"], ascending=[False, False]
        )

        resumen_hogar = resumen_hogar.rename(
            columns={
                "CO_HOGAR": "Código Hogar",
                "Tipo_MO": "Tipo MO",
                "Escala": "Escala",
                "Visitas_validas": "Visitas válidas",
                "Visitas_inconsistentes": "Visitas fuera de rango",
                "Total_de_visitas": "Total de visitas"
            }
        )

        resumen_hogar = resumen_hogar[
            ["Código Hogar", "Tipo MO", "Escala", "Visitas válidas",
             "Visitas fuera de rango", "Total de visitas", "%"]
        ]

        st.table(
            resumen_hogar.head(10)
            .style.format({
                "%": "{:.1f}",
                "Visitas válidas": "{:,.0f}",
                "Visitas fuera de rango": "{:,.0f}",
                "Total de visitas": "{:,.0f}"
            })
            .set_properties(subset=["%"], **{"text-align": "center"})
        )

        # 💾 Botón de descarga Excel
        towrite = io.BytesIO()
        with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
            resumen_hogar.to_excel(writer, index=False, sheet_name="Hogares")
        towrite.seek(0)
        b64 = base64.b64encode(towrite.read()).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="hogares_inconsistentes_{dni_input}.xlsx">📥 Descargar tabla completa</a>'
        st.markdown(href, unsafe_allow_html=True)

# ======================================================
# BLOQUE PRINCIPAL DE LA PESTAÑA 4
# ======================================================
with tabs[3]:

    # 1️⃣ Selectores de filtro
    colf1, colf2 = st.columns(2)
    with colf1:
        ut_sel = st.selectbox(
            "Selecciona una Unidad Territorial (UT):",
            ["-- Selecciona --"] + sorted(df_distancia["UT"].unique()),
            key="ut_select"
        )
    with colf2:
        periodo_sel = st.selectbox(
            "Selecciona un periodo (MES):",
            ["-- Acumulado --"] + sorted(df_distancia["MES"].astype(str).unique()),
            key="period_select"
        )

    @st.cache_data
    def calcular_rankings(df, ut_sel, periodo_sel):
        df_rank = df[df["UT"] == ut_sel].copy()
        if periodo_sel != "-- Acumulado --":
            df_rank = df_rank[df_rank["MES"].astype(str) == periodo_sel]

        resumen = (
            df_rank.groupby(["DNI_GEL", "GEL", "VALIDA_BASE"])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )

        for c in ["VALIDA", "INCONSISTENTE"]:
            if c not in resumen.columns:
                resumen[c] = 0

        resumen["TOTAL"] = resumen["VALIDA"] + resumen["INCONSISTENTE"]
        resumen["%_Inconsistencia"] = (resumen["INCONSISTENTE"] / resumen["TOTAL"] * 100).round(1)

        resumen["Nombre"] = resumen["GEL"].apply(lambda x: x.split(",")[0].strip().title() if isinstance(x, str) else "")
        resumen["DNI"] = resumen["DNI_GEL"].astype(str)

        top_incons = resumen.sort_values(["%_Inconsistencia", "INCONSISTENTE"], ascending=[False, False])
        return top_incons

    if ut_sel != "-- Selecciona --":
        df_ut = df_distancia[df_distancia["UT"] == ut_sel]
        if periodo_sel != "-- Acumulado --":
            df_ut = df_ut[df_ut["MES"].astype(str) == periodo_sel]

        top_incons = calcular_rankings(df_distancia, ut_sel, periodo_sel)

        st.markdown(f"### 🔴 Ranking de gestores con visitas fuera de rango ({ut_sel})")

        tabla_rank = (
            top_incons[["Nombre", "DNI", "VALIDA", "INCONSISTENTE", "TOTAL", "%_Inconsistencia"]]
            .rename(columns={
                "VALIDA": "Visitas válidas",
                "INCONSISTENTE": "Visitas fuera de rango",
                "TOTAL": "Total de visitas",
                "%_Inconsistencia": "%"
            })
            .reset_index(drop=True)
        )

        st.table(
            tabla_rank
            .head(10)
            .style.format({
                "%": "{:.1f}",
                "Visitas válidas": "{:,.0f}",
                "Visitas fuera de rango": "{:,.0f}",
                "Total de visitas": "{:,.0f}"
            })
            .set_properties(subset=["%"], **{"text-align": "center"})
        )

        towrite = io.BytesIO()
        with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
            tabla_rank.to_excel(writer, index=False, sheet_name="Ranking Gestores")
        towrite.seek(0)
        b64 = base64.b64encode(towrite.read()).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="ranking_gestores_inconsistentes_{ut_sel}.xlsx">📥 Descargar ranking completo</a>'
        st.markdown(href, unsafe_allow_html=True)

    else:
        st.info("Selecciona una Unidad Territorial para visualizar los rankings de gestores.")

    mostrar_detalle_gestor(df_distancia)