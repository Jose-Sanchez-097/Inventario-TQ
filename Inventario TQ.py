import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de la página web
st.set_page_config(page_title="Inventario TQ Online", layout="wide")
st.title("📦 Control de Inventario e Historial TQ")

# --- CONTRASEÑA DE SEGURIDAD ---
CONTRASENA_CORRECTA = "TQ2026"

# --- CONFIGURACIÓN DE BASE DE DATOS EN MEMORIA ---
if "inventario" not in st.session_state:
    st.session_state.inventario = pd.DataFrame(columns=[
        "ID", "Tipo Insumo", "Medidas", "Eficiencia", "Clase", "Equipo", "Cant. Actual", "Verificado Por", "Observaciones"
    ])
if "historial" not in st.session_state:
    st.session_state.historial = pd.DataFrame(columns=["Fecha/Hora", "Acción", "Elemento", "Detalle"])
if "id_counter" not in st.session_state:
    st.session_state.id_counter = 1

# --- FUNCIÓN PARA REGISTRAR HISTORIAL ---
def registrar_movimiento(accion, item_id, detalle):
    nueva_fila = {
        "Fecha/Hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Acción": accion,
        "Elemento": f"ID: {item_id}",
        "Detalle": detalle
    }
    # Insertar al inicio y limitar a los últimos 50 movimientos
    st.session_state.historial = pd.concat([pd.DataFrame([nueva_fila]), st.session_state.historial], ignore_index=True).head(50)

# --- FORMULARIO DE ENTRADA ---
st.subheader("📝 Gestión de Ítems")

# Control del modo edición
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

# --- BOTONES DE ACCIÓN DEL FORMULARIO ---
b_col1, b_col2, b_col3 = st.columns([2, 2, 8])

if st.session_state.edit_id is None:
    if b_col1.button("✨ Agregar Insumo", use_container_width=True):
        if tipo and cantidad and verificado:
            try:
                cant_val = float(cantidad)
                nuevo_item = {
                    "ID": st.session_state.id_counter, "Tipo Insumo": tipo, "Medidas": medidas,
                    "Eficiencia": eficiencia, "Clase": clase, "Equipo": equipo,
                    "Cant. Actual": cant_val, "Verificado Por": verificado, "Observaciones": observaciones
                }
                st.session_state.inventario = pd.concat([st.session_state.inventario, pd.DataFrame([nuevo_item])], ignore_index=True)
                registrar_movimiento("REGISTRO", st.session_state.id_counter, f"Creado: {tipo} | Equipo: {equipo} | Stock: {cantidad}")
                st.session_state.id_counter += 1
                st.rerun()
            except ValueError:
                st.error("Por favor, introduce un número válido en Cantidad Actual.")
        else:
            st.warning("Por favor llena los campos obligatorios (Tipo, Cantidad y Verificado Por).")
else:
    if b_col1.button("💾 Guardar Cambios", use_container_width=True):
        try:
            cant_val = float(cantidad)
            idx = st.session_state.inventario[st.session_state.inventario["ID"] == st.session_state.edit_id].index[0]
            st.session_state.inventario.at[idx, "Cant. Actual"] = cant_val
            st.session_state.inventario.at[idx, "Verificado Por"] = verificado
            st.session_state.inventario.at[idx, "Observaciones"] = observaciones
            registrar_movimiento("MODIFICACIÓN", st.session_state.edit_id, f"Nueva Cant.: {cantidad} | Por: {verificado}")
            st.session_state.edit_id = None
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
    # FILTRO DE BÚSQUEDA DINÁMICO
    buscar = st.text_input("🔍 Buscar ítem en el inventario (Filtra en tiempo real)...")
    df_filtrado = st.session_state.inventario.copy()
    
    if buscar:
        mask = df_filtrado.astype(str).apply(lambda x: x.str.contains(buscar, case=False)).any(axis=1)
        df_filtrado = df_filtrado[mask]

    # ALERTA VISUAL: Resaltar la fila completa en naranja si el stock es menor a 5
    def colorear_stock_bajo(row):
        try:
            val = float(row['Cant. Actual'])
            return ['background-color: #ffebdb; color: #d35400' if val < 5 else '' for _ in row]
        except:
            return ['' for _ in row]

    if not df_filtrado.empty:
        df_styled = df_filtrado.style.apply(colorear_stock_bajo, axis=1)
        st.dataframe(df_styled, use_container_width=True, hide_index=True)
        
        # PANEL DE ACCIONES SOBRE LOS ÍTEMS EXISTENTES
        st.write("---")
        st.write("**⚠️ Acciones de Control:**")
        act_col1, act_col2, act_col3, act_col4 = st.columns([2, 3, 3, 4])
        
        id_seleccionar = act_col1.number_input("ID del Ítem:", min_value=1, step=1, key="id_control")
        
        # Acción de Modificar
        if act_col2.button("✏️ Modificar (Solo Columnas Permitidas)", use_container_width=True):
            if id_seleccionar in st.session_state.inventario["ID"].values:
                st.session_state.edit_id = id_seleccionar
                st.rerun()
            else:
                st.error("El ID seleccionado no existe en el inventario.")
                
        # Acción de Eliminar Protegido por Contraseña
        clave_del = act_col3.text_input("Contraseña de seguridad:", type="password", key="pass_del", placeholder="Requerida para eliminar")
        if act_col4.button("🗑️ Eliminar Ítem de forma definitiva", use_container_width=True):
            if clave_del == CONTRASENA_CORRECTA:
                if id_seleccionar in st.session_state.inventario["ID"].values:
                    tipo_item = st.session_state.inventario[st.session_state.inventario["ID"] == id_seleccionar]["Tipo Insumo"].values[0]
                    equipo_item = st.session_state.inventario[st.session_state.inventario["ID"] == id_seleccionar]["Equipo"].values[0]
                    st.session_state.inventario = st.session_state.inventario[st.session_state.inventario["ID"] != id_seleccionar]
                    registrar_movimiento("ELIMINACIÓN", id_seleccionar, f"Eliminado: {tipo_item} | Pertenecía a Equipo: {equipo_item}")
                    st.success(f"El registro con ID {id_seleccionar} fue eliminado con éxito.")
                    st.rerun()
                else:
                    st.error("El ID seleccionado no existe.")
            else:
                st.error("Acceso denegado: Contraseña incorrecta.")
    else:
        st.info("El inventario se encuentra vacío o ningún elemento coincide con la búsqueda.")

with tab_hist:
    st.dataframe(st.session_state.historial, use_container_width=True, hide_index=True)
    
    # VACIAS HISTORIAL PROTEGIDO por Contraseña
    st.write("---")
    h_col1, h_col2 = st.columns([4, 8])
    clave_hist = h_col1.text_input("Contraseña para vaciar registro completo:", type="password", key="key_hist_v")
    if h_col1.button("⚠️ Borrar Todo el Historial"):
        if clave_hist == CONTRASENA_CORRECTA:
            st.session_state.historial = pd.DataFrame(columns=["Fecha/Hora", "Acción", "Elemento", "Detalle"])
            st.success("El historial de movimientos ha sido vaciado correctamente.")
            st.rerun()
        else:
            st.error("Acceso denegado: Contraseña incorrecta.")
            
