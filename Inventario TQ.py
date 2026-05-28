import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# Configuración de la página web
st.set_page_config(page_title="Inventario TQ Online", layout="wide")
st.title("📦 Control de Inventario e Historial TQ")

# --- CONFIGURACIÓN DE SEGURIDAD ---
CONTRASENA_CORRECTA = "TQ2026"

# 1. Enlace de lectura directo en formato CSV
URL_LECTURA_DIRECTA = "https://docs.google.com/spreadsheets/d/1DnYaNa7rJTJZCIIs9GyOMxEeusL7SHoTJjjZwjbV_LI/export?format=csv&gid=1927911440"

# 2. Enlace de respuesta del formulario (limpio para peticiones POST)
URL_FORM_RESPONSE = "https://docs.google.com/forms/e/1FAIpQLScVSnm26xUibVlI8_cvzsqqLLkdLUhWfeA2z9-p-livjUlljA/formResponse"

# --- LECTURA DIRECTA INTEGRAL MAPEADA ---
try:
    df_raw = pd.read_csv(URL_LECTURA_DIRECTA)
    
    if not df_raw.empty:
        # Limpiamos espacios en blanco de los encabezados
        df_raw.columns = [str(c).strip() for c in df_raw.columns]
        df_raw = df_raw.dropna(how="all")
        
        mapa_columnas = {}
        for c in df_raw.columns:
            c_upper = c.upper()
            if c_upper == "ID" or ("ID" in c_upper and len(c) < 6):
                mapa_columnas[c] = "ID"
            elif "TIPO" in c_upper or "INSUMO" in c_upper:
                mapa_columnas[c] = "Tipo Insumo"
            elif "MEDIDA" in c_upper:
                mapa_columnas[c] = "Medidas"
            elif "EFIC" in c_upper:
                mapa_columnas[c] = "Eficiencia"
            elif "CLASE" in c_upper:
                mapa_columnas[c] = "Clase"
            elif "EQUIPO" in c_upper:
                mapa_columnas[c] = "Equipo"
            elif "CANT" in c_upper:
                mapa_columnas[c] = "Cant. Actual"
            elif "VERIF" in c_upper or "QUIEN" in c_upper or "PERSONA" in c_upper:
                mapa_columnas[c] = "Verificado Por"
            elif "OBS" in c_upper or "COMENT" in c_upper:
                mapa_columnas[c] = "Observaciones"
            elif "MARCA" in c_upper or "TIEMPO" in c_upper or "TIMESTAMP" in c_upper:
                mapa_columnas[c] = "Marca temporal"
        
        df_raw = df_raw.rename(columns={k: v for k, v in mapa_columnas.items() if v not in df_raw.columns or k == v})
        
        columnas_obligatorias = ["ID", "Tipo Insumo", "Cant. Actual", "Marca temporal"]
        for col in columnas_obligatorias:
            if col not in df_raw.columns:
                if col == "ID":
                    df_raw["ID"] = range(1, len(df_raw) + 1)
                elif col == "Cant. Actual":
                    df_raw["Cant. Actual"] = 0
                else:
                    df_raw[col] = ""

        df_raw["ID"] = pd.to_numeric(df_raw["ID"], errors="coerce").fillna(0).astype(int)
        df_raw["Cant. Actual"] = pd.to_numeric(df_raw["Cant. Actual"], errors="coerce").fillna(0)
        df_raw["Tipo Insumo"] = df_raw["Tipo Insumo"].astype(str).str.strip()
        
        if "Marca temporal" in df_raw.columns and df_raw["Marca temporal"].notna().any():
            df_raw["Marca temporal"] = pd.to_datetime(df_raw["Marca temporal"], errors="coerce")
            df_raw = df_raw.sort_values(by="Marca temporal", ascending=True)
        
        df_db = df_raw.drop_duplicates(subset=["ID"], keep="last").copy()
        
        if not df_db.empty:
            df_db = df_db[df_db["Tipo Insumo"] != "ELIMINADO"]
            df_db = df_db[df_db["Cant. Actual"] >= 0]
        
        if not df_db.empty and "Tipo Insumo" in df_db.columns:
            df_db = df_db.sort_values(by="Tipo Insumo", key=lambda col: col.astype(str).str.lower(), ascending=True)
            
        id_siguiente = int(df_raw["ID"].max()) + 1 if len(df_raw) > 0 else 1
    else:
        df_db = pd.DataFrame(columns=["ID", "Tipo Insumo", "Medidas", "Eficiencia", "Clase", "Equipo", "Cant. Actual", "Verificado Por", "Observaciones"])
        id_siguiente = 1

except Exception as e:
    st.error(f"Error crítico al conectar con la Base de Datos. Detalles: {e}")
    st.stop()

# --- FUNCIÓN DE ESCRITURA ---
def enviar_datos_formulario(id_val, tipo_val, med_val, efic_val, clase_val, eq_val, cant_val, verif_val, obs_val):
    form_data = {
        "entry.939486531": str(id_val),       
        "entry.1861198387": str(tipo_val),     
        "entry.367765609": str(med_val),      
        "entry.797414005": str(efic_val),     
        "entry.1971304507": str(clase_val),    
        "entry.36072344": str(eq_val),       
        "entry.209965346": str(cant_val),     
        "entry.80107347": str(verif_val),    
        "entry.257529099": str(obs_val)       
    }
    try:
        respuesta = requests.post(URL_FORM_RESPONSE, data=form_data)
        return True
    except Exception as e:
        st.error(f"Error de red al enviar datos: {e}")
        return False

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

# --- CONFIGURACIÓN DE ESTADOS DE SESIÓN PARA EDICIÓN SEGURA ---
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None
if "edit_datos" not in st.session_state:
    st.session_state.edit_datos = {}

# --- FORMULARIO DE ENTRADA EN INTERFAZ ---
st.subheader("📝 Gestión de Ítems")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.session_state.edit_id is not None:
        tipo = st.text_input("Tipo de Insumo", value=st.session_state.edit_datos.get("Tipo Insumo", ""), disabled=True)
        clase = st.text_input("Clase", value=st.session_state.edit_datos.get("Clase", ""), disabled=True)
    else:
        tipo = st.text_input("Tipo de Insumo")
        clase = st.text_input("Clase")
with col2:
    if st.session_state.edit_id is not None:
        medidas = st.text_input("Medidas", value=st.session_state.edit_datos.get("Medidas", ""), disabled=True)
        equipo = st.text_input("Equipo", value=st.session_state.edit_datos.get("Equipo", ""), disabled=True)
    else:
        medidas = st.text_input("Medidas")
        equipo = st.text_input("Equipo")
with col3:
    if st.session_state.edit_id is not None:
        eficiencia = st.text_input("Eficiencia", value=st.session_state.edit_datos.get("Eficiencia", ""), disabled=True)
        cantidad = st.text_input("Cantidad Actual", value=str(st.session_state.edit_datos.get("Cant. Actual", "")))
    else:
        eficiencia = st.text_input("Eficiencia")
        cantidad = st.text_input("Cantidad Actual")
with col4:
    if st.session_state.edit_id is not None:
        verificado = st.text_input("Verificado Por", value=str(st.session_state.edit_datos.get("Verificado Por", "")))
        observaciones = st.text_input("Observaciones", value=str(st.session_state.edit_datos.get("Observaciones", "")))
    else:
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
                    st.success("Insumo guardado de forma permanente.")
                    st.rerun()
            except ValueError:
                st.error("Por favor, introduce un número válido en Cantidad Actual.")
        else:
            st.warning("Por favor llena los campos obligatorios (Tipo, Cantidad y Verificado Por).")
else:
    if b_col1.button("💾 Guardar Cambios", use_container_width=True):
        try:
            cant_val = float(cantidad)
            if verificado:
                # Recuperamos los valores de texto estáticos guardados de forma segura en la sesión
                t_fijo = st.session_state.edit_datos.get("Tipo Insumo", "")
                m_fijo = st.session_state.edit_datos.get("Medidas", "")
                e_fijo = st.session_state.edit_datos.get("Eficiencia", "")
                c_fijo = st.session_state.edit_datos.get("Clase", "")
                eq_fijo = st.session_state.edit_datos.get("Equipo", "")
                
                if enviar_datos_formulario(st.session_state.edit_id, t_fijo, m_fijo, e_fijo, c_fijo, eq_fijo, cant_val, verificado, observaciones):
                    registrar_movimiento("MODIFICACIÓN", st.session_state.edit_id, f"Nueva Cant.: {cantidad} | Obs: {observaciones}")
                    st.session_state.edit_id = None
                    st.session_state.edit_datos = {}
                    st.success("Cambios sincronizados exitosamente.")
                    st.rerun()
            else:
                st.warning("Debes indicar quién está verificando este cambio en 'Verificado Por'.")
        except ValueError:
            st.error("Por favor, introduce un número válido en Cantidad Actual.")
            
    if b_col2.button("❌ Cancelar Edición", use_container_width=True):
        st.session_state.edit_id = None
        st.session_state.edit_datos = {}
        st.rerun()

st.markdown("---")

# --- PESTAÑAS DE VISTA DE DATOS ---
tab_inv, tab_hist = st.tabs(["📋 Inventario Actual", "📜 Historial de Movimientos"])

with tab_inv:
    search_col1, search_col2, search_col3 = st.columns([5, 3, 4])
    
    with search_col1:
        buscar = st.text_input("🔍 Buscar ítem en el inventario...")
        
    df_filtrado = df_db.copy()
    if buscar:
        mask = df_filtrado.astype(str).apply(lambda x: x.str.contains(buscar, case=False)).any(axis=1)
        df_filtrado = df_filtrado[mask]

    # --- MAPEO CRÍTICO DE POSICIONES A DATOS COMPLETOS DE SESIÓN ---
    mapa_posiciones_datos = {}
    if not df_filtrado.empty:
        for i, (idx, row) in enumerate(df_filtrado.iterrows(), start=1):
            mapa_posiciones_datos[i] = row.to_dict()

    with search_col2:
        pos_seleccionar = st.number_input("🆔 N° de posición (#) a modificar:", min_value=1, step=1, key="pos_control")
        
    with search_col3:
        st.write("##") 
        if st.button("✏️ Modificar Atributo", use_container_width=True):
            if pos_seleccionar in mapa_posiciones_datos:
                # Almacenamos el ID y la fila completa en memoria estática de forma blindada
                datos_item = mapa_posiciones_datos[pos_seleccionar]
                st.session_state.edit_id = int(datos_item["ID"])
                st.session_state.edit_datos = datos_item
                st.rerun()
            else:
                st.error("El número de posición seleccionado no aparece en la lista actual.")

    # --- RENDERIZADO DE TARJETAS EXPANSIBLES ---
    if not df_filtrado.empty:
        posicion_visual = 1
        
        for index, row in df_filtrado.iterrows():
            try:
                cant_actual = float(row.get("Cant. Actual", 0))
            except:
                cant_actual = 0
            
            if cant_actual < 5:
                titulo_tarjeta = f"⚠️ [#{posicion_visual}] {row.get('Tipo Insumo', 'N/A')} (Stock Crítico)"
            else:
                titulo_tarjeta = f"📦 [#{posicion_visual}] {row.get('Tipo Insumo', 'N/A')}"
            
            with st.expander(titulo_tarjeta, expanded=True):
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
                    if cant_actual < 5:
                        st.markdown(f"**🟢 Cant. Actual:**\n\n🔴 **{cant_actual}**")
                    else:
                        st.markdown(f"**🟢 Cant. Actual:**\n\n{cant_actual}")
                with c6:
                    st.markdown(f"**👤 Verificado Por:**\n\n{row.get('Verificado Por', 'N/A')}")
                with c7:
                    st.markdown(f"**📝 Obs:**\n\n{row.get('Observaciones', 'N/A')}\n\n")
            
            posicion_visual += 1

        # --- SECCIÓN DE ELIMINACIÓN POR POSICIÓN (#) ---
        st.write("---")
        st.subheader("🗑️ Zona de Eliminación de Insumos")
        del_col1, del_col2, del_col3 = st.columns([2, 3, 3])
        
        with del_col1:
            pos_a_borrar = st.number_input("N° de posición (#) del Ítem a Borrar:", min_value=1, step=1, key="pos_borrar")
        with del_col2:
            clave_input = st.text_input("🔑 Contraseña de Autorización:", type="password", key="clave_borrar")
        with del_col3:
            st.write("##")
            if st.button("🔥 Confirmar Eliminación", use_container_width=True):
                if clave_input == CONTRASENA_CORRECTA:
                    if pos_a_borrar in mapa_posiciones_datos:
                        id_real_borrar = int(mapa_posiciones_datos[pos_a_borrar]["ID"])
                        if enviar_datos_formulario(id_real_borrar, "ELIMINADO", "N/A", "N/A", "N/A", "N/A", -1, "SISTEMA", "Ítem purgado con contraseña"):
                            registrar_movimiento("ELIMINACIÓN", id_real_borrar, "Insumo eliminado usando contraseña TQ2026")
                            st.success(f"El ítem en la posición #{pos_a_borrar} fue eliminado con éxito.")
                            st.rerun()
                    else:
                        st.error("El número de posición seleccionado no aparece en la lista actual.")
                else:
                    st.error("Contraseña incorrecta. Acción denegada.")
    else:
        st.info("El inventario está vacío o no hay coincidencias con la búsqueda.")

with tab_hist:
    st.dataframe(st.session_state.historial, use_container_width=True, hide_index=True)
