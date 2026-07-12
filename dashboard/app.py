"""
Sistema de Alerta Temprana de Inflacion de Alimentos Basicos - Lima
Dashboard Streamlit - Entregable 6
Proyecto: food-price-forecasting-peru | UNMSM - Big Data Analytics 2025-II

Autor de esta vista: Andrew (dashboard).
Lee las tablas de la Zona Oro (kpi_precios, kpi_sentimiento, clusters_productos)
y las metricas estaticas de MLflow (mlflow_metricas.json).
"""

import json
from datetime import datetime, date, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Configuracion general
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Alerta de Precios de Alimentos - Lima",
    page_icon="🥔",
    layout="wide",
)

# Carpeta donde viven las tablas Parquet de la Zona Oro.
# En produccion esto deberia apuntar al bucket de GCS montado o descargado
# (ej. gs://<bucket>/oro/ sincronizado con gcsfs, o rutas locales tras un
# `gsutil -m cp -r gs://<bucket>/oro ./oro`). Para desarrollo local / Colab
# se usan los Parquet que Daniel entrega en la Zona Oro.
DATA_DIR = Path(__file__).parent / "oro"
METRICS_FILE = Path(__file__).parent / "mlflow_metricas.json"

REFRESH_SECONDS = 300  # Vista 1 se actualiza cada 5 minutos (requisito E6)

COLOR_ALERTA = {"ALERTA": "#e63946", "ATENCION": "#f4a261", "NORMAL": "#2a9d8f"}


# ---------------------------------------------------------------------------
# Carga de datos (con cache tipo Zona Oro -> refresco cada 5 min en Vista 1)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def cargar_kpi_precios() -> pd.DataFrame:
    df = pd.read_parquet(DATA_DIR / "kpi_precios.parquet")
    # anio + semana ISO -> fecha (lunes de esa semana), util para graficos temporales
    df["fecha"] = df.apply(
        lambda r: date.fromisocalendar(int(r["anio"]), int(min(r["semana"], 52)), 1),
        axis=1,
    )
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df.sort_values(["producto", "fecha"]).reset_index(drop=True)


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def cargar_kpi_sentimiento() -> pd.DataFrame:
    df = pd.read_parquet(DATA_DIR / "kpi_sentimiento.parquet")
    df["fecha"] = df.apply(
        lambda r: date.fromisocalendar(int(r["anio"]), int(min(r["semana"], 52)), 1),
        axis=1,
    )
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df.sort_values("fecha").reset_index(drop=True)


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def cargar_clusters() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "clusters_productos.parquet")


@st.cache_data(show_spinner=False)
def cargar_metricas_mlflow() -> dict:
    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def ultima_semana(df: pd.DataFrame) -> pd.DataFrame:
    """Fila mas reciente (anio, semana) por producto."""
    idx = df.groupby("producto")["fecha"].idxmax()
    return df.loc[idx].sort_values("precio_promedio", ascending=False)


# ---------------------------------------------------------------------------
# Sidebar - navegacion entre las 6 vistas
# ---------------------------------------------------------------------------
st.sidebar.title("🥔 Alerta de Precios Lima")
st.sidebar.caption("food-price-forecasting-peru · Big Data Analytics UNMSM")

vista = st.sidebar.radio(
    "Selecciona una vista",
    [
        "1. Alertas en Tiempo Real",
        "2. Ranking de Precios",
        "3. Segmentacion por Volatilidad",
        "4. Historico de Precios",
        "5. Sentimiento en Redes Sociales",
        "6. Salud del Sistema",
    ],
)

if st.sidebar.button("🔄 Actualizar datos ahora"):
    cargar_kpi_precios.clear()
    cargar_kpi_sentimiento.clear()
    cargar_clusters.clear()
    st.rerun()

st.sidebar.caption(
    f"La Vista 1 se refresca automaticamente cada {REFRESH_SECONDS // 60} minutos."
)

# Carga perezosa y con manejo de errores si aun no existen los Parquet
try:
    df_precios = cargar_kpi_precios()
    df_sentimiento = cargar_kpi_sentimiento()
    df_clusters = cargar_clusters()
    metricas = cargar_metricas_mlflow()
    datos_ok = True
except FileNotFoundError as e:
    datos_ok = False
    st.error(
        "No se encontraron las tablas de la Zona Oro en la carpeta `oro/`. "
        f"Detalle: {e}\n\n"
        "Copia ahi kpi_precios.parquet, kpi_sentimiento.parquet y "
        "clusters_productos.parquet (o sincroniza el bucket de GCS)."
    )

# ===========================================================================
# VISTA 1 - Alertas de Precio en Tiempo Real
# ===========================================================================
if datos_ok and vista.startswith("1"):
    st.title("🚨 Alertas de Precio en Tiempo Real")
    st.caption("Que alimentos estan en alerta ahora mismo? Fuente: kpi_precios (Zona Oro)")

    actual = ultima_semana(df_precios)
    n_alerta = int((actual["alerta"] == "ALERTA").sum())
    n_atencion = int((actual["alerta"] == "ATENCION").sum())
    n_normal = int((actual["alerta"] == "NORMAL").sum())

    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 ALERTA (>10%)", n_alerta)
    c2.metric("🟡 ATENCION (5-10%)", n_atencion)
    c3.metric("🟢 NORMAL", n_normal)

    st.divider()
    st.subheader("Estado actual por producto")

    tabla = actual[["producto", "precio_promedio", "variacion_porcentual", "alerta"]].copy()
    tabla.columns = ["Producto", "Precio (S/ x kg)", "Variacion semanal (%)", "Alerta"]

    def _icono(a):
        return {"ALERTA": "🔴", "ATENCION": "🟡", "NORMAL": "🟢"}.get(a, "⚪")

    tabla.insert(0, "", tabla["Alerta"].apply(_icono))
    st.dataframe(
        tabla.style.format({"Precio (S/ x kg)": "S/ {:.2f}", "Variacion semanal (%)": "{:+.2f}%"}),
        use_container_width=True,
        hide_index=True,
    )

    ultima_fecha = actual["fecha"].max()
    st.caption(f"Ultima semana con datos: {ultima_fecha:%Y-%m-%d} (anio-semana ISO).")

# ===========================================================================
# VISTA 2 - Ranking de Precios
# ===========================================================================
elif datos_ok and vista.startswith("2"):
    st.title("📊 Ranking de Precios")
    st.caption("Productos ordenados de mayor a menor precio promedio por kg. Fuente: kpi_precios")

    anios = sorted(df_precios["anio"].unique(), reverse=True)
    anio_sel = st.selectbox("Año", anios, index=0)

    df_anio = df_precios[df_precios["anio"] == anio_sel]
    ranking = (
        df_anio.groupby("producto", as_index=False)["precio_promedio"]
        .mean()
        .sort_values("precio_promedio", ascending=True)
    )

    fig = px.bar(
        ranking,
        x="precio_promedio",
        y="producto",
        orientation="h",
        text_auto=".2f",
        labels={"precio_promedio": "Precio promedio (S/ x kg)", "producto": "Producto"},
        title=f"Precio promedio por kg - {anio_sel}",
        color="precio_promedio",
        color_continuous_scale="Oranges",
    )
    fig.update_layout(coloraxis_showscale=False, height=450)
    st.plotly_chart(fig, use_container_width=True)

# ===========================================================================
# VISTA 3 - Segmentacion por Volatilidad (Clusters)
# ===========================================================================
elif datos_ok and vista.startswith("3"):
    st.title("🧬 Segmentacion de Mercados por Volatilidad")
    st.caption(
        "Cada punto es un producto. Eje X: precio historico. Eje Y: volatilidad. "
        "Color: cluster (Modelo 2). Fuente: clusters_productos"
    )

    fig = px.scatter(
        df_clusters,
        x="precio_promedio_historico",
        y="volatilidad",
        color=df_clusters["cluster"].astype(str),
        text="producto",
        size="precio_maximo_historico",
        hover_data={
            "precio_promedio_historico": ":.2f",
            "volatilidad": ":.2f",
            "precio_maximo_historico": ":.2f",
            "precio_minimo_historico": ":.2f",
        },
        labels={
            "precio_promedio_historico": "Precio promedio historico (S/ x kg)",
            "volatilidad": "Volatilidad (desv. estandar)",
            "color": "Cluster",
        },
        title="Segmentacion de productos agricolas por precio y volatilidad",
    )
    fig.update_traces(textposition="top center", marker=dict(line=dict(width=1, color="white")))
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Caracteristicas por cluster")
    resumen = (
        df_clusters.groupby("cluster")
        .agg(
            n_productos=("producto", "count"),
            productos=("producto", lambda s: ", ".join(s)),
            precio_promedio=("precio_promedio_historico", "mean"),
            volatilidad_promedio=("volatilidad", "mean"),
        )
        .reset_index()
    )
    st.dataframe(
        resumen.style.format({"precio_promedio": "S/ {:.2f}", "volatilidad_promedio": "{:.2f}"}),
        use_container_width=True,
        hide_index=True,
    )
    modelo_info = df_clusters["modelo"].iloc[0]
    silhouette = df_clusters["silhouette"].iloc[0]
    st.caption(f"Modelo: {modelo_info} · Silhouette score: {silhouette:.3f}")

# ===========================================================================
# VISTA 4 - Historico de Precios
# ===========================================================================
elif datos_ok and vista.startswith("4"):
    st.title("📈 Historico de Precios")
    st.caption("Evolucion temporal del precio por producto. Fuente: kpi_precios")

    productos_disponibles = sorted(df_precios["producto"].unique())
    col_a, col_b = st.columns([2, 2])
    with col_a:
        productos_sel = st.multiselect(
            "Productos", productos_disponibles, default=productos_disponibles
        )
    with col_b:
        fecha_min = df_precios["fecha"].min().date()
        fecha_max = df_precios["fecha"].max().date()
        rango = st.slider(
            "Rango de fechas",
            min_value=fecha_min,
            max_value=fecha_max,
            value=(fecha_min, fecha_max),
        )

    df_filtrado = df_precios[
        (df_precios["producto"].isin(productos_sel))
        & (df_precios["fecha"].dt.date >= rango[0])
        & (df_precios["fecha"].dt.date <= rango[1])
    ]

    fig = px.line(
        df_filtrado,
        x="fecha",
        y="precio_promedio",
        color="producto",
        labels={"fecha": "Fecha", "precio_promedio": "Precio promedio (S/ x kg)", "producto": "Producto"},
        title="Evolucion del precio promedio semanal por producto",
    )
    fig.update_layout(height=500, legend_title="Producto")
    st.plotly_chart(fig, use_container_width=True)

# ===========================================================================
# VISTA 5 - Sentimiento en Redes Sociales
# ===========================================================================
elif datos_ok and vista.startswith("5"):
    st.title("💬 Sentimiento en Redes Sociales")
    st.caption("Sentimiento promedio semanal de Twitter/X. Fuente: kpi_sentimiento")

    total_tweets = int(df_sentimiento["n_tweets"].sum())
    pct_neg_promedio = df_sentimiento["porcentaje_negativos"].mean()

    c1, c2 = st.columns(2)
    c1.metric("Total de tweets analizados", f"{total_tweets:,}")
    c2.metric("% promedio de tweets negativos", f"{pct_neg_promedio:.1f}%")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_sentimiento["fecha"],
            y=df_sentimiento["sentiment_promedio"],
            mode="lines",
            name="Sentimiento promedio",
            line=dict(color="#457b9d", width=2),
        )
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(
        title="Sentimiento promedio semanal (linea en 0 separa positivo de negativo)",
        xaxis_title="Fecha",
        yaxis_title="Sentimiento promedio (VADER)",
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Ver % de tweets negativos por semana"):
        fig2 = px.line(
            df_sentimiento,
            x="fecha",
            y="porcentaje_negativos",
            labels={"fecha": "Fecha", "porcentaje_negativos": "% tweets negativos"},
        )
        fig2.update_layout(height=350)
        st.plotly_chart(fig2, use_container_width=True)

# ===========================================================================
# VISTA 6 - Salud del Sistema
# ===========================================================================
elif vista.startswith("6"):
    st.title("🩺 Salud del Sistema")
    st.caption("Estado operativo del pipeline y metricas de auditoria de los modelos ML")

    if not METRICS_FILE.exists():
        st.error("No se encontro mlflow_metricas.json con las metricas de los modelos.")
    else:
        metricas = cargar_metricas_mlflow()

        st.subheader("Estado de las fuentes de datos")
        df_fuentes = pd.DataFrame(metricas["fuentes_datos"])
        st.dataframe(df_fuentes, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Metricas de los modelos (registro de auditoria MLflow)")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Modelo 1 - Forecasting**")
            df_m1 = pd.DataFrame(metricas["modelo1_forecasting"]["runs"])
            mejor_m1 = df_m1[df_m1["es_mejor"]].iloc[0]
            st.metric("RMSE (mejor run)", f"{mejor_m1['RMSE']:.3f}")
            st.metric("R² (mejor run)", f"{mejor_m1['R2']:.3f}")
            st.caption(f"Mejor algoritmo: {mejor_m1['algoritmo']} ({mejor_m1['run_name']})")
            with st.expander("Comparar todos los runs registrados"):
                st.dataframe(
                    df_m1[["run_name", "algoritmo", "RMSE", "R2", "MAE"]],
                    use_container_width=True,
                    hide_index=True,
                )

        with col2:
            st.markdown("**Modelo 3 - Clasificacion de alerta**")
            df_m3 = pd.DataFrame(metricas["modelo3_clasificacion"]["runs"])
            mejor_m3 = df_m3[df_m3["es_mejor"]].iloc[0]
            st.metric("AUC-ROC (mejor run)", f"{mejor_m3['AUC_ROC']:.3f}")
            st.metric("F1-Score (mejor run)", f"{mejor_m3['F1']:.3f}")
            st.caption(f"Mejor algoritmo: {mejor_m3['algoritmo']} ({mejor_m3['run_name']})")
            with st.expander("Comparar todos los runs registrados"):
                st.dataframe(
                    df_m3[["run_name", "algoritmo", "AUC_ROC", "F1"]],
                    use_container_width=True,
                    hide_index=True,
                )

        st.divider()
        if datos_ok:
            ultima_actualizacion = df_precios["fecha"].max()
            st.info(
                f"🕒 Ultima actualizacion de datos (kpi_precios): "
                f"{ultima_actualizacion:%Y-%m-%d}. "
                f"Vista consultada el {datetime.now():%Y-%m-%d %H:%M}."
            )
        else:
            st.warning("No se pudo leer kpi_precios para calcular la ultima actualizacion.")

st.sidebar.divider()
st.sidebar.caption("Entregable 6 · Dashboard Streamlit · Dia 12-13")
