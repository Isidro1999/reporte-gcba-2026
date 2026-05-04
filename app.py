import ast
import pandas as pd
import streamlit as st
import plotly.express as px
import os

def check_password():
    # Cambiá esta pass por la tuya momentáneamente
    PASSWORD = "gcba2025"

    if "password_ok" not in st.session_state:
        st.session_state.password_ok = False

    if not st.session_state.password_ok:
        st.markdown("### 🔐 Acceso restringido")
        password = st.text_input("Ingresá la contraseña", type="password")

        if st.button("Entrar"):
            if password == PASSWORD:
                st.session_state.password_ok = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")

        st.stop()

check_password()
st.image("data/logo_gcba.png", width=280)
st.image("data/logo_feater.png", width=180)



PALETA_PLOTLY = ["#800008", "#5B0C11", "#989898", "#FFFFFF", "#C55A5A", "#7A7A7A"]

def aplicar_tema_plotly(fig):
    fig.update_layout(
        plot_bgcolor="#000000",
        paper_bgcolor="#000000",
        font=dict(color="#FFFFFF"),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#FFFFFF")
        ),
        coloraxis_colorbar=dict(
            bgcolor="#000000",
            tickfont=dict(color="#FFFFFF")
        )
    )

    try:
        fig.update_traces(marker=dict(colors=PALETA_PLOTLY), selector=dict(type="bar"))
    except:
        pass

    fig.update_layout(colorway=PALETA_PLOTLY)

    return fig


# =====================================================
# 0. CONFIG STREAMLIT
# =====================================================
st.set_page_config(
    page_title="Reporte Analítico CMS GCBA",
    layout="wide"
)



st.markdown("""
<style>

body, .stApp {
    background-color: #000000 !important;
    color: #FFFFFF !important;
}

/* TITULOS */
h1, h2, h3, h4, h5, h6, label {
    color: #FFFFFF !important;
    font-weight: 600;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background-color: #5B0C11 !important;
    border-right: 1px solid #800008 !important;
}

/* INPUTS */
div[data-baseweb="select"] {
    background-color: #5B0C11 !important;
    color: #FFFFFF !important;
}

.stSelectbox, .stMultiSelect {
    background-color: #5B0C11 !important;
}

/* KPI CUSTOM */
.kpi-card {
    padding: 22px 18px;
    background-color: #800008;
    border-radius: 14px;
    border: 1px solid #5B0C11;
    text-align: left;
}

.kpi-title {
    font-size: 22px;
    color: #D3D3D3;
    font-weight: 600;
    margin-bottom: 8px;
}

.kpi-value {
    font-size: 56px;
    font-weight: 900;
    color: #FFFFFF;
    line-height: 1;
}


/* delta (por si aparece) */
div[data-testid="metric-container"] [data-testid="stMetricDelta"]{
    font-size: 16px !important;
}



/* FOOTER */
.footer {
    text-align: center;
    margin-top: 50px;
    padding: 15px;
    color: #AAAAAA;
    font-size: 14px;
}
            
/* TABS / CATEGORÍAS (fallback) */
div[data-testid="stTabs"] button,
div[data-testid="stTabs"] [role="tab"],
div[data-testid="stTabs"] p,
div[data-testid="stTabs"] span {
    font-size: 18px !important;
}




</style>
""", unsafe_allow_html=True)


# =====================================================
# 1. CARGA Y PREPARACIÓN DE DATOS
# =====================================================

from pathlib import Path

DATA_PATH = Path("data/df_final.csv")

@st.cache_data
def load_data(file_mtime):
    df = pd.read_csv(DATA_PATH)

    df["Eje"] = df["Eje"].astype(str).str.strip()
    df["Sub Eje"] = df["Sub Eje"].astype(str).str.strip()
    df["Tema"] = df["Tema"].astype(str).str.strip()
    df["Subtema"] = df["Subtema"].astype(str).str.strip()
    df["Mes"] = df["Mes"].astype(str).str.lower().str.strip()
    df["Comuna"] = pd.to_numeric(df["Comuna"], errors="coerce")
    df["Tipo de material"] = df["Tipo de material"].astype(str).str.strip()


    meses = {"enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,
             "julio":7,"agosto":8,"septiembre":9,"setiembre":9,"octubre":10,
             "noviembre":11,"diciembre":12}
    df["Mes_num"] = df["Mes"].map(meses)
    df["Año"] = pd.to_numeric(df["Año"], errors="coerce")

    df = df.dropna(subset=["Año", "Mes_num"])
    df["Fecha"] = pd.to_datetime(
        df["Año"].astype(int).astype(str) + "-" +
        df["Mes_num"].astype(int).astype(str) + "-01"
    )

    def parse_tags(x):
        if isinstance(x, list): return x
        if isinstance(x, str):
            try: return ast.literal_eval(x)
            except: return []
        return []
    df["Tags_list"] = df.get("Tags_list", []).apply(parse_tags)

    def extraer_subtipos(tags):
        sub = []
        for t in tags:
            if isinstance(t, str) and t.startswith("Material - "):
                stp = t.replace("Material - ", "").strip().lower()
                sub.append(stp.capitalize())
        return sub

    df["Subtipos_material"] = df["Tags_list"].apply(extraer_subtipos)
    return df




@st.cache_data
def load_bandas_catalogo():
    df_bandas = pd.read_csv("data/bandas_por_catalogo.csv")
    df_bandas["Catálogo"] = df_bandas["Catálogo"].astype(str).str.strip()
    df_bandas["Cantidad de Bandas"] = pd.to_numeric(df_bandas["Cantidad de Bandas"], errors="coerce").fillna(0).astype(int)
    return df_bandas

df_bandas = load_bandas_catalogo()

df = load_data(DATA_PATH.stat().st_mtime)

df["Eje"] = df["Eje"].replace(["nan", "None", ""], "Sin eje")
df["Sub Eje"] = df["Sub Eje"].replace(["nan", "None", ""], "Sin subeje")
df["Tema"] = df["Tema"].replace(["nan", "None", ""], "Sin tema")
df["Subtema"] = df["Subtema"].replace(["nan", "None", ""], "Sin subtema")

MAPEO_EJES = {
    "Cuidado y Bien Público": "Cuidado",
    "Desarrollo": "Reforma y Modernización del estado",
    "Encuentro": "Ciudad Atractiva",
    "Obras": "Movilidad",
    "Orden": "Orden, Seguridad y Limpieaza",
}


# Fechas
fecha_max = df["Fecha"].max()
limite_2y = fecha_max - pd.DateOffset(years=2)

# =====================================================
# 2. SIDEBAR
# =====================================================
st.sidebar.header("Filtros")

from datetime import date

fecha_inicio_default = date(2020, 1, 1)
fecha_fin_default = date.today()

rango_fechas = st.sidebar.date_input(
    "Rango de fechas",
    value=(fecha_inicio_default, fecha_fin_default),
    min_value=fecha_inicio_default,
    max_value=fecha_fin_default
)

if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
    inicio, fin = rango_fechas
else:
    inicio, fin = fecha_inicio_default, fecha_fin_default


df["Eje_display"] = df["Eje"].map(MAPEO_EJES).fillna(df["Eje"])

ejes_disp = sorted(df["Eje_display"].unique())
ejes_sel = st.sidebar.multiselect("Ejes", ejes_disp, default=ejes_disp)


tipos_disp = sorted(df["Tipo de material"].unique())
tipos_sel = st.sidebar.multiselect("Tipo de material", tipos_disp, default=tipos_disp)

subtipos_disp = sorted(df.explode("Subtipos_material")["Subtipos_material"].dropna().unique())
subtipos_sel = st.sidebar.multiselect("Subtipos", subtipos_disp, default=subtipos_disp)

mask = (
    (df["Fecha"].dt.date >= inicio) &
    (df["Fecha"].dt.date <= fin) &
    (df["Eje_display"].isin(ejes_sel)) &
    (df["Tipo de material"].isin(tipos_sel))
)

df_filtrado = df[mask].copy()
st.write("DEBUG 1 - total df:", len(df))

solo_fecha = df[
    (df["Fecha"].dt.date >= inicio) &
    (df["Fecha"].dt.date <= fin)
]
st.write("DEBUG 2 - solo fecha:", len(solo_fecha))

solo_eje = df[df["Eje_display"].isin(ejes_sel)]
st.write("DEBUG 3 - solo eje:", len(solo_eje))

solo_tipo = df[df["Tipo de material"].isin(tipos_sel)]
st.write("DEBUG 4 - solo tipo:", len(solo_tipo))

st.write("DEBUG 5 - final filtrado:", len(df_filtrado))

st.write("Tipos disponibles:", sorted(df["Tipo de material"].dropna().unique()))
st.write("Tipos seleccionados:", tipos_sel)

st.write("Fecha mínima:", df["Fecha"].min())
st.write("Fecha máxima:", df["Fecha"].max())
st.write("DEBUG total df:", len(df))
st.write("DEBUG rango fechas:", inicio, fin)
st.write("DEBUG por fecha:", len(df[(df["Fecha"].dt.date >= inicio) & (df["Fecha"].dt.date <= fin)]))
st.write("DEBUG por eje:", len(df[df["Eje_display"].isin(ejes_sel)]))
st.write("DEBUG por tipo:", len(df[df["Tipo de material"].isin(tipos_sel)]))
st.write("DEBUG final df_filtrado:", len(df_filtrado))
st.write("DEBUG tipos disponibles:", sorted(df["Tipo de material"].dropna().unique()))
st.write("DEBUG tipos seleccionados:", tipos_sel)
df_filtrado["Eje_display"] = (
    df_filtrado["Eje"]
    .map(MAPEO_EJES)
    .fillna(df_filtrado["Eje"])
)


# =====================================================
# 3. KPIs
# =====================================================
col1, col2, col3, col4 = st.columns(4)

def kpi_html(titulo, valor):
    return f"""
    <div class="kpi-card">
        <div class="kpi-title">{titulo}</div>
        <div class="kpi-value">{valor}</div>
    </div>
    """

col1.markdown(kpi_html("Total materiales", f"{len(df_filtrado):,}".replace(",", ".")), unsafe_allow_html=True)
col2.markdown(kpi_html("Ejes activos", df_filtrado["Eje"].nunique()), unsafe_allow_html=True)
comunas_alcanzadas = df_filtrado.loc[df_filtrado["Comuna"].between(1, 15), "Comuna"].nunique()
col3.markdown(kpi_html("Comunas alcanzadas", comunas_alcanzadas), unsafe_allow_html=True)
ultimo_mes = df_filtrado["Fecha"].max().strftime("%m/%Y") if not df_filtrado.empty else "-"
col4.markdown(kpi_html("Último mes cargado", ultimo_mes), unsafe_allow_html=True)



st.markdown("---")

# =====================================================
# 4. TABS
# =====================================================
tab_resumen, tab_ejes, tab_territorio, tab_materiales, tab_insights = st.tabs([
    "📌 Resumen", "🏛️ Gráfico Interactivo", "🗺️ Mapa por comunas", "🎥 Materiales", "🧠 Insights"
])

# -----------------------------------------------------
# 🟦 TAB RESUMEN
# -----------------------------------------------------
with tab_resumen:
    st.subheader("Distribución general por Eje")

    df_eje = df_filtrado.groupby("Eje_display").size().reset_index(name="Cantidad")
    fig_eje = aplicar_tema_plotly(px.bar(df_eje, x="Eje_display", y="Cantidad", text="Cantidad"))

    fig_eje.update_yaxes(title_text="Cantidad de materiales")
    fig_eje.update_xaxes(title_text="Ejes")
    
    st.plotly_chart(fig_eje, use_container_width=True)

    st.subheader("Evolución de carga Mensual")
    # Evolución mensual total (con todos los meses)
    df_mes = df_filtrado.groupby("Fecha").size().rename("Cantidad")

    # Armamos el rango completo de meses según filtro
    start = pd.to_datetime(inicio).to_period("M").to_timestamp()
    end = pd.to_datetime(fin).to_period("M").to_timestamp()

    # Evitar meses anteriores a 2024-01
    start_min = pd.Timestamp("2024-01-01")
    if start < start_min:
        start = start_min

    idx = pd.date_range(start=start, end=end, freq="MS")

    df_mes = df_mes.reindex(idx, fill_value=0).reset_index().rename(columns={"index": "Fecha"})

    fig_total = aplicar_tema_plotly(px.line(df_mes, x="Fecha", y="Cantidad", markers=True))
    fig_total.update_yaxes(title_text="Cantidad de materiales")

    # Fuerza ticks mensuales
    fig_total.update_xaxes(
        dtick="M1",
        tickformat="%b %Y"   # Jan 2024, Feb 2024, ...
    )

    st.plotly_chart(fig_total, use_container_width=True)

    st.subheader("Bandas por Catálogo")

    df_b = df_bandas.sort_values("Cantidad de Bandas", ascending=False)

    fig_bandas = aplicar_tema_plotly(
        px.bar(
            df_b,
            x="Catálogo",
            y="Cantidad de Bandas",
            text="Cantidad de Bandas"
        )
    )

    fig_bandas.update_traces(textposition="outside", cliponaxis=False)
    fig_bandas.update_yaxes(title_text="Cantidad de bandas")
    fig_bandas.update_xaxes(title_text="Catálogo")

    st.plotly_chart(fig_bandas, use_container_width=True)




# -----------------------------------------------------
# 🟩 TAB EJES & TEMAS
# -----------------------------------------------------
with tab_ejes:

    # Sunburst
    st.subheader("Etiqueta --> Ruta --> Cantidad")

    df_h = df_filtrado[["Eje_display", "Sub Eje", "Tema", "Subtema"]].copy()

    REEMPLAZOS = {
        "Eje_display": "Sin eje",
        "Sub Eje": "Sin subeje",
        "Tema": "Sin tema",
        "Subtema": "Sin subtema"
    }

    for col, label in REEMPLAZOS.items():
        df_h[col] = (
            df_h[col]
            .astype(str)
            .str.strip()
            .replace(["nan", "NaN", "None", ""], label)
        )

    fig_sun = aplicar_tema_plotly(
        px.sunburst(df_h, path=["Eje_display", "Sub Eje", "Tema", "Subtema"])
    )

    

    fig_sun.update_traces(
    hovertemplate=
        "<b>Etiqueta:</b> %{label}<br>" +
        "<b>Ruta:</b> %{id}<br>" +
        "<b>Cantidad:</b> %{value}<br>" +
        "<extra></extra>"
)


    fig_sun.update_layout(
    height=550,                 # probá 800–950
    margin=dict(l=10, r=10, t=10, b=10)
)
  



    st.plotly_chart(fig_sun, use_container_width=True)

    # Evolución por eje
    st.subheader("Evolución mensual por Eje")

    df_eje_tiempo = (
        df_filtrado
        .groupby(["Fecha", "Eje_display"])
        .size()
        .reset_index(name="Cantidad")
    )

    fig_eje_tiempo = aplicar_tema_plotly(
     px.line(df_eje_tiempo, x="Fecha", y="Cantidad", color="Eje_display", markers=True)
    )

    st.plotly_chart(fig_eje_tiempo, use_container_width=True)

    # Top subejes
    st.subheader("Top 20 SubEjes")
    df_subeje = df_filtrado.groupby("Sub Eje").size().reset_index(name="Cantidad").nlargest(20, "Cantidad")
    fig_subeje = aplicar_tema_plotly(px.bar(df_subeje, x="Sub Eje", y="Cantidad", text="Cantidad"))
    st.plotly_chart(fig_subeje, use_container_width=True)

    # Heatmaps
    st.subheader("Heatmap — Eje vs Mes")

    df_heat_eje = (
        df_filtrado
        .groupby(["Eje_display", "Mes_num"])
        .size()
        .reset_index(name="Cantidad")
    )

    heat_eje = df_heat_eje.pivot(
        index="Eje_display",
        columns="Mes_num",
            values="Cantidad"
)

    fig_heat1 = aplicar_tema_plotly(
        px.imshow(
            heat_eje,
            color_continuous_scale="Blues",
            labels=dict(
                x="Mes",
                y="Eje",
                color="Cantidad"
        )
    )
)
    fig_heat1.update_xaxes(title_text="Mes")


    st.plotly_chart(fig_heat1, use_container_width=True)


    st.subheader("Heatmap — SubEje vs Mes")
    df_heat_subeje = df_filtrado.groupby(["Sub Eje", "Mes_num"]).size().reset_index(name="Cantidad")
    heat_subeje = df_heat_subeje.pivot(index="Sub Eje", columns="Mes_num", values="Cantidad")
    fig_heat2 = aplicar_tema_plotly(px.imshow(heat_subeje, color_continuous_scale="Reds"))
    fig_heat2.update_xaxes(title_text="Mes")
    st.plotly_chart(fig_heat2, use_container_width=True)

    # YoY
    st.subheader("Comparativa Año vs Año por Eje (YoY)")
    ejes_yoy_disponibles = (
        df_filtrado[["Eje", "Eje_display"]]
        .drop_duplicates()
        .sort_values("Eje_display")
    )

    

    eje_yoy_display = st.selectbox(
        "Seleccioná un Eje:",
        options=ejes_yoy_disponibles["Eje_display"].tolist(),
        index=0
    )

    eje_yoy = ejes_yoy_disponibles.loc[
        ejes_yoy_disponibles["Eje_display"] == eje_yoy_display,
        "Eje"
    ].iloc[0]



    df_yoy = df_filtrado[df_filtrado["Eje"] == eje_yoy]
    df_yoy = df_yoy.groupby(["Año", "Mes_num"]).size().reset_index(name="Cantidad")

    fig_yoy_single = aplicar_tema_plotly(
        px.line(df_yoy, x="Mes_num", y="Cantidad", color="Año", markers=True)
    )
    fig_yoy_single.update_xaxes(title_text="Mes")

    st.plotly_chart(fig_yoy_single, use_container_width=True)



# -----------------------------------------------------
# 🟧 TAB TERRITORIO
# -----------------------------------------------------
with tab_territorio:

    st.subheader("Mapa territorial")

    import json

    try:
        with open("data/comunas_caba.geojson", "r", encoding="utf-8") as f:
            comunas_geojson = json.load(f)

        df_map = df_filtrado[df_filtrado["Comuna"].between(1, 15)]
        df_map = df_map.groupby("Comuna").size().reset_index(name="Cantidad")

        fig_map = px.choropleth_mapbox(
            df_map,
            geojson=comunas_geojson,
            locations="Comuna",
            color="Cantidad",
            featureidkey="properties.comuna",
            center={"lat": -34.61, "lon": -58.44},
            zoom=10.3,
            mapbox_style="carto-positron"
        )

        fig_map = aplicar_tema_plotly(fig_map)
        st.plotly_chart(fig_map, use_container_width=True)

    except Exception as e:
        st.error(f"Error cargando mapa: {e}")

    st.subheader("Materiales por Comuna")

    df_com = (
        df_filtrado[df_filtrado["Comuna"].between(1, 15)]
        .groupby("Comuna")
        .size()
        .reset_index(name="Cantidad")
    )
    fig_com = aplicar_tema_plotly(px.bar(df_com, x="Comuna", y="Cantidad", text="Cantidad"))
    fig_com.update_xaxes(
    tickmode="linear",
    dtick=1
)

    st.plotly_chart(fig_com, use_container_width=True)


# -----------------------------------------------------
# 🟪 TAB MATERIALES
# -----------------------------------------------------
with tab_materiales:
    st.subheader("Distribución por tipo de material")


    df_tipo = df_filtrado.groupby("Tipo de material").size().reset_index(name="Cantidad")
    fig_tipo = aplicar_tema_plotly(px.pie(df_tipo, names="Tipo de material", values="Cantidad", hole=0.4))
    st.plotly_chart(fig_tipo, use_container_width=True)

    st.subheader("Evolución por Subtipo")

    df_sub = df_filtrado.explode("Subtipos_material")
    df_sub = df_sub[df_sub["Subtipos_material"].isin(subtipos_sel)]
    df_sub = df_sub.groupby(["Fecha","Subtipos_material"]).size().reset_index(name="Cantidad")

    fig_evo_sub = aplicar_tema_plotly(px.line(df_sub, x="Fecha", y="Cantidad", color="Subtipos_material", markers=True))
    st.plotly_chart(fig_evo_sub, use_container_width=True)

# -----------------------------------------------------
# 🧠 TAB INSIGHTS
# -----------------------------------------------------
with tab_insights:
    st.subheader("Insights automáticos")

    try:
        top_eje = df_filtrado["Eje"].value_counts().idxmax()
        top_subeje = df_filtrado["Sub Eje"].value_counts().idxmax()
        top_mes = df_filtrado["Mes_num"].value_counts().idxmax()
        pico = df_filtrado["Fecha"].dt.to_period("M").value_counts().idxmax()

        st.markdown(f"""
        ### Conclusiones principales  
        - 🔹 **Eje más activo:** {top_eje}  
        - 🔹 **SubEje líder:** {top_subeje}  
        - 🔹 **Mes con mayor carga:** {top_mes}  
        - 🔹 **Pico de actividad:** {pico}  
        """)
    except:
        st.info("No hay suficientes datos para generar insights.")

