import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import hashlib
from pathlib import Path

# ============================================
# CONFIGURACIÓN DE LA APP
# ============================================
st.set_page_config(
    page_title="📦 Gestión de Inventarios TQ",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# ESTILOS CSS PERSONALIZADOS
# ============================================
st.markdown("""
<style>
    /* Tema oscuro/claro según preferencia */
    <style>
    /* Estilos principales */
    .main {
        background-color: #0e1117;
    }
    .stApp {
        background: linear-gradient(to bottom right, #0e1117, #1a1a2e);
    }
    
    /* Tarjetas de métricas */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    /* Encabezados */
    h1, h2, h3 {
        color: #00d4ff !important;
        font-weight: bold;
    }
    
    /* Botones primary */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 10px;
        color: white;
        font-weight: bold;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(to bottom, #1a1a2e, #0e1117);
    }
    
    /* Alertas */
    .stAlert {
        border-radius: 10px;
    }
    
    /* Tablas */
    .dataframe {
        border-radius: 10px;
    }
    
    /* Campos de formulario */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================
DB_FILE = 'inventario.db'

def init_db():
    """Inicializa la base de datos con todas las tablas necesarias"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Tabla de inventario principal
    c.execute("""CREATE TABLE IF NOT EXISTS inventario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo_insumo TEXT NOT NULL,
        medidas TEXT,
        eficiencia TEXT,
        modelo TEXT,
        equipo TEXT,
        cantidad INTEGER DEFAULT 0,
        cantidad_minima INTEGER DEFAULT 5,
        proveedor TEXT,
        costo_unitario REAL DEFAULT 0,
        realizado_por TEXT,
        observaciones TEXT,
        fecha_actualizacion TEXT,
        fecha_creacion TEXT)""")
    
    # Tabla de sistemas
    c.execute("""CREATE TABLE IF NOT EXISTS sistema (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        tipo_filtro TEXT,
        modelo TEXT,
        eficiencia TEXT,
        medidas TEXT,
        cantidad INTEGER DEFAULT 0,
        cantidad_minima INTEGER DEFAULT 5,
        costo_unitario REAL DEFAULT 0,
        fecha_actualizacion TEXT,
        fecha_creacion TEXT)""")
    
    # Tabla de historial
    c.execute("""CREATE TABLE IF NOT EXISTS historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        accion TEXT,
        descripcion TEXT,
        usuario TEXT)""")
    
    # Tabla de usuarios
    c.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        rol TEXT DEFAULT 'usuario',
        fecha_creacion TEXT)""")
    
    # Tabla de proveedores
    c.execute("""CREATE TABLE IF NOT EXISTS proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        contacto TEXT,
        telefono TEXT,
        email TEXT,
        direccion TEXT,
        observaciones TEXT,
        fecha_actualizacion TEXT)""")
    
    # Tabla de órdenes de pedido
    c.execute("""CREATE TABLE IF NOT EXISTS ordenes_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_numero TEXT UNIQUE NOT NULL,
        insumo_id INTEGER,
        cantidad_solicitada INTEGER,
        proveedor TEXT,
        estado TEXT DEFAULT 'pendiente',
        fecha_solicitud TEXT,
        fecha_entrega TEXT,
        observaciones TEXT,
        usuario_solicita TEXT)""")
    
    # Tabla de configuración
    c.execute("""CREATE TABLE IF NOT EXISTS configuracion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        clave TEXT UNIQUE,
        valor TEXT)""")
    
    # Crear usuario admin por defecto si no existe
    c.execute("SELECT id FROM usuarios WHERE username = 'admin'")
    if not c.fetchone():
        password_admin = hashlib.sha256('TQ2026'.encode()).hexdigest()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO usuarios (username, password, rol, fecha_creacion) VALUES (?, ?, ?, ?)",
                  ('admin', password_admin, 'administrador', fecha))
    
    conn.commit()
    conn.close()

# ============================================
# FUNCIONES DE BASE DE DATOS (SEGURAS)
# ============================================
def run_query(query, params=()):
    """Ejecuta consultas SELECT de forma segura"""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(query, conn, params=params if params else ())
    conn.close()
    return df

def execute_query(query, params=()):
    """Ejecuta consultas INSERT/UPDATE/DELETE de forma segura"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

def execute_many(query, list_params):
    """Ejecuta múltiples consultas de una vez"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.executemany(query, list_params)
    conn.commit()
    conn.close()

# ============================================
# FUNCIONES AUXILIARES
# ============================================
def hash_password(password):
    """Hashea una contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_usuario(username, password):
    """Verifica credenciales del usuario"""
    password_hash = hash_password(password)
    df = run_query("SELECT id, username, rol FROM usuarios WHERE username = ? AND password = ?", 
                  (username, password_hash))
    return df.iloc[0] if not df.empty else None

def generar_numero_orden():
    """Genera un número único para órdenes"""
    return f"ORD-{datetime.now().strftime('%Y%m%d')}-{int(time.time())}"

def exportar_excel(df, filename):
    """Exporta DataFrame a Excel"""
    return df.to_excel(index=False, engine='openpyxl')

def crear_backup():
    """Crea una copia de seguridad de la base de datos"""
    if os.path.exists(DB_FILE):
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_inventario_{fecha}.db"
        import shutil
        shutil.copy2(DB_FILE, backup_name)
        return True
    return False

def obtener_metricas():
    """Obtiene métricas del sistema"""
    df_inv = run_query("SELECT * FROM inventario")
    df_sis = run_query("SELECT * FROM sistema")
    df_prov = run_query("SELECT * FROM proveedores")
    df_ord = run_query("SELECT * FROM ordenes_pedido WHERE estado = 'pendiente'")
    
    # Stock bajo
    stock_bajo_inv = df_inv[df_inv['cantidad'] < df_inv['cantidad_minima']]
    stock_bajo_sis = df_sis[df_sis['cantidad'] < df_sis['cantidad_minima']]
    
    # Valor total inventario
    valor_inv = (df_inv['cantidad'] * df_inv['costo_unitario']).sum()
    valor_sis = (df_sis['cantidad'] * df_sis['costo_unitario']).sum()
    
    return {
        'total_insumos': len(df_inv),
        'total_sistemas': len(df_sis),
        'total_proveedores': len(df_prov),
        'pendientes': len(df_ord),
        'stock_bajo_inv': len(stock_bajo_inv),
        'stock_bajo_sis': len(stock_bajo_sis),
        'valor_total': valor_inv + valor_sis
    }

def add_to_historial(accion, descripcion, usuario):
    """Agrega entrada al historial"""
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execute_query("INSERT INTO historial (fecha, accion, descripcion, usuario) VALUES (?, ?, ?, ?)",
                  (fecha, accion, descripcion, usuario))

def mostrar_mensaje(mensaje, tipo='success'):
    """Muestra mensaje temporal"""
    if tipo == 'success':
        placeholder = st.empty()
        placeholder.success(mensaje)
        time.sleep(3)
        placeholder.empty()
    elif tipo == 'error':
        placeholder = st.empty()
        placeholder.error(mensaje)
        time.sleep(3)
        placeholder.empty()
    elif tipo == 'warning':
        placeholder = st.empty()
        placeholder.warning(mensaje)
        time.sleep(3)
        placeholder.empty()

# ============================================
# GESTIÓN DE SESIÓN
# ============================================
if 'sesion_iniciada' not in st.session_state:
    st.session_state.sesion_iniciada = False
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None
if 'rol_usuario' not in st.session_state:
    st.session_state.rol_usuario = None

def cerrar_sesion():
    st.session_state.sesion_iniciada = False
    st.session_state.usuario_actual = None
    st.session_state.rol_usuario = None
    st.rerun()

# ============================================
# PÁGINA DE LOGIN
# ============================================
def pagina_login():
    """Página de inicio de sesión"""
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h1 style='font-size: 60px;'>📦</h1>
        <h2 style='color: #00d4ff;'>Gestión de Inventarios TQ</h2>
        <p style='color: #888;'>Ingrese sus credenciales para continuar</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("form_login"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("🚀 Iniciar Sesión", use_container_width=True)
            
            if submit:
                usuario_verificado = verificar_usuario(usuario, password)
                if usuario_verificado is not None:
                    st.session_state.sesion_iniciada = True
                    st.session_state.usuario_actual = usuario_verificado['username']
                    st.session_state.rol_usuario = usuario_verificado['rol']
                    add_to_historial("LOGIN", f"Usuario {usuario} inició sesión", usuario)
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")
        
        st.markdown("---")
        st.info("💡 Credenciales por defecto: admin / TQ2026")

# ============================================
# DASHBOARD PRINCIPAL
# ============================================
def mostrar_dashboard():
    """Muestra el dashboard principal"""
    metricas = obtener_metricas()
    
    st.header("📊 Panel de Control en Tiempo Real")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Total Insumos", metricas['total_insumos'])
    col2.metric("⚙️ Total Sistemas", metricas['total_sistemas'])
    col3.metric("🚚 Proveedores", metricas['total_proveedores'])
    col4.metric("💰 Valor Inventario", f"${metricas['valor_total']:,.2f}")
    
    st.markdown("---")
    
    # Alertas de stock bajo
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("⚠️ Alerta: Insumos Stock Bajo")
        df = run_query("SELECT * FROM inventario")
        if not df.empty:
            stock_bajo = df[df['cantidad'] < df['cantidad_minima']]
            if not stock_bajo.empty:
                st.error(f"¡Tienes {len(stock_bajo)} insumos con stock crítico!")
                st.dataframe(stock_bajo[['id', 'tipo_insumo', 'modelo', 'cantidad', 'cantidad_minima', 'proveedor']].set_index('id'), 
                           use_container_width=True)
            else:
                st.success("✅ Inventario en niveles óptimos")
    
    with c2:
        st.subheader("⚠️ Alerta: Sistemas Stock Bajo")
        df_sis = run_query("SELECT * FROM sistema")
        if not df_sis.empty:
            stock_bajo_sis = df_sis[df_sis['cantidad'] < df_sis['cantidad_minima']]
            if not stock_bajo_sis.empty:
                st.warning(f"¡Tienes {len(stock_bajo_sis)} sistemas con stock crítico!")
                st.dataframe(stock_bajo_sis[['id', 'nombre', 'modelo', 'cantidad', 'cantidad_minima']].set_index('id'),
                           use_container_width=True)
            else:
                st.success("✅ Sistemas en niveles óptimos")
    
    st.markdown("---")
    
    # Órdenes pendientes
    st.subheader("📋 Órdenes de Pedido Pendientes")
    df_ord = run_query("SELECT * FROM ordenes_pedido WHERE estado = 'pendiente'")
    if not df_ord.empty:
        st.info(f"Tienes {len(df_ord)} órdenes pendientes de atención")
        st.dataframe(df_ord.set_index('id'), use_container_width=True)
    else:
        st.success("✅ No hay órdenes pendientes")
    
    st.markdown("---")
    
    # Vista general
    st.subheader("📋 Vista General del Inventario")
    df = run_query("SELECT * FROM inventario")
    if not df.empty:
        # Opción de búsqueda rápida
        Buscar = st.text_input("🔍 Búsqueda rápida:", placeholder="Buscar en inventario...")
        if Buscar:
            df_filtrado = df[df['tipo_insumo'].str.contains(Buscar, case=False, na=False) | 
                           df['modelo'].str.contains(Buscar, case=False, na=False)]
            st.dataframe(df_filtrado.set_index('id'), use_container_width=True)
        else:
            st.dataframe(df.set_index('id'), use_container_width=True)
    
    st.markdown("---")
    
    # Gráficos estadísticos
    st.subheader("📈 Estadísticas del Inventario")
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        # Top 10 insumos por cantidad
        df = run_query("SELECT tipo_insumo, cantidad FROM inventario ORDER BY cantidad DESC LIMIT 10")
        if not df.empty:
            st.bar_chart(data=df.set_index('tipo_insumo'), use_container_width=True)
    
    with col_g2:
        # Distribución por equipo
        df = run_query("SELECT equipo, COUNT(*) as total FROM inventario GROUP BY equipo")
        if not df.empty:
            st.bar_chart(data=df.set_index('equipo'), use_container_width=True)

# ============================================
# AGREGAR INSUMO
# ============================================
def pagina_agregar_insumo():
    """Página para agregar nuevo insumo"""
    st.header("➕ Agregar Nuevo Insumo")
    
    with st.form("form_agregar"):
        col1, col2 = st.columns(2)
        with col1:
            tipo = st.text_input("Tipo de Insumo *")
            modelo = st.text_input("Modelo")
            medidas = st.text_input("Medidas")
            eficiencia = st.text_input("Eficiencia")
        
        with col2:
            equipo = st.text_input("Equipo")
            cantidad = st.number_input("Cantidad Actual *", min_value=0, step=1, value=0)
            cantidad_min = st.number_input("Stock Mínimo", min_value=0, step=1, value=5)
        
        col3, col4 = st.columns(2)
        with col3:
            proveedor = st.text_input("Proveedor")
            costo = st.number_input("Costo Unitario ($)", min_value=0.0, step=0.01, value=0.0)
        
        with col4:
            realizado_por = st.text_input("Registrado por")
            observaciones = st.text_area("Observaciones")
        
        submit = st.form_submit_button("💾 Guardar Insumo", use_container_width=True)
        
        if submit and tipo:
            try:
                fecha_actual = datetime.now().strftime("%Y-%m-%d")
                execute_query("""INSERT INTO inventario 
                    (tipo_insumo, medidas, eficiencia, modelo, equipo, cantidad, cantidad_minima, 
                     proveedor, costo
