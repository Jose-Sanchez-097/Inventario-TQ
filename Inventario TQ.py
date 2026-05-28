import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# Configuración de la página web
st.set_page_config(page_title="Inventario TQ Online", layout="wide")
st.title("📦 Control de Inventario e Historial TQ")

# --- CONFIGURACIÓN DE SEGURIDAD ---
CONTRASENA_CORRECTA = "TQ2026"

# 1. ⚠️ PEGA AQUÍ EL ENLACE COMPLETO DE TU GOOGLE SHEETS PARA LECTURA ⚠️
URL_COMPLETA_GOOGLE = "https://docs.google.com/spreadsheets/d/1DnYaNa7rJTJZCIIs9GyOMxEeusL7SHoTJjjZwjbV_LI/edit"

# 2. ⚠️ CONFIGURA AQUÍ LOS DATOS DE TU GOOGLE FORM PARA ESCRITURA ⚠️
URL_FORM_RESPONSE = "https://docs.google.com/forms/d/e/1FAIpQLScVSnm26xUibVlI8_cvzsqqLLkdLUhWfeA2z9-p-livjUlljA/formResponse?usp=pp_url&entry.939486531=1&entry.1861198387=2&entry.367765609=3&entry.797414005=4&entry.1971304507=5&entry.36072344=6&entry.209965346=4&entry.80107347=5&entry.257529099=8"

# --- LECTURA DIRECTA Y CONSOLIDACIÓN ---
try:
    base_url = URL_COMPLETA_GOOGLE.split("/edit")[0]
    URL_LECTURA_DIRECTA = f"{base_url}/export?format=csv"
    df_raw = pd.read_csv(URL_LECTURA_DIRECTA)
    
    if not df_raw.empty:
        # Limpiar espacios en los nombres de las columnas
        df_raw.columns = [c.strip() for c in df_raw.columns]
        df_raw = df_raw.dropna(how="all")
        
        # Forzar ID a numérico de forma segura
        df_raw["ID"] = pd.to_numeric(df_raw["ID"], errors="coerce").fillna(0).astype(int)
        
        # --- CONSOLIDACIÓN DE DUPLICADOS ---
        # Si Google Forms añade "Marca temporal", la usamos para ordenar. 
        # Si no existe, confiamos en el orden posicional (las filas de abajo son las más nuevas).
        if "Marca temporal" in df_raw.columns:
            df_raw["Marca temporal"] = pd.to_datetime(df_raw["Marca temporal"], errors="coerce")
            df_raw = df_raw.sort_values(by="Marca temporal", ascending=True)
        
        # Conservamos ÚNICAMENTE la última fila registrada para cada ID (el estado más actual)
        df_db = df_raw.drop_duplicates(subset=["ID"], keep="last").copy()
        
        # Calcular el siguiente ID disponible basándonos en el histórico completo
        id_siguiente = int(df_raw["ID"].max()) + 1
    else:
        df_db = pd.DataFrame(columns=[
            "ID", "Tipo Insumo", "Medidas", "Eficiencia", "Clase", "Equipo", "Cant. Actual", "Verificado Por", "Observaciones"
        ])
        id_siguiente = 1
except Exception as e:
    st.error(f"Error crítico al conectar con la Base de Datos. Detalles: {e}")
    st.stop()

# --- FUNCIÓN DE ESCRITURA MEDIANTE FORMULARIO ---
def enviar_datos_formulario(id_val, tipo_val, med_val, efic_val, clase_val, eq_val, cant_val, verif_val, obs_val):
    # ⚠️ REEMPLAZA LOS NÚMEROS 'entry.XXXXXX' CON LOS TUYOS REALES ⚠️
    form_data = {
        "entry.100001": str(id_val),       
        "entry.100002": str(tipo_val),     
        "entry.100003": str(med_val),      
        "entry.100004": str(efic_val),     
        "entry.100005": str(clase_val),    
        "entry.100006": str(eq_val),       
        "entry.100007": str(cant_val),     
        "entry.100008": str(verif_val),    
        "entry.100009": str(obs_val)       
    }
    try:
        respuesta = requests.post(URL_FORM_RESPONSE, data=form_data)
        return True
    except Exception as e:
        st.error(f"Error de red al sincronizar con la nube: {e}")
        return False

# Historial en memoria de la sesión
if "historial" not in st.session_state:
    st.session_state.historial = pd.DataFrame(columns=["Fecha/Hora", "Acción", "Elemento", "Detalle"])

def registrar_movimiento(accion, item_id, detalle):
    nueva_fila = {
        "Fecha/Hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Acción": accion,
        "Elemento": f"ID: {item_id}",
        "Detalle": detalle
    }
    st.session_state.historial = pd.concat([pd.DataFrame([nueva_fila]), st.session_state.historial], ignore_index=True).head(50)

# --- FORMULARIO DE ENTRADA EN INTERFAZ ---
st.subheader("📝 Gestión de Ítems")

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

col1, col2, col3, col4 = st.columns(4)

with col1:
    tipo = st.text_input("Tipo de Insumo", disabled=st.session_state.edit_id is not None)
    clase = st.text_input("Clase", disabled=st.session_state.edit_id is not None)
with col2:
    medidas = st.text_input("Medidas", disabled=st.session_state.edit_id is not None)
    equipo = st.text_input("Equipo", disabled=st.session_state.edit_id is not None)
with col3:
    eficiencia = st.text_input("Eficiencia", disabled=st.session_state.edit_id is not None)
    cantidad = st.text_input("Cantidad Actual")
with col4:
    verificado = st.text_input("Verificado Por")
    observaciones = st.text_input("Observaciones")

# --- BOTONES DE ACCIÓN ---
b_col1, b_col2, b_col3 = st.columns([2, 2, 8])

if st.session_state.edit_id is None:
    if b_col1.button("✨ Agregar Insumo", use_container_width=True):
        if tipo and cantidad and verificado:
            try:
                cant_val = float(cantidad)
                if enviar_datos_formulario(id_siguiente, tipo, medidas, eficiencia, clase, equipo, cant_val, verificado, observaciones):
                    registrar_movimiento("REGISTRO", id_siguiente, f"Creado: {tipo} | Stock: {cantidad}")
                    st.success("Insumo guardado de forma permanente en la base de datos.")
                    st.rerun()
            except ValueError:
                st.error("Por favor, introduce un número válido en Cantidad Actual.")
        else:
            st.warning("Por favor llena los campos obligatorios (Tipo, Cantidad y Verificado Por).")
else:
    if b_col1.button("💾 Guardar Cambios", use_container_width=True):
        try:
            cant_val = float(cantidad)
            idx = df_db[df_db["ID"] == st.session_state.edit_id].index[0]
            
            t_fijo = df_db.at[idx, "Tipo Insumo"]
            m_fijo = df_db.at[idx, "Medidas"]
            e_fijo = df_db.at[idx, "Eficiencia"]
            c_fijo = df_db.at[idx, "Clase"]
            eq_fijo = df_db.at[idx, "Equipo"]
            
            if enviar_datos_formulario(st.session_state.edit_id, t_fijo, m_fijo, e_fijo, c_fijo, eq_fijo, cant_val, verificado, observaciones):
                registrar_movimiento("MODIFICACIÓN", st.session_state.edit_id, f"Nueva Cant.: {cantidad} | Por: {verificado}")
                st.session_state.edit_id = None
                st.success("Cambios sincronizados.")
                st.rerun()
        except ValueError:
            st.error("Por favor, introduce un número válido en Cantidad Actual.")
            
    if b_col2.button("❌ Cancelar Edición", use_container_width=True):
        st.session_state.edit_id = None
        st.rerun()

st.markdown("---")

# --- PESTAÑAS DE VISTA DE DATOS ---
tab_inv, tab_hist = st.tabs(["📋 Inventario Actual", "📜 Historial de Movimientos"])

with tab_inv:
    buscar = st.text_input("🔍 Buscar ítem en el inventario...")
    df_filtrado = df_db.copy()
    
    # Ocular la columna de marca temporal de Google en la visualización para limpieza de la interfaz
    if "Marca temporal" in df_filtrado.columns:
        df_filtrado = df_filtrado.drop(columns=["Marca temporal"])
    
    if buscar:
        mask = df_filtrado.astype(str).apply(lambda x: x.str.contains(buscar, case=False)).any(axis=1)
        df_filtrado = df_filtrado[mask]

    def colorear_stock_bajo(row):
        try:
            val = float(row['Cant. Actual'])
            return ['background-color: #ffebdb; color: #d35400' if val < 5 else '' for _ in row]
        except:
            return ['' for _ in row]

    if not df_filtrado.empty:
        df_styled = df_filtrado.style.apply(colorear_stock_bajo, axis=1)
        st.dataframe(df_styled, use_container_width=True, hide_index=True)
        
        st.write("---")
        st.write("**⚠️ Acciones de Control:**")
        st.info("Para modificar existencias, introduce el ID del ítem abajo. Nota: Cada modificación añadirá una nueva fila histórica en Google Sheets, pero la aplicación siempre mostrará el valor más reciente.")
        
        act_col1, act_col2 = st.columns([2, 10])
        id_seleccionar = act_col1.number_input("ID del Ítem para Modificar:", min_value=1, step=1, key="id_control")
        
        if act_col2.button("✏️ Cargar Ítem en el Formulario", use_container_width=True):
            if id_seleccionar in df_db["ID"].values:
                st.session_state.edit_id = id_seleccionar
                st.rerun()
            else:
                st.error("El ID seleccionado no existe en el inventario.")
    else:
        st.info("El inventario está vacío o no hay coincidencias.")

with tab_hist:
    st.dataframe(st.session_state.historial, use_container_width=True, hide_index=True)
    
