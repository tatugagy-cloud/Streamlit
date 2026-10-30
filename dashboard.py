import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

st.set_page_config(page_title="Tablero del clima", layout="wide")

st.title("Tablero del clima")
nombre = st.text_input("¿Cómo te llamas?")
if nombre:
    st.write("Hola", nombre)

CIUDADES = {
    "San Juan del Río": (20.39, -99.99),
    "Querétaro": (20.59, -100.39),
    "Ciudad de México": (19.43, -99.13),
    "Guadalajara": (20.67, -103.35),
    "Monterrey": (25.67, -100.31),
}

st.sidebar.header("Opciones")
ciudad = st.sidebar.selectbox("Ciudad", list(CIUDADES.keys()))
dias = st.sidebar.slider("Días de historial", 3, 14, 7)


@st.cache_data(ttl=3600)
def obtener_datos(lat, lon, dias):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,shortwave_radiation",
        "past_days": dias,
        "forecast_days": 1,
        "timezone": "auto",
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    h = r.json()["hourly"]
    df = pd.DataFrame(
        {
            "fecha_hora": pd.to_datetime(h["time"]),
            "temperatura": h["temperature_2m"],
            "humedad": h["relative_humidity_2m"],
            "radiacion": h["shortwave_radiation"],
        }
    )
    df["fecha"] = df["fecha_hora"].dt.date
    df["hora"] = df["fecha_hora"].dt.hour
    return df


lat, lon = CIUDADES[ciudad]

try:
    df = obtener_datos(lat, lon, dias)
except Exception:
    st.error("No se pudieron obtener los datos de la API. Intenta de nuevo en un momento.")
    st.stop()

st.subheader(f"Clima en {ciudad}")

c1, c2, c3 = st.columns(3)
c1.metric("Temperatura promedio", f"{df['temperatura'].mean():.1f} °C")
c2.metric("Temperatura máxima", f"{df['temperatura'].max():.1f} °C")
c3.metric("Humedad promedio", f"{df['humedad'].mean():.0f} %")

st.markdown("#### Temperatura por hora")
fig1, ax1 = plt.subplots(figsize=(10, 4))
sns.lineplot(data=df, x="fecha_hora", y="temperatura", ax=ax1)
ax1.set_xlabel("Fecha")
ax1.set_ylabel("°C")
fig1.autofmt_xdate()
st.pyplot(fig1)

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("#### Radiación promedio por día")
    rad = df.groupby("fecha", as_index=False)["radiacion"].mean()
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    sns.barplot(data=rad, x="fecha", y="radiacion", ax=ax2)
    ax2.set_xlabel("Fecha")
    ax2.set_ylabel("W/m²")
    plt.setp(ax2.get_xticklabels(), rotation=45, ha="right")
    st.pyplot(fig2)

with col_b:
    st.markdown("#### Mapa de calor: temperatura por día y hora")
    pivote = df.pivot_table(index="fecha", columns="hora", values="temperatura")
    fig3, ax3 = plt.subplots(figsize=(6, 4))
    sns.heatmap(pivote, cmap="YlOrRd", ax=ax3, cbar_kws={"label": "°C"})
    ax3.set_xlabel("Hora")
    ax3.set_ylabel("Fecha")
    st.pyplot(fig3)

with st.expander("Ver datos"):
    st.dataframe(df[["fecha_hora", "temperatura", "humedad", "radiacion"]])
