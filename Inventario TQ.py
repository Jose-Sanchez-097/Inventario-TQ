import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
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
    """Inicializa la base de datos"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Eliminar tablas existentes y recrear
        c.execute("DROP TABLE IF EXISTS inventario")
        c.execute("DROP TABLE IF EXISTS sistema")
        c.execute("DROP TABLE IF EXISTS historial")
        c.execute("DROP TABLE IF EXISTS usuarios")
        
        # Tabla inventario
        c.execute('''CREATE TABLE inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            tipo_insumo TEXT NOT NULL, 
            modelo TEXT DEFAULT '', 
            cantidad INTEGER DEFAULT 0,
            cantidad_minima INTEGER DEFAULT 5, 
            proveedor TEXT DEFAULT '', 
            costo REAL DEFAULT 0,
            observaciones TEXT DEFAULT '', 
            fecha TEXT)''')
        
        # Tabla sistema - nueva estructura exacta
        c.execute('''CREATE TABLE sistema (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            equipo TEXT NOT NULL, 
            articulo TEXT DEFAULT '',
            modelo TEXT DEFAULT '', 
            medidas TEXT DEFAULT '', 
            eficiencia TEXT DEFAULT '', 
            cantidad INTEGER DEFAULT 0,
            ubicacion TEXT DEFAULT '', 
            observaciones TEXT DEFAULT '',
            fecha TEXT)''')
        
        # Tabla historial
        c.execute('''CREATE TABLE historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            fecha TEXT, accion TEXT, descripcion TEXT, usuario TEXT)''')
        
        # Tabla usuarios
        c.execute('''CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL, 
            rol TEXT DEFAULT 'usuario')''')
        
        # Admin
        password_admin = hashlib.sha256('TQ2026'.encode()).hexdigest()
        c.execute("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
                 ('admin', password_admin, 'administrador'))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error init_db: {e}")

def run_query(query, params=()):
    try:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query(query, conn, params=params if params else ())
        conn.close()
        return df
    except Exception as e:
        print(f"Error query: {e}")
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
        print(f"Error execute: {e}")
        return False

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
    df = run_query("SELECT id, username, rol FROM usuarios WHERE username = ? AND password = ?", 
                  (username, password_hash))
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

# Inicializar
init_db()

# ==================== PÁGINAS ====================

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
    
    col1, col2 = st.columns(2)
    col1.metric("📦 Insumos", len(df))
    col2.metric("⚙️ Sistemas", len(df_sis))
    
    st.markdown("---")
    st.subheader("📋 Inventario")
    st.dataframe(df)
    
    st.subheader("⚙️ Sistemas")
    st.dataframe(df_sis)

def pagina_agregar_insumo():
    st.header("➕ Agregar Insumo")
    
    with st.form("form_agregar"):
        tipo = st.text_input("Tipo *")
        modelo = st.text_input("Modelo")
        cantidad = st.number_input("Cantidad", min_value=0, step=1, value=0)
        submit = st.form_submit_button("💾 Guardar")
        
        if submit and tipo:
            fecha = datetime.now().strftime("%Y-%m-%d")
            
            success = execute_query(
                "INSERT INTO inventario (tipo_insumo, modelo, cantidad, fecha) VALUES (?, ?, ?, ?)",
                (tipo.strip(), modelo.strip() if modelo else "", cantidad, fecha)
            )
            
            if success:
                st.success("✅ Guardado!")
                st.rerun()
            else:
                st.error("❌ Error")

def pagina_buscar():
    st.header("🔍 Buscar Insumo")
    df = get_inventario()
    
    if df.empty:
        st.info("Sin datos")
    else:
        campo = st.selectbox("Campo", list(df.columns))
        texto = st.text_input("Buscar")
        
        if texto:
            res = df[df[campo].astype(str).str.contains(texto, case=False, na=False)]
            st.dataframe(res)

def pagina_sistema():
    st.header("⚙️ Agregar Sistema")
    
    with st.form("form_sistema"):
        c1, c2 = st.columns(2)
        with c1:
            equipo = st.text_input("Equipo *")
            articulo = st.text_input("Artículo")
            modelo = st.text_input("Modelo")
        with c2:
            medida = st.text_input("Medidas")
            eficiencia = st.text_input("Eficiencia")
            cantidad = st.number_input("Cantidad", min_value=0, step=1, value=0)
        
        ubicacion = st.text_input("Ubicación")
        observaciones = st.text_area("Observaciones")
        
        submit = st.form_submit_button("💾 Guardar")
        
        if submit and equipo:
            fecha = datetime.now().strftime("%Y-%m-%d")
            
            # Verificar estructura de la tabla
            print(f"Guardando sistema: equipo={equipo}")
            
            success = execute_query(
                "INSERT INTO sistema (equipo, articulo, modelo, medidas, eficiencia, cantidad, ubicacion, observaciones, fecha) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (equipo.strip(), 
                 articulo.strip() if articulo else "", 
                 modelo.strip() if modelo else "",
                 medida.strip() if medida else "",
                 eficiencia.strip() if eficiencia else "",
                 cantidad,
                 ubicacion.strip() if ubicacion else "",
                 observaciones.strip() if observaciones else "",
                 fecha)
            )
            
            if success:
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
        st.info("Sin sistemas")
    else:
        st.dataframe(df)

def pagina_historial():
    st.header("📜 Historial")
    df = get_historial()
    st.dataframe(df)

# ==================== MAIN ====================

def main():
    if not st.session_state.sesion_iniciada:
        pagina_login()
    else:
        st.sidebar.title("📦 Menú")
        menu = st.sidebar.selectbox("Opciones", 
            ["🏠 Inicio", "➕ Agregar Insumo", "🔍 Buscar Insumo", 
             "⚙️ Agregar Sistema", "🔍 Buscar Sistema", "📜 Historial"])
        
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Cerrar Sesión"):
            cerrar_sesion()
        
        if menu == "🏠 Inicio":
            mostrar_dashboard()
        elif menu == "➕ Agregar Insumo":
            pagina_agregar_insumo()
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
