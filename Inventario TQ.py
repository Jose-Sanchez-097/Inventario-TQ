import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Configuración de la página web
st.set_page_config(page_title="Inventario TQ Online", layout="wide")
st.title("📦 Control de Inventario e Historial TQ")

# --- CONFIGURACIÓN DE SEGURIDAD ---
CONTRASENA_CORRECTA = "TQ2026"

# ⚠️ PEGA AQUÍ EL LINK DE TU GOOGLE SHEETS ENTRE LAS COMILLAS ⚠️
URL_HOJA_CALCULO = "https://docs.google.com/spreadsheets/d/1DnYaNa7rJTJZCIIs9GyOMxEeusL7SHoTJjjZwjbV_LI/edit?usp=sharing"

# --- CONEXIÓN DIRECTA A GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Leer datos existentes
    df_db = conn.read(spreadsheet=URL_HOJA_CALCULO, worksheet="Sheet1", ttl=0)
    # Asegurar que el ID sea numérico
    if not df_db.empty:
        df_db["ID"] = pd.to_numeric(df_db["ID"])
        id_siguiente = int(df_db["ID"].max()) + 1
    else:
        id_siguiente = 1
except Exception as e:
    st.error("Error de conexión con Google Sheets. Verifica los permisos de edición.")
    st.stop()

# Historial temporal (el historial puede seguir en memoria o puedes crear otra hoja si lo requieres)
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
                # Añadir fila al DataFrame actual y subirlo a la nube
                df_actualizado = pd.concat([df_db, pd.DataFrame([nuevo_item])], ignore_index=True)
                conn.update(spreadsheet=URL_HOJA_CALCULO, worksheet="Sheet1", data=df_actualizado)
                registrar_movimiento("REGISTRO", id_siguiente, f"Creado: {tipo} | Equipo: {equipo} | Stock: {cantidad}")
                st.success("Insumo guardado permanentemente en la nube.")
                st.flush()
                st.rerun()
            except ValueError:
                st.error("Por favor, introduce un número válido en Cantidad Actual.")
        else:
            st.warning("Por favor llena los campos obligatorios (Tipo, Cantidad y Verificado Por).")
else:
    if b_col1.button("💾 Guardar Cambios", use_container_width=True):
        try:
            cant_val = float(cantidad)
            # Buscar el índice en el DataFrame proveniente de Google Sheets
            idx = df_db[df_db["ID"] == st.session_state.edit_id].index[0]
            df_db.at[idx, "Cant. Actual"] = cant_val
            df_db.at[idx, "Verificado Por"] = verificado
            df_db.at[idx, "Observaciones"] = observaciones
            
            # Subir cambios
            conn.update(spreadsheet=URL_HOJA_CALCULO, worksheet="Sheet1", data=df_db)
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
    buscar = st.text_input("🔍 Buscar ítem en el inventario (Filtra en tiempo real)...")
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
                # Pre-cargar datos en el formulario
                item_edit = df_db[df_db["ID"] == id_seleccionar].iloc[0]
                st.rerun()
            else:
                st.error("El ID seleccionado no existe en el inventario.")
                
        clave_del = act_col3.text_input("Contraseña de seguridad:", type="password", key="pass_del", placeholder="Requerida para eliminar")
        if act_col4.button("🗑️ Eliminar Ítem de forma definitiva", use_container_width=True):
            if clave_del == CONTRASENA_CORRECTA:
                if id_seleccionar in df_db["ID"].values:
                    df_recortado = df_db[df_db["ID"] != id_seleccionar]
                    conn.update(spreadsheet=URL_HOJA_CALCULO, worksheet="Sheet1", data=df_recortado)
                    registrar_movimiento("ELIMINACIÓN", id_seleccionar, f"Eliminado de la base de datos.")
                    st.success(f"El registro con ID {id_seleccionar} fue eliminado de la nube.")
                    st.rerun()
                else:
                    st.error("El ID seleccionado no existe.")
            else:
                st.error("Acceso denegado: Contraseña incorrecta.")
    else:
        st.info("El inventario se encuentra vacío o ningún elemento coincide con la búsqueda.")

with tab_hist:
    st.dataframe(st.session_state.historial, use_container_width=True, hide_index=True)
    
