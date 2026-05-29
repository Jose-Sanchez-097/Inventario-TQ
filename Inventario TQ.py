import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario TQ Online", layout="wide")
URL_DB = "https://docs.google.com/spreadsheets/d/1DnYaNa7rJTJZCIIs9GyOMxEeusL7SHoTJjjZwjbV_LI/export?format=csv&gid=1927911440"
URL_FORM = "https://docs.google.com/forms/d/e/1FAIpQLScVSnm26xUibVlI8_cvzsqqLLkdLUhWfeA2z9-p-livjUlljA/formResponse"
CONTRASENA_CORRECTA = "TQ2026"

# --- LÓGICA DE DATOS ---
@st.cache_data(ttl=30) # Reducido a 30s para mayor frescura
def cargar_datos(url):
    df = pd.read_csv(url)
    df.columns = [str(c).strip() for c in df.columns]
    return df.dropna(how="all")

if "df_base" not in st.session_state:
    st.session_state.df_base = cargar_datos(URL_DB)

def obtener_inventario_limpio():
    df = st.session_state.df_base.copy()
    # Limpieza de nulos y tipos
    df["ID"] = pd.to_numeric(df["ID"], errors="coerce")
    df = df.dropna(subset=["ID"])
    df = df.drop_duplicates(subset=["ID"], keep="last")
    # Filtro: Excluir "ELIMINADO" (case insensitive)
    df = df[df["Tipo Insumo"].astype(str).str.upper() != "ELIMINADO"]
    return df.fillna("N/A")

# --- FUNCIONES ---
def enviar_datos(datos):
    return requests.post(URL_FORM, data=datos).status_code == 200

# --- UI PRINCIPAL ---
st.title("📦 Control de Inventario TQ")
df_db = obtener_inventario_limpio()

# --- ZONA DE ELIMINACIÓN ---
with st.expander("🗑️ Zona de Eliminación"):
    c1, c2, c3 = st.columns([2, 3, 3])
    id_del = c1.number_input("ID a borrar", min_value=1, step=1)
    clave = c2.text_input("Contraseña", type="password")
    if c3.button("Confirmar Eliminación"):
        if clave == CONTRASENA_CORRECTA:
            if id_del in df_db["ID"].values:
                datos = {"entry.939486531": str(id_del), "entry.209965346": "-1", "entry.1861198387": "ELIMINADO"}
                if enviar_datos(datos):
                    st.success("Eliminado correctamente.")
                    st.session_state.df_base = cargar_datos(URL_DB) # Forzar refresco
                    st.rerun()
            else:
                st.error("ID no encontrado.")
        else:
            st.error("Contraseña incorrecta.")

# --- VISTA DE DATOS (Tu estructura original) ---
tab_inv, tab_hist = st.tabs(["📋 Inventario Actual", "📜 Historial"])

with tab_inv:
    # Renderizado de tarjetas original
    for _, row in df_db.iterrows():
        cant = float(row["Cant. Actual"]) if row["Cant. Actual"] != "N/A" else 0
        titulo = f"⚠️ [#{row['ID']}] {row['Tipo Insumo']} (Crítico)" if cant < 5 else f"📦 [#{row['ID']}] {row['Tipo Insumo']}"
        
        with st.expander(titulo):
            cols = st.columns(7)
            cols[0].markdown(f"**Medidas:**\n{row['Medidas']}")
            cols[1].markdown(f"**Eficiencia:**\n{row['Eficiencia']}")
            cols[2].markdown(f"**Clase:**\n{row['Clase']}")
            cols[3].markdown(f"**Equipo:**\n{row['Equipo']}")
            cols[4].markdown(f"**Cant. Actual:**\n{cant}")
            cols[5].markdown(f"**Verificado:**\n{row['Verificado Por']}")
            cols[6].markdown(f"**Obs:**\n{row['Observaciones']}")

with tab_hist:
    st.dataframe(df_db, use_container_width=True)
