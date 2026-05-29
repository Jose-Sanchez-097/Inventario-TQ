import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib

st.set_page_config(page_title="📦 Gestión de Inventarios TQ", page_icon="📦", layout="wide", initial_sidebar_state="expanded")

DB_FILE = 'inventario.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Eliminar y recrear tabla sistema específicamente
    c.execute("DROP TABLE IF EXISTS sistema")
    
    # Tabla sistema con estructura simple
    c.execute('''CREATE TABLE sistema (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        equipo TEXT NOT NULL, 
        articulo TEXT,
        modelo TEXT, 
        medida TEXT, 
        eficiencia TEXT, 
        cantidad INTEGER DEFAULT 0,
        ubicacion TEXT, 
        observaciones TEXT,
        fecha TEXT)''')
    
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
    rows = c.rowcount  # Verificar que se ejecutó
    conn.close()
    print(f"Ejecutado: {rows} fila(s)")
    return True

def get_inventario():
    return run_query("SELECT * FROM inventario")

def get_sistema():
    return run_query("SELECT * FROM sistema")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_usuario(username, password):
    password_hash = hash_password(password)
    df = run_query("SELECT * FROM usuarios WHERE username = ? AND password = ?", (username, password_hash))
    return df.iloc[0] if not df.empty else None

if 'sesion_iniciada' not in st.session_state:
    st.session_state.sesion_iniciada = False

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
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas")
    
    st.info("💡 admin / TQ2026")

# ==================== DASHBOARD ====================
def mostrar_dashboard():
    st.header("📊 Panel de Control")
    
    df = get_inventario()
    df_sis = get_sistema()
    
    col1, col2 = st.columns(2)
    col1.metric("📦 Insumos", len(df))
    col2.metric("⚙️ Sistemas", len(df_sis))
    
    st.markdown("---")
    st.subheader("⚙️ Sistemas Registrados")
    st.dataframe(df_sis)

# ==================== AGREGAR SISTEMA (SIMPLE) ====================
def pagina_sistema():
    st.header("⚙️ Agregar Sistema")
    
    # Ver estructura
    df_test = run_query("SELECT * FROM sistema LIMIT 0")
    st.caption(f"Columnas: {list(df_test.columns)}")
    
    with st.form("form_sistema"):
        equipo = st.text_input("Equipo *")
        articulo = st.text_input("Artículo")
        modelo = st.text_input("Modelo")
        medida = st.text_input("Medida")
        eficiencia = st.text_input("Eficiencia")
        cantidad = st.number_input("Cantidad", min_value=0, step=1, value=0)
        ubicacion = st.text_input("Ubicación")
        observaciones = st.text_area("Observaciones")
        
        submit = st.form_submit_button("💾 Guardar Sistema")
        
        if submit and equipo:
            fecha = datetime.now().strftime("%Y-%m-%d")
            
            # Consulta simple - solo equipo primero, luego agregamos los demás
            query = """INSERT INTO sistema 
                (equipo, articulo, modelo, medida, eficiencia, cantidad, ubicacion, observaciones, fecha) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            
            params = (
                equipo,
                articulo if articulo else "",
                modelo if modelo else "",
                medida if medida else "",
                eficiencia if eficiencia else "",
                int(cantidad),
                ubicacion if ubicacion else "",
                observaciones if observaciones else "",
                fecha
            )
            
            print(f"Query: {query}")
            print(f"Params: {params}")
            
            # Ejecutar
            success = execute_query(query, params)
            
            if success:
                st.success("✅ Sistema guardado correctamente!")
                st.rerun()
            else:
                st.error("❌ Error al guardar")
        elif submit:
            st.warning("El campo Equipo es requerido")

# ==================== AGREGAR INSUMO ====================
def pagina_agregar_insumo():
    st.header("➕ Agregar Insumo")
    
    with st.form("form_agregar"):
        tipo = st.text_input("Tipo *")
        cantidad = st.number_input("Cantidad", min_value=0, step=1, value=0)
        submit = st.form_submit_button("💾 Guardar")
        
        if submit and tipo:
            fecha = datetime.now().strftime("%Y-%m-%d")
            execute_query("INSERT INTO inventario (tipo_insumo, cantidad, fecha) VALUES (?, ?, ?)", 
                       (tipo, cantidad, fecha))
            st.success("✅ Guardado!")
            st.rerun()

# ==================== MAIN ====================
def main():
    if not st.session_state.sesion_iniciada:
        pagina_login()
    else:
        st.sidebar.title("📦 Menú")
        menu = st.sidebar.selectbox("Opciones", 
            ["🏠 Inicio", "➕ Agregar Insumo", "⚙️ Agregar Sistema"])
        
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Cerrar Sesión"):
            st.session_state.sesion_iniciada = False
            st.rerun()
        
        if menu == "🏠 Inicio":
            mostrar_dashboard()
        elif menu == "➕ Agregar Insumo":
            pagina_agregar_insumo()
        elif menu == "⚙️ Agregar Sistema":
            pagina_sistema()

if __name__ == "__main__":
    main()
