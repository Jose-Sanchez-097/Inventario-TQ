import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib

st.set_page_config(page_title="📦 Gestión de Inventarios TQ", page_icon="📦", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
h1,h2,h3{color:#00d4ff!important}
div[data-testid="stMetric"]{background:linear-gradient(135deg,#667eea,#764ba2);padding:15px;border-radius:10px}
.stButton>button{background:#667eea;color:white;border-radius:8px}
</style>
""", unsafe_allow_html=True)

DB_FILE = 'inventario.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Tabla inventario
    c.execute('''CREATE TABLE IF NOT EXISTS inventario (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        tipo_insumo TEXT NOT NULL, 
        modelo TEXT,
        cantidad INTEGER DEFAULT 0,
        cantidad_minima INTEGER DEFAULT 5, 
        proveedor TEXT,
        costo REAL DEFAULT 0,
        observaciones TEXT,
        fecha TEXT)''')
    
    # Tabla sistema
    c.execute('''CREATE TABLE IF NOT EXISTS sistema (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        equipo TEXT NOT NULL, 
        articulo TEXT,
        modelo TEXT, 
        medida TEXT, 
        eficiencia TEXT, 
        cantidad INTEGER DEFAULT 0,
        ubicacion TEXT, 
        observaciones TEXT,
        cantidad_minima INTEGER DEFAULT 5,
        fecha TEXT)''')
    
    # Tabla historial
    c.execute('''CREATE TABLE IF NOT EXISTS historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        fecha TEXT, accion TEXT, descripcion TEXT, usuario TEXT)''')
    
    # Tabla usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL, 
        rol TEXT DEFAULT 'usuario')''')
    
    # Admin
    c.execute("SELECT id FROM usuarios WHERE username = 'admin'")
    if not c.fetchone():
        password_admin = hashlib.sha256('TQ2026'.encode()).hexdigest()
        c.execute("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
                 ('admin', password_admin, 'administrador'))
    
    # Agregar columnas faltantes si existen
    try:
        c.execute("ALTER TABLE sistema ADD COLUMN cantidad_minima INTEGER DEFAULT 5")
    except:
        pass
    
    conn.commit()
    conn.close()

def run_query(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(query, conn, params=params if params else ())
    conn.close()
    return df

def execute_query(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()
    return True

def get_inventario():
    return run_query("SELECT * FROM inventario")

def get_sistema():
    return run_query("SELECT * FROM sistema")

def get_historial():
    return run_query("SELECT * FROM historial ORDER BY fecha DESC")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_usuario(username, password):
    password_hash = hash_password(password)
    df = run_query("SELECT * FROM usuarios WHERE username = ? AND password = ?", (username, password_hash))
    return df.iloc[0] if not df.empty else None

def add_to_historial(accion, descripcion, usuario):
    try:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        execute_query("INSERT INTO historial (fecha, accion, descripcion, usuario) VALUES (?, ?, ?, ?)", 
                   (fecha, accion, descripcion, usuario))
    except:
        pass

# Sesión
if 'sesion_iniciada' not in st.session_state:
    st.session_state.sesion_iniciada = False
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None

def cerrar_sesion():
    st.session_state.sesion_iniciada = False
    st.session_state.usuario_actual = None
    st.rerun()

init_db()

# ==================== LOGIN ====================
def pagina_login():
    st.markdown("### 🔐 Iniciar Sesión")
    
    with st.form("form_login"):
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("🚀 Entrar")
        
        if submit:
            usuario_verificado = verificar_usuario(usuario, password)
            if usuario_verificado is not None:
                st.session_state.sesion_iniciada = True
                st.session_state.usuario_actual = usuario
                add_to_historial("LOGIN", f"Usuario {usuario} inició sesión", usuario)
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas")
    
    st.info("💡 admin / TQ2026")

# ==================== DASHBOARD ====================
def mostrar_dashboard():
    st.header("📊 Panel de Control")
    
    df = get_inventario()
    df_sis = get_sistema()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Insumos", len(df))
    col2.metric("⚙️ Sistemas", len(df_sis))
    
    # Stock bajo
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("⚠️ Stock Bajo - Insumos")
        if not df.empty:
            stock = df[df['cantidad'] < df['cantidad_minima']]
            if not stock.empty:
                st.error(f"¡{len(stock)} críticos!")
                st.dataframe(stock[['id','tipo_insumo','cantidad','cantidad_minima']])
            else:
                st.success("✅ Niveles óptimos")
    
    with c2:
        st.subheader("⚠️ Stock Bajo - Sistemas")
        if not df_sis.empty:
            stock = df_sis[df_sis['cantidad'] < df_sis.get('cantidad_minima', 5)]
            if not stock.empty:
                st.warning(f"¡{len(stock)} críticos!")
                st.dataframe(stock[['id','equipo','cantidad']])
            else:
                st.success("✅ Niveles óptimos")
    
    st.markdown("---")
    st.subheader("📋 Vista General Inventario")
    st.dataframe(df)
    
    st.subheader("⚙️ Vista General Sistemas")
    st.dataframe(df_sis)

# ==================== AGREGAR INSUMO ====================
def pagina_agregar_insumo():
    st.header("➕ Agregar Insumo")
    
    with st.form("form_agregar"):
        c1, c2 = st.columns(2)
        with c1:
            tipo = st.text_input("Tipo *")
            modelo = st.text_input("Modelo")
        with c2:
            cantidad = st.number_input("Cantidad", min_value=0, step=1, value=0)
            cantidad_min = st.number_input("Stock Mínimo", min_value=0, step=1, value=5)
        proveedor = st.text_input("Proveedor")
        costo = st.number_input("Costo", min_value=0.0, step=0.01)
        observaciones = st.text_area("Observaciones")
        
        submit = st.form_submit_button("💾 Guardar")
        
        if submit and tipo:
            fecha = datetime.now().strftime("%Y-%m-%d")
            execute_query(
                "INSERT INTO inventario (tipo_insumo, modelo, cantidad, cantidad_minima, proveedor, costo, observaciones, fecha) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (tipo, modelo if modelo else "", cantidad, cantidad_min, proveedor if proveedor else "", costo, observaciones if observaciones else "", fecha)
            )
            add_to_historial("AGREGAR INSUMO", f"Insumo: {tipo}", st.session_state.usuario_actual)
            st.success("✅ Guardado!")
            st.rerun()

# ==================== MODIFICAR INSUMO ====================
def pagina_modificar_insumo():
    st.header("✏️ Modificar Insumo")
    df = get_inventario()
    
    if df.empty:
        st.info("No hay insumos")
    else:
        opciones = df.apply(lambda x: f"{x['id']} - {x['tipo_insumo']}", axis=1).tolist()
        seleccion = st.selectbox("Seleccionar insumo", opciones)
        
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
                    cantidad_min = st.number_input("Stock Mínimo", min_value=0, value=int(item.get('cantidad_minima', 5)))
                submit = st.form_submit_button("✏️ Actualizar")
                
                if submit:
                    fecha = datetime.now().strftime("%Y-%m-%d")
                    execute_query(
                        "UPDATE inventario SET tipo_insumo=?, modelo=?, cantidad=?, cantidad_minima=?, fecha=? WHERE id=?",
                        (tipo, modelo if modelo else "", cantidad, cantidad_min, fecha, item_id)
                    )
                    add_to_historial("MODIFICAR INSUMO", f"ID: {item_id}", st.session_state.usuario_actual)
                    st.success("✅ Actualizado!")
                    st.rerun()

# ==================== ELIMINAR INSUMO ====================
def pagina_eliminar_insumo():
    st.header("🗑️ Eliminar Insumo")
    df = get_inventario()
    
    if df.empty:
        st.info("Inventario vacío")
    else:
        opciones = df.apply(lambda x: f"{x['id']} - {x['tipo_insumo']}", axis=1).tolist()
        seleccion = st.selectbox("Seleccionar insumo", opciones)
        passwd = st.text_input("Contraseña para confirmar", type="password")
        
        if st.button("🗑️ Eliminar"):
            if passwd == "TQ2026":
                item_id = int(seleccion.split(" - ")[0])
                nombre = df[df['id'] == item_id]['tipo_insumo'].values[0]
                execute_query("DELETE FROM inventario WHERE id=?", (item_id,))
                add_to_historial("ELIMINAR INSUMO", f"Insumo: {nombre}", st.session_state.usuario_actual)
                st.success("✅ Eliminado!")
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")

# ==================== BUSCAR INSUMO ====================
def pagina_buscar_insumo():
    st.header("🔍 Buscar Insumo")
    df = get_inventario()
    
    if df.empty:
        st.info("Sin datos")
    else:
        campo = st.selectbox("Campo de búsqueda", list(df.columns))
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

# ==================== AGREGAR SISTEMA ====================
def pagina_agregar_sistema():
    st.header("⚙️ Agregar Sistema")
    
    with st.form("form_sistema"):
        c1, c2 = st.columns(2)
        with c1:
            equipo = st.text_input("Equipo *")
            articulo = st.text_input("Artículo")
            modelo = st.text_input("Modelo")
        with c2:
            medida = st.text_input("Medida")
            eficiencia = st.text_input("Eficiencia")
            cantidad = st.number_input("Cantidad", min_value=0, step=1, value=0)
        
        ubicacion = st.text_input("Ubicación")
        observaciones = st.text_area("Observaciones")
        
        submit = st.form_submit_button("💾 Guardar Sistema")
        
        if submit and equipo:
            fecha = datetime.now().strftime("%Y-%m-%d")
            execute_query(
                "INSERT INTO sistema (equipo, articulo, modelo, medida, eficiencia, cantidad, ubicacion, observaciones, fecha) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (equipo, articulo if articulo else "", modelo if modelo else "", medida if medida else "", eficiencia if eficiencia else "", cantidad, ubicacion if ubicacion else "", observaciones if observaciones else "", fecha)
            )
            add_to_historial("AGREGAR SISTEMA", f"Sistema: {equipo}", st.session_state.usuario_actual)
            st.success("✅ Sistema guardado!")
            st.rerun()
        elif submit:
            st.warning("El campo Equipo es requerido")

# ==================== MODIFICAR SISTEMA ====================
def pagina_modificar_sistema():
    st.header("✏️ Modificar Sistema")
    df = get_sistema()
    
    if df.empty:
        st.info("No hay sistemas")
    else:
        opciones = df.apply(lambda x: f"{x['id']} - {x['equipo']}", axis=1).tolist()
        seleccion = st.selectbox("Seleccionar sistema", opciones)
        
        if seleccion:
            item_id = int(seleccion.split(" - ")[0])
            item = df[df['id'] == item_id].iloc[0]
            
            with st.form("form_mod_sis"):
                c1, c2 = st.columns(2)
                with c1:
                    equipo = st.text_input("Equipo", value=str(item['equipo']))
                    articulo = st.text_input("Artículo", value=str(item.get('articulo', '')))
                    modelo = st.text_input("Modelo", value=str(item.get('modelo', '')))
                with c2:
                    medida = st.text_input("Medida", value=str(item.get('medida', '')))
                    eficiencia = st.text_input("Eficiencia", value=str(item.get('eficiencia', '')))
                    cantidad = st.number_input("Cantidad", min_value=0, value=int(item['cantidad']))
                ubicacion = st.text_input("Ubicación", value=str(item.get('ubicacion', '')))
                observaciones = st.text_area("Observaciones", value=str(item.get('observaciones', '')))
                submit = st.form_submit_button("✏️ Actualizar")
                
                if submit:
                    fecha = datetime.now().strftime("%Y-%m-%d")
                    execute_query(
                        "UPDATE sistema SET equipo=?, articulo=?, modelo=?, medida=?, eficiencia=?, cantidad=?, ubicacion=?, observaciones=?, fecha=? WHERE id=?",
                        (equipo, articulo if articulo else "", modelo if modelo else "", medida if medida else "", eficiencia if eficiencia else "", cantidad, ubicacion if ubicacion else "", observaciones if observaciones else "", fecha, item_id)
                    )
                    add_to_historial("MODIFICAR SISTEMA", f"ID: {item_id}", st.session_state.usuario_actual)
                    st.success("✅ Actualizado!")
                    st.rerun()

# ==================== ELIMINAR SISTEMA ====================
def pagina_eliminar_sistema():
    st.header("🗑️ Eliminar Sistema")
    df = get_sistema()
    
    if df.empty:
        st.info("No hay sistemas")
    else:
        opciones = df.apply(lambda x: f"{x['id']} - {x['equipo']}", axis=1).tolist()
        seleccion = st.selectbox("Seleccionar sistema", opciones)
        passwd = st.text_input("Contraseña para confirmar", type="password")
        
        if st.button("🗑️ Eliminar"):
            if passwd == "TQ2026":
                item_id = int(seleccion.split(" - ")[0])
                nombre = df[df['id'] == item_id]['equipo'].values[0]
                execute_query("DELETE FROM sistema WHERE id=?", (item_id,))
                add_to_historial("ELIMINAR SISTEMA", f"Sistema: {nombre}", st.session_state.usuario_actual)
                st.success("✅ Eliminado!")
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")

# ==================== BUSCAR SISTEMA ====================
def pagina_buscar_sistema():
    st.header("🔍 Buscar Sistema")
    df = get_sistema()
    
    if df.empty:
        st.info("Sin sistemas")
    else:
        campo = st.selectbox("Campo de búsqueda", list(df.columns))
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

# ==================== HISTORIAL ====================
def pagina_historial():
    st.header("📜 Historial de Movimientos")
    df = get_historial()
    
    if df.empty:
        st.info("Sin movimientos")
    else:
        st.dataframe(df)

==================== MAIN ====================
def main():
    if not st.session_state.sesion_iniciada:
        pagina_login()
    else:
        st.sidebar.title("📦 Menú")
        menu = st.sidebar.selectbox("Opciones", 
            ["🏠 Inicio", 
             "➕ Agregar Insumo", "✏️ Modificar Insumo", "🗑️ Eliminar Insumo", "🔍 Buscar Insumo",
             "⚙️ Agregar Sistema", "✏️ Modificar Sistema", "🗑️ Eliminar Sistema", "🔍 Buscar Sistema",
             "📜 Historial"])
        
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
            pagina_buscar_insumo()
        elif menu == "⚙️ Agregar Sistema":
            pagina_agregar_sistema()
        elif menu == "✏️ Modificar Sistema":
            pagina_modificar_sistema()
        elif menu == "🗑️ Eliminar Sistema":
            pagina_eliminar_sistema()
        elif menu == "🔍 Buscar Sistema":
            pagina_buscar_sistema()
        elif menu == "📜 Historial":
            pagina_historial()

if __name__ == "__main__":
    main()
