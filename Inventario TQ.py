import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# Configuración de la página web
st.set_page_config(page_title="Inventario TQ Online", layout="wide")
st.title("📦 Control de Inventario e Historial TQ")

# --- CONFIGURACIÓN DE SEGURIDAD ---
CONTRASENA_CORRECTA = "TQ2026"

# ⚠️ REEMPLAZA ESTO CON EL ID LARGO DE TU HOJA DE CÁLCULO ⚠️
ID_HOJA = "1DnYaNa7rJTJZCIIs9GyOMxEeusL7SHoTJjjZwjbV_LI"
NOMB_HOJA = "Sheet1"

# URL de exportación directa en formato CSV para lectura rápida y URL de envío de datos
URL_LECTURA = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/gviz/tq?tqx=out:csv&sheet={NOMB_HOJA}"
URL_ESCRITURA = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/edit"

# --- LECTURA DIRECTA DE LA BASE DE DATOS ---
try:
    # Lee la hoja de cálculo directamente a través de la API de visualización de Google como CSV
    df_db = pd.read_csv(URL_LECTURA)
    
    # Limpieza y formateo de los datos leídos
    if not df_db.empty:
        # Renombrar columnas por si acaso Google Sheets añade espacios extras
        df_db.columns = [c.strip() for c in df_db.columns]
        df_db = df_db.dropna(how="all")
        df_db["ID"] = pd.to_numeric(df_db["ID"], errors="coerce").fillna(0).astype(int)
        id_siguiente = int(df_db["ID"].max()) + 1
    else:
        # Si la hoja está completamente vacía, estructuramos las columnas manualmente
        df_db = pd.DataFrame(columns=[
            "ID", "Tipo Insumo", "Medidas", "Eficiencia", "Clase", "Equipo", "Cant. Actual", "Verificado Por", "Observaciones"
        ])
        id_siguiente = 1
except Exception as e:
    st.error(f"Error crítico al conectar con Google Sheets de forma directa. Detalles: {e}")
    st.stop()

# --- FUNCIÓN AUXILIAR PARA GUARDAR EN LA NUBE ---
def guardar_en_google_sheets(df_para_guardar):
    """ Utiliza el backend de Streamlit para reescribir los datos usando actualización directa """
    try:
        from streamlit_gsheets import GSheetsConnection
        conexion_directa = st.connection("gsheets", type=GSheetsConnection)
        conexion_directa.update(spreadsheet=URL_ESCRITURA, worksheet=NOMB_HOJA, data=df_para_guardar)
        return True
    except:
        # Alternativa de respaldo por si falla la librería de actualización
        st.error("No se pudo escribir en la hoja. Verifica que la librería 'st-gsheets-connection' siga instalada en requirements.txt")
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

# --- FORMULARIO DE ENTRADA ---
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
                nuevo_item = {
                    "ID": id_siguiente, "Tipo Insumo": tipo, "Medidas": medidas,
                    "Eficiencia": eficiencia, "Clase": clase, "Equipo": equipo,
                    "Cant. Actual": cant_val, "Verificado Por": verificado, "Observaciones": observaciones
                }
                df_actualizado = pd.concat([df_db, pd.DataFrame([nuevo_item])], ignore_index=True)
                if guardar_en_google_sheets(df_actualizado):
                    registrar_movimiento("REGISTRO", id_siguiente, f"Creado: {tipo} | Equipo: {equipo} | Stock: {cantidad}")
                    st.success("Insumo guardado exitosamente en la nube.")
                    st.rerun()
            except ValueError:
                st.error("Por favor, introduce un número válido en Cantidad Actual.")
        else:
            st.warning("Por favor llena los campos obligatorios (Tipo, Cantidad y Verificado Por).")
else:
    # Cargar datos visuales si estamos editando
    if b_col1.button("💾 Guardar Cambios", use_container_width=True):
        try:
            cant_val = float(cantidad)
            idx = df_db[df_db["ID"] == st.session_state.edit_id].index[0]
            df_db.at[idx, "Cant. Actual"] = cant_val
            df_db.at[idx, "Verificado Por"] = verificado
            df_db.at[idx, "Observaciones"] = observaciones
            
            if guardar_en_google_sheets(df_db):
                registrar_movimiento("MODIFICACIÓN", st.session_state.edit_id, f"Nueva Cant.: {cantidad} | Por: {verificado}")
                st.session_state.edit_id = None
                st.success("Cambios actualizados en la nube.")
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
        act_col1, act_col2, act_col3, act_col4 = st.columns([2, 3, 3, 4])
        
        id_seleccionar = act_col1.number_input("ID del Ítem:", min_value=1, step=1, key="id_control")
        
        if act_col2.button("✏️ Modificar (Solo Columnas Permitidas)", use_container_width=True):
            if id_seleccionar in df_db["ID"].values:
                st.session_state.edit_id = id_seleccionar
                st.rerun()
            else:
                st.error("El ID seleccionado no existe en el inventario.")
                
        clave_del = act_col3.text_input("Contraseña de seguridad:", type="password", key="pass_del")
        if act_col4.button("🗑️ Eliminar Ítem de forma definitiva", use_container_width=True):
            if clave_del == CONTRASENA_CORRECTA:
                if id_seleccionar in df_db["ID"].values:
                    df_recortado = df_db[df_db["ID"] != id_seleccionar]
                    if guardar_en_google_sheets(df_recortado):
                        registrar_movimiento("ELIMINACIÓN", id_seleccionar, "Eliminado de la base de datos.")
                        st.success(f"ID {id_seleccionar} eliminado.")
                        st.rerun()
                else:
                    st.error("El ID seleccionado no existe.")
            else:
                st.error("Contraseña incorrecta.")
    else:
        st.info("El inventario está vacío o no hay coincidencias.")

with tab_hist:
    st.dataframe(st.session_state.historial, use_container_width=True, hide_index=True)
    
