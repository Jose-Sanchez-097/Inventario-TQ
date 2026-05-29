import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
import hashlib
import os

st.set_page_config(page_title="📦 Gestión de Inventarios TQ", page_icon="📦", layout="wide", initial_sidebar_state="expanded")

DB_FILE = 'inventario.db'

st.markdown("""
<style>
h1,h2,h3{color:#00d4ff!important}
div[data-testid="stMetric"]{background:linear-gradient(135deg,#667eea,#764ba2);padding:15px;border-radius:10px}
.stButton>button{background:linear-gradient(135deg,#667eea,#764ba2);border:none;border-radius:8px;color:white}
</style>
""", unsafe_allow_html=True)

def init_db():
    # Eliminar base de datos existente para empezar limpio
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Tabla inventario - solo columnas esenciales
    c.execute('''CREATE TABLE inventario (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        tipo_insumo TEXT NOT NULL, 
        medidas TEXT DEFAULT '',
        eficiencia TEXT DEFAULT '', 
        modelo TEXT DEFAULT '', 
        equipo TEXT DEFAULT '', 
        cantidad INTEGER DEFAULT 0,
        cantidad_minima INTEGER DEFAULT 5, 
        proveedor TEXT DEFAULT '', 
        costo_unitario REAL DEFAULT 0,
        realizado_por TEXT DEFAULT '', 
        observaciones TEXT DEFAULT '', 
        fecha_actualizacion TEXT, 
        fecha_creacion TEXT)''')
    
    # Tabla sistema
    c.execute('''CREATE TABLE sistema (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        nombre TEXT NOT NULL, 
        tipo_filtro TEXT DEFAULT '',
        modelo TEXT DEFAULT '', 
        eficiencia TEXT DEFAULT '', 
        medidas TEXT DEFAULT '', 
        cantidad INTEGER DEFAULT 0,
        cantidad_minima INTEGER DEFAULT 5, 
        costo_unitario REAL DEFAULT 0,
        fecha_actualizacion TEXT, 
        fecha_creacion TEXT)''')
    
    # Tabla historial
    c.execute('''CREATE TABLE historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        fecha TEXT, 
        accion TEXT, 
        descripcion TEXT, 
        usuario TEXT)''')
    
    # Tabla usuarios
    c.execute('''CREATE TABLE usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL, 
        rol TEXT DEFAULT 'usuario', 
        fecha_creacion TEXT)''')
    
    # Tabla proveedores
    c.execute('''CREATE TABLE proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        nombre TEXT NOT NULL, 
        contacto TEXT DEFAULT '',
        telefono TEXT DEFAULT '', 
        email TEXT DEFAULT '', 
        observaciones TEXT DEFAULT '', 
        fecha_actualizacion TEXT)''')
    
    # Tabla ordenes
    c.execute('''CREATE TABLE ordenes_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        orden_numero TEXT UNIQUE NOT NULL,
        insumo_id INTEGER, 
        cantidad_solicitada INTEGER, 
        proveedor TEXT DEFAULT '', 
        estado TEXT DEFAULT 'pendiente',
        fecha_solicitud TEXT, 
        observaciones TEXT DEFAULT '', 
        usuario_solicita TEXT)''')
    
    # Admin por defecto
    password_admin = hashlib.sha256('TQ2026'.encode()).hexdigest()
    c.execute("INSERT INTO usuarios (username, password, rol, fecha_creacion) VALUES (?, ?, ?, ?)",
             ('admin', password_admin, 'administrador', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()

def run_query(query, params=()):
    try:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query(query, conn, params=params if params else ())
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error en consulta: {e}")
        return pd.DataFrame()

def execute_query(query, params=()):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error en ejecución: {e}")
        return False

def get_inventario():
    return run_query("SELECT * FROM inventario")

def get_sistema():
    return run_query("SELECT * FROM sistema")

def get_historial():
    return run_query("SELECT * FROM historial ORDER BY fecha DESC")

def get_proveedores():
    return run_query("SELECT * FROM proveedores")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_usuario(username, password):
    password_hash = hash_password(password)
    df = run_query("SELECT id, username, rol FROM usuarios WHERE username = ? AND password = ?", (username, password_hash))
    return df.iloc[0] if not df.empty else None

def add_to_historial(accion, descripcion, usuario):
    try:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        execute_query("INSERT INTO historial (fecha, accion, descripcion, usuario) VALUES (?, ?, ?, ?)", (fecha, accion, descripcion, usuario))
    except:
        pass

def mostrar_mensaje(mensaje, tipo='success'):
    if tipo == 'success': st.success(mensaje)
    elif tipo == 'error': st.error(mensaje)
    elif tipo == 'warning': st.warning(mensaje)
    time.sleep(2)

if 'sesion_iniciada' not in st.session_state:
    st.session_state.sesion_iniciada = False
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None

def cerrar_sesion():
    st.session_state.sesion_iniciada = False
    st.session_state.usuario_actual = None
    st.rerun()

init_db()

def pagina_login():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("### 🔐 Iniciar Sesión")
        with st.form("form_login"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("🚀 Entrar", use_container_width=True)
            if submit:
                usuario_verificado = verificar_usuario(usuario, password)
                if usuario_verificado is not None:
                    st.session_state.sesion_iniciada = True
                    st.session_state.usuario_actual = usuario_verificado['username']
                    add_to_historial("LOGIN", f"Usuario {usuario} inició sesión", usuario)
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")
        st.info("💡 admin / TQ2026")

def mostrar_dashboard():
    st.header("📊 Panel de Control")
    
    df = get_inventario()
    df_sis = get_sistema()
    df_prov = get_proveedores()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Insumos", len(df))
    col2.metric("⚙️ Sistemas", len(df_sis))
    col3.metric("🚚 Proveedores", len(df_prov))
    
    valor = 0
    if not df.empty:
        valor += (df['cantidad'] * df['costo_unitario']).sum()
    if not df_sis.empty:
        valor += (df_sis['cantidad'] * df_sis['costo_unitario']).sum()
    
    col4.metric("💰 Valor", f"${valor:,.0f}")
    
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("⚠️ Stock Bajo - Insumos")
        if not df.empty:
            stock = df[df['cantidad'] < df['cantidad_minima']]
            if not stock.empty:
                st.error(f"¡{len(stock)} críticos!")
                cols = [c for c in ['tipo_insumo','modelo','cantidad','proveedor'] if c in stock.columns]
                if cols:
                    st.dataframe(stock[cols])
            else:
                st.success("✅ OK")
    with c2:
        st.subheader("⚠️ Stock Bajo - Sistemas")
        if not df_sis.empty:
            stock = df_sis[df_sis['cantidad'] < df_sis['cantidad_minima']]
            if not stock.empty:
                st.warning(f"¡{len(stock)} críticos!")
                cols = [c for c in ['nombre','modelo','cantidad'] if c in stock.columns]
                if cols:
                    st.dataframe(stock[cols])
            else:
                st.success("✅ OK")
    
    st.markdown("---")
    st.subheader("📋 Inventario")
    if not df.empty:
        st.dataframe(df)

def pagina_agregar_insumo():
    st.header("➕ Agregar Insumo")
    with st.form("form_agregar"):
        c1, c2 = st.columns(2)
        with c1:
            tipo = st.text_input("Tipo *")
            modelo = st.text_input("Modelo")
            medidas = st.text_input("Medidas")
        with c2:
            equipo = st.text_input("Equipo")
            cantidad = st.number_input("Cantidad", min_value=0, step=1, value=0)
            cantidad_min = st.number_input("Stock Mínimo", min_value=0, step=1, value=5)
        c3, c4 = st.columns(2)
        with c3:
            proveedor = st.text_input("Proveedor")
            costo = st.number_input("Costo", min_value=0.0, step=0.01)
        with c4:
            observaciones = st.text_area("Observaciones")
        
        submit = st.form_submit_button("💾 Guardar", use_container_width=True)
        
        if submit and tipo:
            fecha = datetime.now().strftime("%Y-%m-%d")
            
            # Valores por defecto para campos vacíos
            modelo = modelo if modelo else ""
            medidas = medidas if medidas else ""
            equipo = equipo if equipo else ""
            proveedor = proveedor if proveedor else ""
            observaciones = observaciones if observaciones else ""
            
            # Consulta simplificada
            success = execute_query(
                "INSERT INTO inventario (tipo_insumo, medidas, modelo, equipo, cantidad, cantidad_minima, proveedor, costo_unitario, observaciones, fecha_actualizacion, fecha_creacion) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (tipo, medidas, modelo, equipo, cantidad, cantidad_min, proveedor, costo, observaciones, fecha, fecha)
            )
            
            if success:
                add_to_historial("AGREGAR", f"Insumo: {tipo}", st.session_state.usuario_actual)
                mostrar_mensaje("✅ Insumo agregado correctamente")
                st.rerun()
            else:
                st.error("❌ Error al guardar")
        elif submit:
            st.warning("Completar tipo requerido")

def pagina_modificar_insumo():
    st.header("✏️ Modificar Insumo")
    df = get_inventario()
    if df.empty:
        st.info("Vacío")
    else:
        opciones = df.apply(lambda x: f"{x['id']} - {x['tipo_insumo']}", axis=1).tolist()
        seleccion = st.selectbox("Seleccionar", opciones)
        if seleccion:
            item_id = int(seleccion.split(" - ")[0])
            item = df[df['id'] == item_id].iloc[0]
            with st.form("form_mod"):
                c1, c2 = st.columns(2)
                with c1:
                    tipo = st.text_input("Tipo", value=str(item['tipo_insumo']))
                    modelo = st.text_input("Modelo", value=str(item.get('modelo', '')))
                with c2:
                    cantidad = st.number_input("Cantidad", min_value=0, value=int(item['cantidad']))
                    cantidad_min = st.number_input("Stock Mín", min_value=0, value=int(item['cantidad_minima']))
                submit = st.form_submit_button("✏️ Actualizar", use_container_width=True)
                if submit:
                    fecha = datetime.now().strftime("%Y-%m-%d")
                    execute_query(
                        "UPDATE inventario SET tipo_insumo=?, modelo=?, cantidad=?, cantidad_minima=?, fecha_actualizacion=? WHERE id=?",
                        (tipo, modelo, cantidad, cantidad_min, fecha, item_id)
                    )
                    add_to_historial("MODIFICAR", f"ID: {item_id}", st.session_state.usuario_actual)
                    mostrar_mensaje("✅ OK")
                    st.rerun()

def pagina_eliminar_insumo():
    st.header("🗑️ Eliminar Insumo")
    df = get_inventario()
    if df.empty:
        st.info("Vacío")
    else:
        opciones = df.apply(lambda x: f"{x['id']} - {x['tipo_insumo']}", axis=1).tolist()
        seleccion = st.selectbox("Seleccionar", opciones)
        passwd = st.text_input("Contraseña", type="password")
        if st.button("🗑️ Eliminar"):
            if passwd == "TQ2026":
                item_id = int(seleccion.split(" - ")[0])
                execute_query("DELETE FROM inventario WHERE id=?", (item_id,))
                add_to_historial("ELIMINAR", f"ID: {item_id}", st.session_state.usuario_actual)
                mostrar_mensaje("✅ OK")
                st.rerun()
            else:
                st.error("❌ Error")

def pagina_buscar():
    st.header("🔍 Buscar")
    df = get_inventario()
    if df.empty:
        st.info("Sin datos")
    else:
        columnas = [c for c in df.columns]
        campo = st.selectbox("Campo", columnas)
        texto = st.text_input("Buscar", placeholder="...")
        if texto:
            res = df[df[campo].astype(str).str.contains(texto, case=False, na=False)]
            if not res.empty:
                st.success(f"✅ {len(res)} resultados")
                st.dataframe(res)
            else:
                st.warning("Sin resultados")
        else:
            st.dataframe(df)

def pagina_sistema():
    st.header("⚙️ Agregar Sistema")
    with st.form("form_sis"):
        nombre = st.text_input("Nombre *")
        modelo = st.text_input("Modelo")
        cantidad = st.number_input("Cantidad", min_value=0, step=1, value=0)
        submit = st.form_submit_button("💾 Guardar", use_container_width=True)
        if submit and nombre:
            fecha = datetime.now().strftime("%Y-%m-%d")
            execute_query(
                "INSERT INTO sistema (nombre, modelo, cantidad, fecha_actualizacion, fecha_creacion) VALUES (?, ?, ?, ?, ?)",
                (nombre, modelo if modelo else "", cantidad, fecha, fecha)
            )
            add_to_historial("AGREGAR SISTEMA", nombre, st.session_state.usuario_actual)
            mostrar_mensaje("✅ OK")
            st.rerun()

def pagina_historial():
    st.header("📜 Historial")
    df = get_historial()
    if df.empty:
        st.info("Sin movimientos")
    else:
        st.dataframe(df)

def main():
    if not st.session_state.sesion_iniciada:
        pagina_login()
    else:
        st.sidebar.title("📦 Menú")
        menu = st.sidebar.selectbox("Opciones", 
            ["🏠 Inicio", "➕ Agregar", "✏️ Modificar", "🗑️ Eliminar", "🔍 Buscar", "⚙️ Sistema", "📜 Historial"])
        
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Cerrar Sesión"):
            cerrar_sesion()
        
        if menu == "🏠 Inicio":
            mostrar_dashboard()
        elif menu == "➕ Agregar":
            pagina_agregar_insumo()
        elif menu == "✏️ Modificar":
            pagina_modificar_insumo()
        elif menu == "🗑️ Eliminar":
            pagina_eliminar_insumo()
        elif menu == "🔍 Buscar":
            pagina_buscar()
        elif menu == "⚙️ Sistema":
            pagina_sistema()
        elif menu == "📜 Historial":
            pagina_historial()

if __name__ == "__main__":
    main()
