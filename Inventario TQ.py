import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# Configuración de la página
st.set_page_config(page_title="Inventario TQ Online", layout="wide")
st.title("📦 Control de Inventario e Historial TQ")

# --- CONFIGURACIÓN ---
CONTRASENA_CORRECTA = "TQ2026"
URL_BASE = "https://docs.google.com/spreadsheets/d/1DnYaNa7rJTJZCIIs9GyOMxEeusL7SHoTJjjZwjbV_LI/export?format=csv&gid=1927911440"
URL_FORM = "https://docs.google.com/forms/e/1FAIpQLScVSnm26xUibVlI8_cvzsqqLLkdLUhWfeA2z9-p-livjUlljA/formResponse"

# --- FUNCIONES DE CARGA Y ESCRITURA ---
@st.cache_data(ttl=10)
def cargar_datos(url):
    return pd.read_csv(url)

def enviar_datos(id_val, tipo, med, efic, clase, eq, cant, verif, obs):
    form_data = {
        "entry.939486531": str(id_val), "entry.1861198387": str(tipo),
        "entry.367765609": str(med), "entry.797414005": str(efic),
        "entry.1971304507": str(clase), "entry.36072344": str(eq),
        "entry.209965346": str(cant), "entry.80107347": str(verif),
        "entry.257529099": str(obs)
    }
    return requests.post(URL_FORM, data=form_data).status_code == 200

# --- LÓGICA DE ESTADO ---
if "edit_id" not in st.session_state: st.session_state.edit_id = None
if "edit_datos" not in st.session_state: st.session_state.edit_datos = {}
if "historial" not in st.session_state: 
    st.session_state.historial = pd.DataFrame(columns=["Fecha/Hora", "Acción", "Elemento", "Detalle"])

# --- PROCESAMIENTO DE DATOS ---
df_raw = cargar_datos(URL_BASE + "&t=" + str(datetime.now().timestamp()))
df_raw.columns = [str(c).strip() for c in df_raw.columns]
# Parche de sincronización
if st.session_state.edit_id is not None and "Cant. Actual" in st.session_state.edit_datos:
    mask = df_raw["ID"] == st.session_state.edit_id
    df_raw.loc[mask, "Cant. Actual"] = st.session_state.edit_datos["Cant. Actual"]

df_db = df_raw.drop_duplicates(subset=["ID"], keep="last")
id_siguiente = int(df_db["ID"].max()) + 1 if not df_db.empty else 1

# --- INTERFAZ ---
st.subheader("📝 Gestión de Ítems")
c1, c2, c3, c4 = st.columns(4)
with c1:
    tipo = st.text_input("Tipo de Insumo", value=st.session_state.edit_datos.get("Tipo Insumo", ""), disabled=st.session_state.edit_id is not None)
    clase = st.text_input("Clase", value=st.session_state.edit_datos.get("Clase", ""))
with c2:
    medidas = st.text_input("Medidas", value=st.session_state.edit_datos.get("Medidas", ""))
    equipo = st.text_input("Equipo", value=st.session_state.edit_datos.get("Equipo", ""))
with c3:
    eficiencia = st.text_input("Eficiencia", value=st.session_state.edit_datos.get("Eficiencia", ""))
    cantidad = st.text_input("Cantidad Actual", value=str(st.session_state.edit_datos.get("Cant. Actual", "")))
with c4:
    verificado = st.text_input("Verificado Por", value=st.session_state.edit_datos.get("Verificado Por", ""))
    observaciones = st.text_input("Observaciones", value=st.session_state.edit_datos.get("Observaciones", ""))

b1, b2, b3 = st.columns([2, 2, 8])
if b3.button("🔄 Actualizar"): st.rerun()

if st.session_state.edit_id is None:
    if b1.button("✨ Agregar"):
        if enviar_datos(id_siguiente, tipo, medidas, eficiencia, clase, equipo, cantidad, verificado, observaciones):
            st.success("Guardado. Presiona Actualizar.")
else:
    if b1.button("💾 Guardar"):
        if enviar_datos(st.session_state.edit_id, tipo, medidas, eficiencia, clase, equipo, cantidad, verificado, observaciones):
            st.session_state.edit_id = None
            st.rerun()
    if b2.button("❌ Cancelar"):
        st.session_state.edit_id = None
        st.rerun()

# --- TABLA Y EDICIÓN ---
tab1, tab2 = st.tabs(["📋 Inventario", "📜 Historial"])
with tab1:
    buscar = st.text_input("🔍 Buscar...")
    df_v = df_db[df_db.apply(lambda row: buscar.lower() in row.astype(str).str.lower().values, axis=1)]
    for idx, row in df_v.iterrows():
        with st.expander(f"📦 {row['Tipo Insumo']}"):
            if st.button(f"Modificar {row['ID']}", key=f"btn_{row['ID']}"):
                st.session_state.edit_id = row['ID']
                st.session_state.edit_datos = row.to_dict()
                st.rerun()
