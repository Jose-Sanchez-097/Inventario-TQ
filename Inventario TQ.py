import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# Configuración de página
st.set_page_config(page_title="Inventario TQ Online", layout="wide")
st.title("📦 Control de Inventario e Historial TQ")

# --- CONFIGURACIÓN ---
CONTRASENA_CORRECTA = "TQ2026"
URL_LECTURA_DIRECTA = "https://docs.google.com/spreadsheets/d/1DnYaNa7rJTJZCIIs9GyOMxEeusL7SHoTJjjZwjbV_LI/export?format=csv&gid=1927911440"
URL_FORM_RESPONSE = "https://docs.google.com/forms/d/e/1FAIpQLScVSnm26xUibVlI8_cvzsqqLLkdLUhWfeA2z9-p-livjUlljA/formResponse"

# --- LÓGICA DE DATOS ---
@st.cache_data(ttl=60)
def cargar_datos_fuente(url):
    df = pd.read_csv(url)
    df.columns = [str(c).strip() for c in df.columns]
    return df.dropna(how="all")

# Carga inicial o desde estado
if "df_base" not in st.session_state:
    st.session_state.df_base = cargar_datos_fuente(URL_LECTURA_DIRECTA)

def obtener_inventario_limpio():
    # Usamos la base de datos completa del estado
    df = st.session_state.df_base.copy()
    # Asegurar que ID sea numérico para consolidar
    df["ID"] = pd.to_numeric(df["ID"], errors="coerce")
    df = df.dropna(subset=["ID"])
    # Consolidación: último registro
    df = df.drop_duplicates(subset=["ID"], keep="last")
    # Filtro estricto
    df = df[(df["Tipo Insumo"].astype(str).str.upper() != "ELIMINADO") & 
            (df["Cant. Actual"].astype(float) >= 0)]
    return df.fillna("N/A")

def registrar_movimiento(accion, item_id, detalle):
    if "historial" not in st.session_state:
        st.session_state.historial = pd.DataFrame(columns=["Fecha/Hora", "Acción", "Elemento", "Detalle"])
    nueva_fila = {
        "Fecha/Hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Acción": accion,
        "Elemento": f"ID: {item_id}",
        "Detalle": detalle
    }
    st.session_state.historial = pd.concat([pd.DataFrame([nueva_fila]), st.session_state.historial], ignore_index=True).head(50)

# --- UI PRINCIPAL ---
df_db = obtener_inventario_limpio()
id_siguiente = int(df_db["ID"].max()) + 1 if not df_db.empty else 1

st.subheader("📝 Gestión de Ítems")
# [Tu lógica de campos de entrada va aquí]

# --- ZONA DE ELIMINACIÓN ---
with st.expander("🗑️ Zona de Eliminación de Insumos"):
    col_d1, col_d2, col_d3 = st.columns([2, 3, 3])
    with col_d1:
        id_a_borrar = st.number_input("ID a borrar:", min_value=1, step=1, key="id_borrar")
    with col_d2:
        clave_input = st.text_input("🔑 Contraseña:", type="password", key="clave_borrar")
    with col_d3:
        if st.button("🔥 Confirmar Eliminación", use_container_width=True):
            if clave_input == CONTRASENA_CORRECTA:
                # Verificación de existencia real en la base completa
                if id_a_borrar in st.session_state.df_base["ID"].values:
                    # Enviar a Google Form
                    datos = {"entry.939486531": str(id_a_borrar), "entry.209965346": "-1", "entry.1861198387": "ELIMINADO"}
                    if requests.post(URL_FORM_RESPONSE, data=datos).status_code == 200:
                        registrar_movimiento("ELIMINACIÓN", id_a_borrar, "Ítem purgado")
                        st.success(f"ID {id_a_borrar} eliminado.")
                        # Recargar datos inmediatamente
                        st.session_state.df_base = cargar_datos_fuente(URL_LECTURA_DIRECTA)
                        st.rerun()
                else:
                    st.error("El ID no existe.")
            else:
                st.error("Contraseña incorrecta.")

# --- VISTA DE DATOS ---
tab_inv, tab_hist = st.tabs(["📋 Inventario Actual", "📜 Historial de Movimientos"])

with tab_inv:
    # Aquí renderizas tus tarjetas usando df_db (que ya está limpio y filtrado)
    for _, row in df_db.iterrows():
        with st.expander(f"📦 {row.get('Tipo Insumo', 'Ítem')}"):
            st.write(f"ID: {row['ID']} | Cantidad: {row['Cant. Actual']}")

with tab_hist:
    if "historial" in st.session_state:
        st.dataframe(st.session_state.historial)
