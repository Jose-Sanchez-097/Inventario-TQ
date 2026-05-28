import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# Configuración de la página web
st.set_page_config(page_title="Inventario TQ Online", layout="wide")
st.title("📦 Control de Inventario e Historial TQ")

# --- CONFIGURACIÓN DE SEGURIDAD ---
CONTRASENA_CORRECTA = "TQ2026"

# 1. ⚠️ TU ENLACE DE LECTURA DE RESPUESTAS CORREGIDO ⚠️
URL_LECTURA_DIRECTA = "https://docs.google.com/spreadsheets/d/1DnYaNa7rJTJZCIIs9GyOMxEeusL7SHoTJjjZwjbV_LI/export?format=csv&gid=1927911440"

# 2. ⚠️ LA URL DE TU GOOGLE FORM PARA ESCRITURA ⚠️
URL_FORM_RESPONSE = "https://docs.google.com/forms/d/e/1FAIpQLScVSnm26xUibVlI8_cvzsqqLLkdLUhWfeA2z9-p-livjUlljA/formResponse?usp=pp_url&entry.939486531=1&entry.1861198387=2&entry.367765609=3&entry.797414005=4&entry.1971304507=5&entry.36072344=6&entry.209965346=4&entry.80107347=5&entry.257529099=8"

# --- LECTURA DIRECTA INTELIGENTE ---
try:
    df_raw = pd.read_csv(URL_LECTURA_DIRECTA)
    
    if not df_raw.empty:
        # Limpiamos nombres de columnas
        df_raw.columns = [str(c).strip() for c in df_raw.columns]
        df_raw = df_raw.dropna(how="all")
        
        # Búsqueda flexible de la columna ID
        columna_id_encontrada = [c for c in df_raw.columns if c.upper().strip() == "ID"]
        
        if columna_id_encontrada:
            nombre_real_id = columna_id_encontrada[0]
            df_raw = df_raw.rename(columns={nombre_real_id: "ID"})
        else:
            df_raw["ID"] = range(1, len(df_raw) + 1)
        
        df_raw["ID"] = pd.to_numeric(df_raw["ID"], errors="coerce").fillna(0).astype(int)
        
        if "Marca temporal" in df_raw.columns:
            df_raw["Marca temporal"] = pd.to_datetime(df_raw["Marca temporal"], errors="coerce")
            df_raw = df_raw.sort_values(by="Marca temporal", ascending=True)
        
        # Filtro de duplicados (Nos quedamos con el último estado de cada ID)
        df_db = df_raw.drop_duplicates(subset=["ID"], keep="last").copy()
        id_siguiente = int(df_raw["ID"].max()) + 1 if len(df_raw) > 0 else 1
        
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
    # ⚠️ REEMPLAZA ESTOS 'entry.XXXXXX' CON LOS TUYOS DEL FORMULARIO ⚠️
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
        st.error(f"Error de red al enviar datos: {e}")
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
            
            t_fijo = df_db.at[idx, "Tipo Insumo"] if "Tipo Insumo" in df_db.columns else ""
            m_fijo = df_db.at[idx, "Medidas"] if "Medidas" in df_db.columns else ""
            e_fijo = df_db.at[idx, "Eficiencia"] if "Eficiencia" in df_db.columns else ""
            c_fijo = df_db.at[idx, "Clase"] if "Clase" in df_db.columns else ""
            eq_fijo = df_db.at[idx, "Equipo"] if "Equipo" in df_db.columns else ""
            
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
    
    # Aplicar buscador si el usuario escribe algo
    if buscar:
        mask = df_filtrado.astype(str).apply(lambda x: x.str.contains(buscar, case=False)).any(axis=1)
        df_filtrado = df_filtrado[mask]

    if not df_filtrado.empty:
        # --- NUEVA ESTRUCTURA VISUAL HORIZONTAL ---
        for index, row in df_filtrado.iterrows():
            try:
                cant_actual = float(row.get("Cant. Actual", 0))
            except:
                cant_actual = 0
            
            # Alerta visual si el stock es bajo (< 5 unidades)
            if cant_actual < 5:
                titulo_tarjeta = f"⚠️ ID {row['ID']}: {row.get('Tipo Insumo', 'N/A')} (Stock Bajo)"
            else:
                titulo_tarjeta = f"📦 ID {row['ID']}: {row.get('Tipo Insumo', 'N/A')}"
            
            # Cada ítem es un bloque horizontal colapsable
            with st.expander(titulo_tarjeta, expanded=True):
                # Creamos 7 columnas horizontales fijas para los datos
                c1, c2, c3, c4, c5, c6, c7 = st.columns([2, 2, 2, 2, 2, 3, 2])
                
                with c1:
                    st.markdown(f"**Medidas:**\n\n{row.get('Medidas', 'N/A')}")
                with c2:
                    st.markdown(f"**Eficiencia:**\n\n{row.get('Eficiencia', 'N/A')}")
                with c3:
                    st.markdown(f"**Clase:**\n\n{row.get('Clase', 'N/A')}")
                with c4:
                    st.markdown(f"**Equipo:**\n\n{row.get('Equipo', 'N/A')}")
                with c5:
                    # Si el stock es bajo lo resalta en color naranja/rojo textualmente
                    if cant_actual < 5:
                        st.markdown(f"**🟢 Cant. Actual:**\n\n🔴 **{cant_actual}**")
                    else:
                        st.markdown(f"**🟢 Cant. Actual:**\n\n{cant_actual}")
                with c6:
                    st.markdown(f"**👤 Verificado Por:**\n\n{row.get('Verificado Por', 'N/A')}")
                with c7:
                    st.markdown(f"**📝 Obs:**\n\n{row.get('Observaciones', 'N/A')}")
        
        st.write("---")
        st.write("**⚠️ Acciones de Control:**")
        
        act_col1, act_col2 = st.columns([3, 9])
        id_seleccionar = act_col1.number_input("ID del Ítem para Modificar:", min_value=1, step=1, key="id_control")
        
        if act_col2.button("✏️ Cargar Ítem en el Formulario Superior", use_container_width=True):
            if id_seleccionar in df_db["ID"].values:
                st.session_state.edit_id = id_seleccionar
                st.rerun()
            else:
                st.error("El ID seleccionado no existe en el inventario.")
    else:
        st.info("El inventario está vacío o no hay coincidencias.")

with tab_hist:
    st.dataframe(st.session_state.historial, use_container_width=True, hide_index=True)
    
