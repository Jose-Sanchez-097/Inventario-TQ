import streamlit as st
import pandas as pd
from datetime import datetime
import requests

st.set_page_config(page_title="Inventario TQ Online", layout="wide")
st.title("📦 Control de Inventario e Historial TQ")

# --- LÓGICA DE DATOS ---
@st.cache_data(ttl=60)
def cargar_datos(url):
    df = pd.read_csv(url)
    df.columns = [str(c).strip() for c in df.columns]
    return df.dropna(how="all")

# Carga inicial o desde estado
if "df_base" not in st.session_state:
    st.session_state.df_base = cargar_datos("https://docs.google.com/spreadsheets/d/1DnYaNa7rJTJZCIIs9GyOMxEeusL7SHoTJjjZwjbV_LI/export?format=csv&gid=1927911440")

# --- PROCESAMIENTO ---
def obtener_inventario_limpio():
    df = st.session_state.df_base.copy()
    # Mapeo básico de ID
    df = df.rename(columns={c: "ID" for c in df.columns if "ID" in c.upper() and len(c) < 6})
    df = df.drop_duplicates(subset=["ID"], keep="last")
    
    # Filtro estricto
    df = df[(df["Tipo Insumo"].astype(str).str.upper() != "ELIMINADO") & (df["Cant. Actual"].astype(float) >= 0)]
    return df.fillna("N/A")

# --- ACCIONES DE ESCRITURA CON ACTUALIZACIÓN INSTANTÁNEA ---
def ejecutar_accion_formulario(id_val, accion, cant_val, obs=""):
    # Enviar a Google
    url = "https://docs.google.com/forms/d/e/1FAIpQLScVSnm26xUibVlI8_cvzsqqLLkdLUhWfeA2z9-p-livjUlljA/formResponse"
    # (Asegúrate de que tus keys sean correctas)
    datos = {"entry.939486531": str(id_val), "entry.209965346": str(cant_val), "entry.257529099": obs}
    
    if requests.post(url, data=datos).status_code == 200:
        # ACTUALIZACIÓN INSTANTÁNEA EN MEMORIA
        # Esto evita esperar a que el CSV de Google se refresque
        st.session_state.df_base = st.session_state.df_base.append(
            {"ID": id_val, "Tipo Insumo": accion, "Cant. Actual": cant_val}, ignore_index=True
        )
        return True
    return False

# --- UI (Fragmento de la Zona de Eliminación) ---
with st.expander("🗑️ Zona de Eliminación"):
    id_del = st.number_input("ID a borrar", min_value=1, step=1)
    clave = st.text_input("Contraseña", type="password")
    if st.button("Confirmar Eliminación"):
        if clave == "TQ2026":
            if ejecutar_accion_formulario(id_del, "ELIMINADO", -1, "Ítem purgado"):
                st.success("Eliminado correctamente.")
                st.rerun()
        else:
            st.error("Contraseña incorrecta")

df_db = obtener_inventario_limpio()
# ... resto de tu código de visualización ...
        
        # Consolidación: tomamos el último registro de cada ID
        df_db = df_raw.drop_duplicates(subset=["ID"], keep="last").copy()

        # --- AÑADE ESTE BLOQUE DE LIMPIEZA Y FILTRADO AQUÍ ---
        # 1. Filtro estricto: Elimina filas marcadas como ELIMINADO y cantidades negativas
        df_db = df_db[
            (df_db["Tipo Insumo"].astype(str).str.upper() != "ELIMINADO") & 
            (df_db["Cant. Actual"] >= 0)
        ].copy()
        
        # 2. Reemplaza todos los valores nulos o "nan" por "N/A" para que la UI se vea limpia
        df_db = df_db.fillna("N/A")
        # -----------------------------------------------------
        
        # --- PARCHE DE SINCRONIZACIÓN ---
        if "edit_id" in st.session_state and st.session_state.edit_id is not None:
            mask = df_db["ID"] == st.session_state.edit_id
            if mask.any():
                # Nota: 'cantidad' debe estar definido, asegúrate de que el flujo sea correcto
                try:
                    df_db.loc[mask, "Cant. Actual"] = float(st.session_state.get("cantidad_temp", 0))
                except: pass

        id_siguiente = int(df_db["ID"].max()) + 1 if not df_db.empty else 1
    else:
        df_db = pd.DataFrame()
        id_siguiente = 1

except Exception as e:
    st.error(f"Error al conectar con la BD: {e}")
    st.stop()

# --- FUNCIONES RESTANTES ---
def enviar_datos_formulario(id_val, tipo_val, med_val, efic_val, clase_val, eq_val, cant_val, verif_val, obs_val):
    form_data = {
        "entry.939486531": str(id_val), "entry.1861198387": str(tipo_val),
        "entry.367765609": str(med_val), "entry.797414005": str(efic_val),
        "entry.1971304507": str(clase_val), "entry.36072344": str(eq_val),
        "entry.209965346": str(cant_val), "entry.80107347": str(verif_val),
        "entry.257529099": str(obs_val)
    }
    return requests.post(URL_FORM_RESPONSE, data=form_data).status_code == 200

# Historial en memoria de sesión
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
                    st.success("Insumo guardado de forma permanente.")
                    st.rerun()
            except ValueError:
                st.error("Por favor, introduce un número válido en Cantidad Actual.")
        else:
            st.warning("Por favor llena los campos obligatorios (Tipo, Cantidad y Verificado Por).")
else:
    # --- BOTÓN DE GUARDAR CAMBIOS (CORREGIDO) ---
    if b_col1.button("💾 Guardar Cambios", use_container_width=True):
        try:
            cant_val = float(cantidad)
            if verificado:
                idx = df_db[df_db["ID"] == st.session_state.edit_id].index[0]
                
                t_fijo = df_db.at[idx, "Tipo Insumo"] if "Tipo Insumo" in df_db.columns else ""
                m_fijo = df_db.at[idx, "Medidas"] if "Medidas" in df_db.columns else ""
                e_fijo = df_db.at[idx, "Eficiencia"] if "Eficiencia" in df_db.columns else ""
                c_fijo = df_db.at[idx, "Clase"] if "Clase" in df_db.columns else ""
                eq_fijo = df_db.at[idx, "Equipo"] if "Equipo" in df_db.columns else ""
                
                # --- AQUÍ ESTABA EL ERROR: EL IF DEBÍA ESTAR DENTRO DEL TRY ---
                if enviar_datos_formulario(st.session_state.edit_id, t_fijo, m_fijo, e_fijo, c_fijo, eq_fijo, cant_val, verificado, observaciones):
                    registrar_movimiento("MODIFICACIÓN", st.session_state.edit_id, f"Nueva Cant.: {cantidad}")
                    st.session_state.edit_id = None
                    st.toast("Cambios guardados. Sincronizando...", icon="✅")
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.warning("Debes indicar quién está verificando este cambio en 'Verificado Por'.")
        except ValueError:
            st.error("Por favor, introduce un número válido en Cantidad Actual.")
        except Exception as e:
            st.error(f"Ocurrió un error: {e}")

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

    # --- MAPEEO DE POSICIÓN VISUAL A ID REAL ---
    # Creamos un diccionario para saber qué [#] corresponde a qué ID Real
    mapa_posiciones_id = {}
    if not df_filtrado.empty:
        for i, (idx, row) in enumerate(df_filtrado.iterrows(), start=1):
            mapa_posiciones_id[i] = int(row["ID"])

    with search_col2:
        # Ahora el usuario digita el número de posición (#) que ve en la tarjeta
        pos_seleccionar = st.number_input("🆔 N° de posición (#) a modificar:", min_value=1, step=1, key="pos_control")
        
    with search_col3:
        st.write("##") 
        if st.button("✏️ Modificar Atributo", use_container_width=True):
            # Verificamos si la posición ingresada existe en la pantalla
            if pos_seleccionar in mapa_posiciones_id:
                st.session_state.edit_id = mapa_posiciones_id[pos_seleccionar]
                st.rerun()
            else:
                st.error("El número de posición seleccionado no aparece en la lista actual.")

    # --- RENDERIZADO DE TARJETAS EXPANSIBLES CON NUMERACIÓN VIRTUAL ---
    if not df_filtrado.empty:
        posicion_visual = 1
        
        for index, row in df_filtrado.iterrows():
            try:
                cant_actual = float(row.get("Cant. Actual", 0))
            except:
                cant_actual = 0
            
            # Título impecable: Solo la posición (#) limpia y el Insumo
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
                    # Guardamos el ID Real de la Base de Datos de manera discreta en la tarjeta para tu control técnico
                    st.markdown(f"**📝 Obs (ID: {row['ID']}):**\n\n{row.get('Observaciones', 'N/A')}")
            
            posicion_visual += 1
        # --- SECCIÓN DE ELIMINACIÓN REAL ---
        st.write("---")
        st.subheader("🗑️ Zona de Eliminación de Insumos")
        del_col1, del_col2, del_col3 = st.columns([2, 3, 3])
        
        with del_col1:
            id_a_borrar = st.number_input("ID de la base de datos a Borrar:", min_value=1, step=1, key="id_borrar")
        with del_col2:
            clave_input = st.text_input("🔑 Contraseña de Autorización:", type="password", key="clave_borrar")
        with del_col3:
            st.write("##")
            # --- EN TU ZONA DE ELIMINACIÓN ---
if st.button("🔥 Confirmar Eliminación", use_container_width=True):
    if clave_input == CONTRASENA_CORRECTA:
        # CAMBIO CLAVE: Usamos 'df_raw' en lugar de 'df_db' para verificar la existencia,
        # porque df_raw tiene todos los datos, incluidos los "ELIMINADO"
        if id_a_borrar in df_raw["ID"].values:
            if enviar_datos_formulario(id_a_borrar, "ELIMINADO", "N/A", "N/A", "N/A", "N/A", -1, "SISTEMA", "Ítem purgado"):
                registrar_movimiento("ELIMINACIÓN", id_a_borrar, "Insumo eliminado")
                st.success(f"El ítem con ID {id_a_borrar} fue eliminado.")
                st.cache_data.clear() # Limpiamos caché para que el cambio se refleje
                st.rerun()
        else:
            st.error("El ID seleccionado no existe en la base de datos.")
                
    else:
        st.info("El inventario está vacío o no hay coincidencias con la búsqueda.")

with tab_hist:
    st.dataframe(st.session_state.historial, use_container_width=True, hide_index=True)
