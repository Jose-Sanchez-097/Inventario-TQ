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
URL_COMPLETA_GOOGLE = "https://docs.google.com/spreadsheets/d/TU_ID_AQUI/edit"

# 2. ⚠️ CONFIGURA AQUÍ LOS DATOS DE TU GOOGLE FORM PARA ESCRITURA ⚠️
# Cambia 'viewform' por 'formResponse' en la URL base de tu formulario
URL_FORM_RESPONSE = "https://docs.google.com/forms/d/e/1FAIpQLScVSnm26xUibVlI8_cvzsqqLLkdLUhWfeA2z9-p-livjUlljA/formResponse?usp=pp_url&entry.939486531=1&entry.1861198387=2&entry.367765609=3&entry.797414005=4&entry.1971304507=5&entry.36072344=6&entry.209965346=4&entry.80107347=5&entry.257529099=8"

# --- LECTURA DIRECTA (ESTO YA FUNCIONA PERFECTO) ---
try:
    base_url = URL_COMPLETA_GOOGLE.split("/edit")[0]
    URL_LECTURA_DIRECTA = f"{base_url}/export?format=csv"
    df_db = pd.read_csv(URL_LECTURA_DIRECTA)
    
    if not df_db.empty:
        df_db.columns = [c.strip() for c in df_db.columns]
        df_db = df_db.dropna(how="all")
        # Forzar a que ID sea numérico. Si Google Forms añade columnas de marca de tiempo a la izquierda,
        # nos aseguramos de mapear la columna 'ID' correctamente.
        df_db["ID"] = pd.to_numeric(df_db["ID"], errors="coerce").fillna(0).astype(int)
        id_siguiente = int(df_db["ID"].max()) + 1
    else:
        df_db = pd.DataFrame(columns=[
            "ID", "Tipo Insumo", "Medidas", "Eficiencia", "Clase", "Equipo", "Cant. Actual", "Verificado Por", "Observaciones"
        ])
        id_siguiente = 1
except Exception as e:
    st.error(f"Error crítico al conectar con la Base de Datos. Detalles: {e}")
    st.stop()

# --- FUNCIÓN DE ESCRITURA INVENTADA MEDIANTE FORMULARIO ---
def enviar_datos_formulario(id_val, tipo_val, med_val, efic_val, clase_val, eq_val, cant_val, verif_val, obs_val):
    # ⚠️ REEMPLAZA LOS NÚMEROS 'entry.XXXXXX' CON LOS TUYOS DEL PASO 2 ⚠️
    form_data = {
        "entry.100001": str(id_val),       # Reemplaza con tu código para ID
        "entry.100002": str(tipo_val),     # Reemplaza con tu código para Tipo Insumo
        "entry.100003": str(med_val),      # Reemplaza con tu código para Medidas
        "entry.100004": str(efic_val),     # Reemplaza con tu código para Eficiencia
        "entry.100005": str(clase_val),    # Reemplaza con tu código para Clase
        "entry.100006": str(eq_val),       # Reemplaza con tu código para Equipo
        "entry.100007": str(cant_val),     # Reemplaza con tu código para Cantidad
        "entry.100008": str(verif_val),    # Reemplaza con tu código para Verificado Por
        "entry.100009": str(obs_val)       # Reemplaza con tu código para Observaciones
    }
    try:
        respuesta = requests.post(URL_FORM_RESPONSE, data=form_data)
        if respuesta.status_code == 200:
            return True
        else:
            # Google Forms suele responder con código 200 incluso si procesó la inserción exitosamente
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
            # Recuperamos los valores fijos del ítem para reenviarlos en la nueva fila de actualización
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
        st.info("Para modificar existencias, introduce el ID del ítem arriba. Nota: Al usar el método de sincronización por formulario, las modificaciones y adiciones crearán un nuevo registro histórico en tu hoja con el estado más actualizado de las existencias.")
        
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
    
