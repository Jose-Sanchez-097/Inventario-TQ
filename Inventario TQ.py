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
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Tabla inventario
    c.execute('''CREATE TABLE IF NOT EXISTS inventario (
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
    
    # Tabla sistema - NUEVA ESTRUCTURA
    c.execute('''CREATE TABLE IF NOT EXISTS sistema (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        equipo TEXT NOT NULL, 
        articulo TEXT DEFAULT '',
        modelo TEXT DEFAULT '', 
        medidas TEXT DEFAULT '', 
        eficiencia TEXT DEFAULT '', 
        cantidad INTEGER DEFAULT 0,
        ubicacion TEXT DEFAULT '', 
        observaciones TEXT DEFAULT '',
        cantidad_minima INTEGER DEFAULT 5,
        fecha_actualizacion TEXT, 
        fecha_creacion TEXT)''')
    
    # Tabla historial
    c.execute('''CREATE TABLE IF NOT EXISTS historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        fecha TEXT, 
        accion TEXT, 
        descripcion TEXT, 
        usuario TEXT)''')
    
    # Tabla usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL, 
        rol TEXT DEFAULT 'usuario', 
        fecha_creacion TEXT)''')
    
    # Tabla proveedores
    c.execute('''CREATE TABLE IF NOT EXISTS proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        nombre TEXT NOT NULL, 
        contacto TEXT DEFAULT '',
        telefono TEXT DEFAULT '', 
        email TEXT DEFAULT '', 
        observaciones TEXT DEFAULT '', 
        fecha_actualizacion TEXT)''')
    
    # Tabla ordenes
    c.execute('''CREATE TABLE IF NOT EXISTS ordenes_pedido (
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
    c.execute("SELECT id FROM usuarios WHERE username = 'admin'")
    if not c.fetchone():
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
        print(f"Error: {e}")
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
        print(f"Error: {e}")
        return False

def get_inventario():
    return run_query("SELECT id, tipo_insumo, modelo, equipo, cantidad, cantidad_minima, proveedor, costo_unitario, observaciones FROM inventario")

def get_sistema():
    return run_query("SELECT id, equipo, articulo, modelo, medidas, eficiencia, cantidad, ubicacion, observaciones FROM sistema")

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
    
    col4.metric("💰 Valor", f"${valor:,.0f}")
    
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("⚠️ Stock Bajo - Insumos")
        if not df.empty:
            stock = df[df['cantidad'] < df['cantidad_minima']]
            if not stock.empty:
                st.error(f"¡{len(stock)} críticos!")
                st.dataframe(stock)
            else:
                st.success("✅ OK")
    with c2:
        st.subheader("⚠️ Stock Bajo - Sistemas")
        if not df_sis.empty:
            stock = df_sis[df_sis['cantidad'] < df_sis.get('cantidad_minima', 5)]
            if not stock.empty:
                st.warning(f"¡{len(stock)} críticos!")
                st.dataframe(stock)
            else:
                st.success("✅ OK")
    
    st.markdown("---")
    st.subheader("📋 Inventario")
    if not df.empty:
        st.dataframe(df)
    else:
        st.info("No hay insumos registrados")

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
            
            success = execute_query(
                "INSERT INTO inventario (tipo_insumo, medidas, modelo, equipo, cantidad, cantidad_minima, proveedor, costo_unitario, observaciones, fecha_actualizacion, fecha_creacion) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (tipo.strip(), modelo.strip() if modelo else "", medidas.strip() if medidas else "", equipo.strip() if equipo else "", cantidad, cantidad_min, proveedor.strip() if proveedor else "", costo, observaciones.strip() if observaciones else "", fecha, fecha)
            )
            
            if success:
                add_to_historial("AGREGAR", f"Insumo: {tipo}", st.session_state.usuario_actual)
                st.success("✅ Guardado!")
                st.rerun()
            else:
                st.error("❌ Error")

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
                submit = st.form_submit_button("✏️ Actualizar")
                if submit:
                    fecha = datetime.now().strftime("%Y-%m-%d")
                    execute_query(
                        "UPDATE inventario SET tipo_insumo=?, modelo=?, cantidad=?, cantidad_minima=?, fecha_actualizacion=? WHERE id=?",
                        (tipo, modelo, cantidad, cantidad_min, fecha, item_id)
                    )
                    st.success("✅ Actualizado!")
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
                st.success("✅ Eliminado!")
                st.rerun()
            else:
                st.error("❌ Error")

def pagina_buscar():
    st.header("🔍 Buscar")
    df = get_inventario()
    if df.empty:
        st.info("Sin datos")
    else:
        columnas = list(df.columns)
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
    with st.form("form_sistema"):
        c1, c2 = st.columns(2)
        with c1:
            equipo = st.text_input("Equipo *")
            articulo = st.text_input("Articulo")
            modelo = st.text_input("Modelo")
        with c2:
            medida = st.text_input("Medida")
            eficiencia = st.text_input("Eficiencia")
            cantidad = st.number_input("Cantidad", min_value=0, step=1, value=0)
        
        ubicacion = st.text_input("Ubicación")
        observaciones = st.text_area("Observaciones")
        
        submit = st.form_submit_button("💾 Guardar", use_container_width=True)
        
        if submit and equipo:
            fecha = datetime.now().strftime("%Y-%m-%d")
            
            success = execute_query(
                "INSERT INTO sistema (equipo, articulo, modelo, medidas, eficiencia, cantidad, ubicacion, observaciones, cantidad_minima, fecha_actualizacion, fecha_creacion) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (equipo.strip(), articulo.strip() if articulo else "", modelo.strip() if modelo else "", medida.strip() if medida else "", eficiencia.strip() if eficiencia else "", cantidad, ubicacion.strip() if ubicacion else "", observaciones.strip() if observaciones else "", 5, fecha, fecha)
            )
            
            if success:
                add_to_historial("AGREGAR SISTEMA", f"Sistema: {equipo}", st.session_state.usuario_actual)
                st.success("✅ Sistema guardado!")
                st.rerun()
            else:
                st.error("❌ Error al guardar")
        elif submit:
            st.warning("El campo Equipo es requerido")

def pagina_buscar_sistema():
    st.header("🔍 Buscar Sistema")
    df = get_sistema()
    if df.empty:
        st.info("Sin sistemas registrados")
    else:
        columnas = list(df.columns)
        campo = st.selectbox("Campo de búsqueda", columnas)
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
            ["🏠 Inicio", "➕ Agregar Insumo", "✏️ Modificar Insumo", "🗑️ Eliminar Insumo", "🔍 Buscar Insumo", "⚙️ Agregar Sistema", "🔍 Buscar Sistema", "📜 Historial"])
        
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Cerrar Sesión"):
            cerrar_sesion()
        
        if menu == "🏠 Inicio":
            mostrar_dashboard()
        elif menu == "➕ Agregar Insumo":
            pagina_agregar_insumo()
        elif menu == "✏️ Modificar Insumo":
            pagina_modificar_insumo()
        elif menu == "🗑️ Eliminar Insumo":
            pagina_eliminar_insumo()
        elif menu == "🔍 Buscar Insumo":
            pagina_buscar()
        elif menu == "⚙️ Agregar Sistema":
            pagina_sistema()
        elif menu == "🔍 Buscar Sistema":
            pagina_buscar_sistema()
        elif menu == "📜 Historial":
            pagina_historial()

if __name__ == "__main__":
    main()
    
