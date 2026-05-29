import streamlit as st
import pandas as pd
import datetime
import os
import uuid

# --- CONFIGURACIÓN DE LA APP ---
st.set_page_config(page_title="Gestión de Inventarios", page_icon="📦", layout="wide")

# --- FUNCIONES DE BASE DE DATOS ---
FILE_INVENTARIO = "inventario.csv"
FILE_HISTORIAL = "historial.csv"

def cargar_datos():
    if not os.path.exists(FILE_INVENTARIO):
        df = pd.DataFrame(columns=[
            "ID", "Tipo de Insumo", "Medidas", "Eficiencia", "Modelo", 
            "Equipo", "Cantidad Actual", "Realizado Por", "Observaciones", "Última Actualización"
        ])
        df.to_csv(FILE_INVENTARIO, index=False)
    return pd.read_csv(FILE_INVENTARIO)

def guardar_datos(df):
    df.to_csv(FILE_INVENTARIO, index=False)

def cargar_historial():
    if not os.path.exists(FILE_HISTORIAL):
        df = pd.DataFrame(columns=["ID_Mov", "ID_Insumo", "Tipo Movimiento", "Fecha", "Usuario"])
        df.to_csv(FILE_HISTORIAL, index=False)
    return pd.read_csv(FILE_HISTORIAL)

def guardar_historial(df_hist):
    df_hist.to_csv(FILE_HISTORIAL, index=False)

def registrar_movimiento(id_insumo, tipo_mov, usuario):
    df_hist = cargar_historial()
    nuevo_mov = pd.DataFrame({
        "ID_Mov": [str(uuid.uuid4())[:8]],
        "ID_Insumo": [id_insumo],
        "Tipo Movimiento": [tipo_mov],
        "Fecha": [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "Usuario": [usuario]
    })
    df_hist = pd.concat([df_hist, nuevo_mov], ignore_index=True)
    guardar_historial(df_hist)

# --- ESTILOS CSS PARA MÓVIL Y FLUIDEZ ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; }
    .css-1d391kg { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

# --- TÍTULO E HISTORIAL ---
st.title("🖥️ Plataforma de Gestión de Insumos")
st.markdown("---")

# --- LOGICA PRINCIPAL ---
df_inventario = cargar_datos()

# 1. BARRA LATERAL Y BUSQUEDA
st.sidebar.header("🔍 Buscar Insumo")
termino_busqueda = st.sidebar.text_input("Ingrese ID, Modelo o Equipo")

menu = st.sidebar.radio("Menú", ["📊 Dashboard", "➕ Agregar Insumo", "✏️ Modificar Insumo", "🗑️ Eliminar Insumo", "📜 Historial Movimientos"])

# Filtrar datos para búsqueda o visualización
df_mostrar = df_inventario.copy()
if termino_busqueda:
    df_mostrar = df_inventario[
        df_inventario.apply(lambda row: termino_busqueda.lower() in row.astype(str).str.lower().values, axis=1)
    ]
    st.sidebar.success(f"Encontrados: {len(df_mostrar)}")


# --- VISTA: DASHBOARD (ALERTAS) ---
if menu == "📊 Dashboard":
    st.header("Panel de Control")
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Insumos", len(df_inventario))
    col2.metric("Unidades Totales", df_inventario["Cantidad Actual"].sum() if not df_inventario.empty else 0)
    
    # Alertas de stock bajo
    alerta_df = df_inventario[df_inventario["Cantidad Actual"] < 5]
    if not alerta_df.empty:
        col3.error(f"⚠️ Stock Bajo: {len(alerta_df)} items")
        st.subheader("⚠️ ALERTA: Insumos con Cantidad < 5")
        st.dataframe(alerta_df[["ID", "Tipo de Insumo", "Modelo", "Cantidad Actual"]].style.background_color('#ffcccc', axis=0), use_container_width=True)
    else:
        col3.success("✅ Stock Óptimo")

    st.subheader("Inventario Completo")
    st.dataframe(df_mostrar, use_container_width=True)


# --- VISTA: AGREGAR INSUMO ---
elif menu == "➕ Agregar Insumo":
    st.header("Agregar Nuevo Insumo")
    with st.form("form_agregar"):
        tipo = st.text_input("Tipo de Insumo")
        medidas = st.text_input("Medidas")
        eff = st.selectbox("Eficiencia", ["Nueva", "Usada", "En Reparación"])
        modelo = st.text_input("Modelo")
        equipo = st.text_input("Equipo")
        cant = st.number_input("Cantidad Actual", min_value=0, step=1)
        user = st.text_input("Realizado Por")
        obs = st.text_area("Observaciones")
        
        submit = st.form_submit_button("Guardar Insumo")
        
        if submit:
            if tipo and modelo:
                nuevo_id = str(uuid.uuid4())[:8]
                nueva_fila = pd.DataFrame({
                    "ID": [nuevo_id],
                    "Tipo de Insumo": [tipo],
                    "Medidas": [medidas],
                    "Eficiencia": [eff],
                    "Modelo": [modelo],
                    "Equipo": [equipo],
                    "Cantidad Actual": [cant],
                    "Realizado Por": [user],
                    "Observaciones": [obs],
                    "Última Actualización": [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                })
                df_inventario = pd.concat([df_inventario, nueva_fila], ignore_index=True)
                guardar_datos(df_inventario)
                registrar_movimiento(nuevo_id, "ALTA", user)
                st.success("Insumo guardado correctamente.")
            else:
                st.error("Los campos Tipo y Modelo son obligatorios.")


# --- VISTA: MODIFICAR INSUMO ---
elif menu == "✏️ Modificar Insumo":
    st.header("Modificar Insumo Existente")
    ids_disponibles = df_inventario["ID"].tolist()
    if not ids_disponibles:
        st.warning("No hay insumos.")
    else:
        id_selec = st.selectbox("Seleccionar ID a modificar", ids_disponibles)
        insumo = df_inventario[df_inventario["ID"] == id_selec].iloc[0]
        
        with st.form("form_modificar"):
            tipo = st.text_input("Tipo de Insumo", value=insumo["Tipo de Insumo"])
            medidas = st.text_input("Medidas", value=insumo["Medidas"])
            eff = st.selectbox("Eficiencia", ["Nueva", "Usada", "En Reparación"], index=["Nueva", "Usada", "En Reparación"].index(insumo["Eficiencia"]))
            modelo = st.text_input("Modelo", value=insumo["Modelo"])
            equipo = st.text_input("Equipo", value=insumo["Equipo"])
            cant = st.number_input("Cantidad Actual", min_value=0, value=int(insumo["Cantidad Actual"]))
            user = st.text_input("Realizado Por", value=insumo["Realizado Por"])
            obs = st.text_area("Observaciones", value=insumo["Observaciones"])
            
            submit = st.form_submit_button("Actualizar Datos")
            
            if submit:
                df_inventario.loc[df_inventario["ID"] == id_selec, 
                    ["Tipo de Insumo", "Medidas", "Eficiencia", "Modelo", "Equipo", 
                     "Cantidad Actual", "Realizado Por", "Observaciones", "Última Actualización"]] = [
                    tipo, medidas, eff, modelo, equipo, cant, user, obs, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ]
                guardar_datos(df_inventario)
                registrar_movimiento(id_selec, "MODIFICACIÓN", user)
                st.success(f"Insumo {id_selec} actualizado.")
                st.rerun()


# --- VISTA: ELIMINAR INSUMO ---
elif menu == "🗑️ Eliminar Insumo":
    st.header("Eliminar Insumo")
    st.warning("Para eliminar un insumo debe verificar su identidad y contraseña.")
    
    ids_disponibles = df_inventario["ID"].tolist()
    if ids_disponibles:
        id_del = st.selectbox("Seleccionar ID a eliminar", ids_disponibles)
        password_input = st.text_input("Contraseña de Seguridad (TQ2026)", type="password")
        
        if st.button("Confirmar Eliminación"):
            if password_input == "TQ2026":
                # Guardar historial antes de borrar
                registrar_movimiento(id_del, "BAJA (ELIMINACIÓN)", "Admin")
                df_inventario = df_inventario[df_inventario["ID"] != id_del]
                guardar_datos(df_inventario)
                st.success(f"Insumo {id_del} eliminado del sistema.")
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
    else:
        st.info("No hay insumos para eliminar.")


# --- VISTA: HISTORIAL ---
elif menu == "📜 Historial Movimientos":
    st.header("Historial Completo")
    df_hist = cargar_historial()
    
    # Filtrar búsqueda en historial
    search_hist = st.text_input("Buscar en Historial")
    if search_hist:
        df_hist = df_hist[df_hist.apply(lambda row: search_hist.lower() in row.astype(str).str.lower().values, axis=1)]
        
    st.dataframe(df_hist.sort_values(by="Fecha", ascending=False), use_container_width=True)
    
