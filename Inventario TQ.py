import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario TQ Online", layout="wide")
URL_BD = "https://docs.google.com/spreadsheets/d/1DnYaNa7rJTJZCIIs9GyOMxEeusL7SHoTJjjZwjbV_LI/export?format=csv&gid=1927911440"
URL_FORM = "https://docs.google.com/forms/d/e/1FAIpQLScVSnm26xUibVlI8_cvzsqqLLkdLUhWfeA2z9-p-livjUlljA/formResponse"
CONTRASENA_CORRECTA = "TQ2026"

# --- LÓGICA DE DATOS ---
@st.cache_data(ttl=60)
def cargar_datos(url):
    df = pd.read_csv(url)
    df.columns = [str(c).strip() for c in df.columns]
    return df.dropna(how="all")

if "df_base" not in st.session_state:
    st.session_state.df_base = cargar_datos(URL_BD)

def obtener_inventario_limpio():
    df = st.session_state.df_base.copy()
    # Mapeo y limpieza
    df = df.rename(columns={c: "ID" for c in df.columns if "ID" in c.upper() and len(c) < 6})
    df["ID"] = pd.to_numeric(df["ID"], errors="coerce")
    df = df.drop_duplicates(subset=["ID"], keep="last")
    
    # Filtro: Excluir "ELIMINADO" y negativos
    df = df[(df["Tipo Insumo"].astype(str).str.upper() != "ELIMINADO") & 
            (df["Cant. Actual"].astype(float) >= 0)]
    return df.fillna("N/A")

# --- FUNCIONES DE ENVÍO ---
def enviar_datos_formulario(id_val, tipo_val, med_val, efic_val, clase_val, eq_val, cant_val, verif_val, obs_val):
    form_data = {
        "entry.939486531": str(id_val), "entry.1861198387": str(tipo_val),
        "entry.367765609": str(med_val), "entry.797414005": str(efic_val),
        "entry.1971304507": str(clase_val), "entry.36072344": str(eq_val),
        "entry.209965346": str(cant_val), "entry.80107347": str(verif_val),
        "entry.257529099": str(obs_val)
    }
    return requests.post(URL_FORM, data=form_data).status_code == 200

# --- HISTORIAL ---
if "historial" not in st.session_state:
    st.session_state.historial = pd.DataFrame(columns=["Fecha/Hora", "Acción", "Elemento", "Detalle"])

def registrar_movimiento(accion, item_id, detalle):
    nueva_fila = pd.DataFrame([{
        "Fecha/Hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Acción": accion,
        "Elemento": f"ID: {item_id}",
        "Detalle": detalle
    }])
    st.session_state.historial = pd.concat([nueva_fila, st.session_state.historial], ignore_index=True).head(50)

# --- UI PRINCIPAL ---
st.title("📦 Control de Inventario e Historial TQ")
df_db = obtener_inventario_limpio()
id_siguiente = int(df_db["ID"].max()) + 1 if not df_db.empty else 1

# --- FORMULARIO DE ENTRADA ---
st.subheader("📝 Gestión de Ítems")
if "edit_id" not in st.session_state: st.session_state.edit_id = None

col1, col2, col3, col4 = st.columns(4)
tipo = col1.text_input("Tipo de Insumo", disabled=st.session_state.edit_id is not None)
clase = col1.text_input("Clase", disabled=st.session_state.edit_id is not None)
medidas = col2.text_input("Medidas", disabled=st.session_state.edit_id is not None)
equipo = col2.text_input("Equipo", disabled=st.session_state.edit_id is not None)
eficiencia = col3.text_input("Eficiencia", disabled=st.session_state.edit_id is not None)
cantidad = col3.text_input("Cantidad Actual")
verificado = col4.text_input("Verificado Por")
observaciones = col4.text_input("Observaciones")

# --- BOTONES ---
b_col1, b_col2, b_col3 = st.columns([2, 2, 8])
if b_col1.button("✨ Agregar / Guardar" if st.session_state.edit_id is None else "💾 Guardar Cambios"):
    try:
        cant_val = float(cantidad)
        if enviar_datos_formulario(st.session_state.edit_id or id_siguiente, tipo, medidas, eficiencia, clase, equipo, cant_val, verificado, observaciones):
            registrar_movimiento("REGISTRO/MOD", st.session_state.edit_id or id_siguiente, f"Cant: {cantidad}")
            st.cache_data.clear()
            st.session_state.edit_id = None
            st.rerun()
    except ValueError:
        st.error("Cantidad inválida.")

# --- VISTA Y ELIMINACIÓN ---
tab_inv, tab_hist = st.tabs(["📋 Inventario Actual", "📜 Historial de Movimientos"])

with tab_inv:
    buscar = st.text_input("🔍 Buscar...")
    df_filtrado = df_db[df_db.apply(lambda row: buscar.lower() in row.astype(str).str.lower().values, axis=1)] if buscar else df_db
    
    for _, row in df_filtrado.iterrows():
        with st.expander(f"📦 {row['Tipo Insumo']} (ID: {row['ID']})"):
            st.write(f"Medidas: {row['Medidas']} | Cantidad: {row['Cant. Actual']}")

    st.write("---")
    st.subheader("🗑️ Zona de Eliminación")
    id_del = st.number_input("ID a borrar", step=1)
    pwd = st.text_input("Contraseña", type="password")
    if st.button("🔥 Confirmar Eliminación"):
        if pwd == CONTRASENA_CORRECTA:
            if enviar_datos_formulario(id_del, "ELIMINADO", "N/A", "N/A", "N/A", "N/A", -1, "SISTEMA", "Purgado"):
                st.cache_data.clear()
                st.rerun()
        else:
            st.error("Contraseña incorrecta")

with tab_hist:
    st.dataframe(st.session_state.historial)
