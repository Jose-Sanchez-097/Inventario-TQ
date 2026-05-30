import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time

# Configuración de la Página
st.set_page_config(page_title="Gestion de Inventarios TQ", page_icon="📦", layout="wide", initial_sidebar_state="expanded")

DB_FILE = 'inventario.db'

# --- FUNCIONES DE BASE DE DATOS ---
def init_db():
    """Inicializa las tablas si no existen."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Tabla Inventario
    c.execute('''CREATE TABLE IF NOT EXISTS inventario (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        tipo_insumo TEXT NOT NULL, 
        medidas TEXT, 
        eficiencia TEXT, 
        modelo TEXT, 
        equipo TEXT, 
        cantidad INTEGER DEFAULT 0, 
        realizado_por TEXT, 
        observaciones TEXT, 
        ubicacion TEXT,
        fecha_actualizacion TEXT)''')
    
    # Tabla Sistema
    c.execute('''CREATE TABLE IF NOT EXISTS sistema (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        nombre TEXT NOT NULL, 
        tipo_filtro TEXT, 
        modelo TEXT, 
        eficiencia TEXT, 
        medidas TEXT, 
        cantidad INTEGER DEFAULT 0, 
        ubicacion TEXT,
        observaciones TEXT,
        fecha_actualizacion TEXT)''')
    
    # Tabla Historial
    c.execute('''CREATE TABLE IF NOT EXISTS historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        fecha TEXT, 
        accion TEXT, 
        descripcion TEXT, 
        usuario TEXT)''')
    
    # Verificar y agregar columnas si no existen (para actualizaciones de la DB)
    try:
        c.execute("ALTER TABLE inventario ADD COLUMN ubicacion TEXT")
    except:
        pass
    
    try:
        c.execute("ALTER TABLE sistema ADD COLUMN ubicacion TEXT")
    except:
        pass
    
    try:
        c.execute("ALTER TABLE sistema ADD COLUMN observaciones TEXT")
    except:
        pass
    
    conn.commit()
    conn.close()

def run_query(query, params=()):
    """Ejecuta consultas SELECT y retorna un DataFrame."""
    conn = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        st.error(f"Error en consulta: {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

def execute_query(query, params=()):
    """Ejecuta consultas INSERT, UPDATE, DELETE."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute(query, params)
        conn.commit()
    except Exception as e:
        st.error(f"Error en operación: {e}")
    finally:
        conn.close()

def get_inventario():
    return run_query("SELECT * FROM inventario")

def get_sistema():
    return run_query("SELECT * FROM sistema")

def add_to_historial(accion, descripcion, usuario):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execute_query("INSERT INTO historial (fecha, accion, descripcion, usuario) VALUES (?, ?, ?, ?)", 
                  (fecha, accion, descripcion, usuario))

def mostrar_mensaje_exito(mensaje):
    success_placeholder = st.empty()
    success_placeholder.success(mensaje)
    time.sleep(5)
    success_placeholder.empty()

# --- INICIO DE LA APP ---
init_db()

st.title("📦 Plataforma de Gestion de Inventarios TQ")

# Menú Sidebar
menu = st.sidebar.selectbox("Menu Principal", [
    "🏠 Inicio", "➕ Agregar Insumo", "✏️ Modificar Insumo", 
    "🗑️ Eliminar Insumo", "🔍 Buscar Inventario", 
    "➕ Agregar Sistema", "✏️ Modificar Sistema", "🔍 Buscar Sistema", "📜 Historial"
])

# --- VISTAS ---

if menu == "🏠 Inicio":
    st.header("Panel de Control en Tiempo Real")
    
    df = get_inventario()
    df_sis = get_sistema()
    
    col1, col2 = st.columns(2)
    col1.metric("Total Insumos", len(df))
    col2.metric("Total Sistemas", len(df_sis))
    
    st.markdown("---")
    
    # Alertas de Stock Bajo
    st.subheader("⚠️ Alerta: Stock Bajo (< 5 unidades)")
    if not df.empty:
        low_stock = df[df['cantidad'] < 5]
        if not low_stock.empty:
            st.error(f"¡Tienes {len(low_stock)} insumos con stock crítico!")
            st.dataframe(low_stock.set_index('id'), use_container_width=True)
        else:
            st.success("✅ Inventario en niveles óptimos.")
            
    if not df_sis.empty:
        low_stock_sis = df_sis[df_sis['cantidad'] < 5]
        if not low_stock_sis.empty:
            st.warning(f"¡Tienes {len(low_stock_sis)} sistemas con stock crítico!")

    # Vista General
    st.subheader("📋 Vista General del Inventario")
    tab1, tab2 = st.tabs(["Insumos", "Sistemas"])
    with tab1:
        st.dataframe(df.set_index('id'), use_container_width=True)
    with tab2:
        st.dataframe(df_sis.set_index('id'), use_container_width=True)


elif menu == "➕ Agregar Insumo":
    st.header("Agregar Nuevo Insumo")
    with st.form("form_agregar"):
        c1, c2 = st.columns(2)
        tipo = c1.text_input("Tipo de Insumo *")
        modelo = c1.text_input("Modelo")
        medidas = c2.text_input("Medidas")
        eficiencia = c2.text_input("Eficiencia")
        
        c3, c4 = st.columns(2)
        equipo = c3.text_input("Equipo")
        cantidad = c4.number_input("Cantidad Actual *", min_value=0, step=1)
        
        c5, c6 = st.columns(2)
        ubicacion = c5.text_input("Ubicación")
        realizado_por = c6.text_input("Realizado por")
        
        observaciones = st.text_area("Observaciones")
        
        submit = st.form_submit_button("💾 Guardar Insumo")
        
        if submit:
            if not tipo:
                st.warning("Por favor complete los campos obligatorios (*).")
            else:
                try:
                    fecha_actual = datetime.now().strftime("%Y-%m-%d")
                    query = """INSERT INTO inventario 
                              (tipo_insumo, medidas, eficiencia, modelo, equipo, cantidad, realizado_por, observaciones, ubicacion, fecha_actualizacion) 
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                    params = (tipo, medidas, eficiencia, modelo, equipo, cantidad, realizado_por, observaciones, ubicacion, fecha_actual)
                    
                    execute_query(query, params)
                    
                    desc_historial = f"Insumo: {tipo} | Cantidad: {cantidad} | Modelo: {modelo} | Ubicación: {ubicacion}"
                    add_to_historial("AGREGAR INSUMO", desc_historial, realizado_por if realizado_por else "Usuario")
                    
                    st.success("✅ Insumo agregado exitosamente!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")


elif menu == "✏️ Modificar Insumo":
    st.header("Modificar Insumo Existente")
    df = get_inventario()
    
    if df.empty:
        st.info("No hay insumos para modificar.")
    else:
        opciones = df.apply(lambda x: f"{x['id']} - {x['tipo_insumo']} ({x['modelo']})", axis=1).tolist()
        seleccion = st.selectbox("Seleccione Insumo a Modificar", opciones)
        
        if seleccion:
            item_id = int(seleccion.split(" - ")[0])
            item = df[df['id'] == item_id].iloc[0]
            
            with st.form("form_modificar"):
                c1, c2 = st.columns(2)
                tipo = c1.text_input("Tipo de Insumo", value=item['tipo_insumo'])
                modelo = c1.text_input("Modelo", value=item['modelo'])
                medidas = c2.text_input("Medidas", value=item['medidas'])
                eficiencia = c2.text_input("Eficiencia", value=item['eficiencia'])
                
                c3, c4 = st.columns(2)
                equipo = c3.text_input("Equipo", value=item['equipo'])
                cantidad = c4.number_input("Cantidad Actual", min_value=0, value=int(item['cantidad']))
                
                c5, c6 = st.columns(2)
                ubicacion = c5.text_input("Ubicación", value=item.get('ubicacion', ''))
                observaciones = st.text_area("Observaciones", value=item['observaciones'])
                
                submit = st.form_submit_button("✏️ Actualizar")
                
                if submit:
                    fecha_actual = datetime.now().strftime("%Y-%m-%d")
                    query = """UPDATE inventario SET 
                               tipo_insumo=?, medidas=?, eficiencia=?, modelo=?, equipo=?, cantidad=?, observaciones=?, ubicacion=?, fecha_actualizacion=? 
                               WHERE id=?"""
                    params = (tipo, medidas, eficiencia, modelo, equipo, cantidad, observaciones, ubicacion, fecha_actual, item_id)
                    
                    execute_query(query, params)
                    add_to_historial("MODIFICAR INSUMO", f"ID: {item_id} | Nuevo: {tipo} | Ubicación: {ubicacion}", "Usuario")
                    
                    st.success("✅ Insumo actualizado exitosamente!")
                    st.rerun()


elif menu == "🗑️ Eliminar Insumo":
    st.header("Eliminar Insumo")
    df = get_inventario()
    
    if df.empty:
        st.info("Inventario vacío.")
    else:
        opciones = df.apply(lambda x: f"{x['id']} - {x['tipo_insumo']}", axis=1).tolist()
        seleccion = st.selectbox("Seleccione Insumo a Eliminar", opciones)
        
        passwd = st.text_input("Ingrese Contraseña para Confirmar Eliminación", type="password")
        
        if st.button("🗑️ Eliminar Definitivamente"):
            if passwd == "TQ2026":
                item_id = int(seleccion.split(" - ")[0])
                nombre_insumo = df[df['id'] == item_id]['tipo_insumo'].values[0]
                
                execute_query("DELETE FROM inventario WHERE id=?", (item_id,))
                
                add_to_historial("ELIMINAR INSUMO", f"Insumo: {nombre_insumo} | ID: {item_id}", "Admin")
                
                st.success("✅ Insumo eliminado exitosamente!")
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta.")


elif menu == "🔍 Buscar Inventario":
    st.header("🔍 Buscar Insumo en Inventario")
    df = get_inventario()
    
    if df.empty:
        st.info("No hay insumos registrados.")
    else:
        campo_busqueda = st.selectbox("Seleccione campo de búsqueda:", 
            ["tipo_insumo", "modelo", "equipo", "medidas", "eficiencia", "realizado_por", "ubicacion"])
        texto_busqueda = st.text_input("Buscar:", placeholder="Ingrese texto a buscar...")
        
        if texto_busqueda:
            resultado = df[df[campo_busqueda].str.contains(texto_busqueda, case=False, na=False)]
            if not resultado.empty:
                st.success(f"✅ Se encontraron {len(resultado)} resultado(s)")
                add_to_historial("BUSCAR INSUMO", f"Busqueda: {texto_busqueda} | Campo: {campo_busqueda} | Resultados: {len(resultado)}", "Usuario")
                st.dataframe(resultado.set_index('id'), use_container_width=True)
            else:
                st.warning(f"⚠️ No se encontraron resultados")
        else:
            st.dataframe(df.set_index('id'), use_container_width=True)


elif menu == "➕ Agregar Sistema":
    st.header("Agregar Nuevo Sistema")
    with st.form("form_sistema_agregar"):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre del Sistema *")
        tipo_filtro = c1.text_input("Tipo de Filtro")
        modelo = c2.text_input("Modelo")
        eficiencia = c2.text_input("Eficiencia")
        
        c3, c4 = st.columns(2)
        medidas = c3.text_input("Medidas")
        cantidad = c4.number_input("Cantidad *", min_value=0, step=1)
        
        c5, c6 = st.columns(2)
        ubicacion = c5.text_input("Ubicación")
        
        observaciones = st.text_area("Observaciones")
        
        submit = st.form_submit_button("💾 Guardar Sistema")
        
        if submit:
            if not nombre:
                st.warning("Complete los campos obligatorios (*).")
            else:
                try:
                    fecha_actual = datetime.now().strftime("%Y-%m-%d")
                    query = """INSERT INTO sistema 
                              (nombre, tipo_filtro, modelo, eficiencia, medidas, cantidad, ubicacion, observaciones, fecha_actualizacion) 
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                    params = (nombre, tipo_filtro, modelo, eficiencia, medidas, cantidad, ubicacion, observaciones, fecha_actual)
                    
                    execute_query(query, params)
                    
                    desc_historial = f"Sistema: {nombre} | Cantidad: {cantidad} | Ubicación: {ubicacion}"
                    add_to_historial("AGREGAR SISTEMA", desc_historial, "Usuario")
                    
                    st.success("✅ Sistema agregado exitosamente!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")


elif menu == "✏️ Modificar Sistema":
    st.header("Modificar Sistema Existente")
    df_sis = get_sistema()
    
    if df_sis.empty:
        st.info("No hay sistemas para modificar.")
    else:
        opciones = df_sis.apply(lambda x: f"{x['id']} - {x['nombre']} ({x['modelo']})", axis=1).tolist()
        seleccion = st.selectbox("Seleccione Sistema a Modificar", opciones)
        
        if seleccion:
            item_id = int(seleccion.split(" - ")[0])
            item = df_sis[df_sis['id'] == item_id].iloc[0]
            
            with st.form("form_sistema_modificar"):
                c1, c2 = st.columns(2)
                nombre = c1.text_input("Nombre del Sistema", value=item['nombre'])
                tipo_filtro = c1.text_input("Tipo de Filtro", value=item['tipo_filtro'])
                modelo = c2.text_input("Modelo", value=item['modelo'])
                eficiencia = c2.text_input("Eficiencia", value=item['eficiencia'])
                
                c3, c4 = st.columns(2)
                medidas = c3.text_input("Medidas", value=item['medidas'])
                cantidad = c4.number_input("Cantidad", min_value=0, value=int(item['cantidad']))
                
                c5, c6 = st.columns(2)
                ubicacion = c5.text_input("Ubicación", value=item.get('ubicacion', ''))
                
                observaciones = st.text_area("Observaciones", value=item.get('observaciones', ''))
                
                submit = st.form_submit_button("✏️ Actualizar Sistema")
                
                if submit:
                    fecha_actual = datetime.now().strftime("%Y-%m-%d")
                    query = """UPDATE sistema SET 
                               nombre=?, tipo_filtro=?, modelo=?, eficiencia=?, medidas=?, cantidad=?, ubicacion=?, observaciones=?, fecha_actualizacion=? 
                               WHERE id=?"""
                    params = (nombre, tipo_filtro, modelo, eficiencia, medidas, cantidad, ubicacion, observaciones, fecha_actual, item_id)
                    
                    execute_query(query, params)
                    add_to_historial("MODIFICAR SISTEMA", f"ID: {item_id} | Nuevo: {nombre} | Ubicación: {ubicacion}", "Usuario")
                    
                    st.success("✅ Sistema actualizado exitosamente!")
                    st.rerun()


elif menu == "🔍 Buscar Sistema":
    st.header("🔍 Buscar Sistema")
    df_sis = get_sistema()
    
    if df_sis.empty:
        st.info("No hay sistemas registrados.")
    else:
        campo_busqueda_sis = st.selectbox("Seleccione campo de búsqueda:", 
            ["nombre", "tipo_filtro", "modelo", "eficiencia", "medidas", "ubicacion"])
        texto_busqueda_sis = st.text_input("Buscar:", placeholder="Ingrese texto a buscar...")
