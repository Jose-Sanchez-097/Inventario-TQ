import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
import os
import hashlib
from io import BytesIO
import shutil

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
    .main {
        background-color: #0e1117;
    }
    h1, h2, h3 {
        color: #00d4ff !important;
        font-weight: bold;
    }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 10px;
        color: white;
        font-weight: bold;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(to bottom, #1a1a2e, #0e1117);
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================
DB_FILE = 'inventario.db'

def init_db():
    """Inicializa la base de datos"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Tabla de inventario
    c.execute('''CREATE TABLE IF NOT EXISTS inventario (
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
        fecha_creacion TEXT)''')
    
    # Tabla de sistemas
    c.execute('''CREATE TABLE IF NOT EXISTS sistema (
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
        fecha_creacion TEXT)''')
    
    # Tabla de historial
    c.execute('''CREATE TABLE IF NOT EXISTS historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        accion TEXT,
        descripcion TEXT,
        usuario TEXT)''')
    
    # Tabla de usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        rol TEXT DEFAULT 'usuario',
        fecha_creacion TEXT)''')
    
    # Tabla de proveedores
    c.execute('''CREATE TABLE IF NOT EXISTS proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        contacto TEXT,
        telefono TEXT,
        email TEXT,
        direccion TEXT,
        observaciones TEXT,
        fecha_actualizacion TEXT)''')
    
    # Tabla de órdenes
    c.execute('''CREATE TABLE IF NOT EXISTS ordenes_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_numero TEXT UNIQUE NOT NULL,
        insumo_id INTEGER,
        cantidad_solicitada INTEGER,
        proveedor TEXT,
        estado TEXT DEFAULT 'pendiente',
        fecha_solicitud TEXT,
        fecha_entrega TEXT,
        observaciones TEXT,
        usuario_solicita TEXT)''')
    
    # Crear admin si no existe
    c.execute("SELECT id FROM usuarios WHERE username = 'admin'")
    if not c.fetchone():
        password_admin = hashlib.sha256('TQ2026'.encode()).hexdigest()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO usuarios (username, password, rol, fecha_creacion) VALUES (?, ?, ?, ?)",
                  ('admin', password_admin, 'administrador', fecha))
    
    conn.commit()
    conn.close()

# ============================================
# FUNCIONES DE BASE DE DATOS
# ============================================
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

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_usuario(username, password):
    password_hash = hash_password(password)
    df = run_query("SELECT id, username, rol FROM usuarios WHERE username = ? AND password = ?", 
                  (username, password_hash))
    return df.iloc[0] if not df.empty else None

def crear_backup():
    if os.path.exists(DB_FILE):
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(DB_FILE, f"backup_inventario_{fecha}.db")
        return True
    return False

def obtener_metricas():
    df_inv = run_query("SELECT * FROM inventario")
    df_sis = run_query("SELECT * FROM sistema")
    df_prov = run_query("SELECT * FROM proveedores")
    df_ord = run_query("SELECT * FROM ordenes_pedido WHERE estado = 'pendiente'")
    
    stock_bajo_inv = df_inv[df_inv['cantidad'] < df_inv['cantidad_minima']]
    valor_inv = (df_inv['cantidad'] * df_inv['costo_unitario']).sum()
    valor_sis = (df_sis['cantidad'] * df_sis['costo_unitario']).sum()
    
    return {
        'total_insumos': len(df_inv),
        'total_sistemas': len(df_sis),
        'total_proveedores': len(df_prov),
        'pendientes': len(df_ord),
        'stock_bajo_inv': len(stock_bajo_inv),
        'valor_total': valor_inv + valor_sis
    }

def add_to_historial(accion, descripcion, usuario):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execute_query("INSERT INTO historial (fecha, accion, descripcion, usuario) VALUES (?, ?, ?, ?)",
                  (fecha, accion, descripcion, usuario))

def mostrar_mensaje(mensaje, tipo='success'):
    if tipo == 'success':
        st.success(mensaje)
    elif tipo == 'error':
        st.error(mensaje)
    elif tipo == 'warning':
        st.warning(mensaje)
    time.sleep(3)

def generar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventario')
    return output.getvalue()

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

def importar_excel():
    uploaded_file = st.file_uploader("Importar desde Excel", type=['xlsx', 'xls'])
    if uploaded_file is not None:
        try:
            df_nuevo = pd.read_excel(uploaded_file)
            for _, row in df_nuevo.iterrows():
                execute_query('''INSERT INTO inventario 
                    (tipo_insumo, medidas, eficiencia, modelo, equipo, cantidad, cantidad_minima, 
                     proveedor, costo_unitario, realizado_por, observaciones, fecha_actualizacion, fecha_creacion)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (row.get('tipo_insumo', ''), row.get('medidas', ''), row.get('eficiencia', ''),
                     row.get('modelo', ''), row.get('equipo', ''), row.get('cantidad', 0),
                     row.get('cantidad_minima', 5), row.get('proveedor', ''), row.get('costo_unitario', 0),
                     row.get('realizado_por', ''), row.get('observaciones', ''),
                     datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%Y-%m-%d")))
            mostrar_mensaje("✅ Datos importados correctamente", 'success')
            st.rerun()
        except Exception as e:
            st.error(f"Error al importar: {e}")

# ============================================
# PÁGINA DE LOGIN
# ============================================
def pagina_login():
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h1 style='font-size: 60px;'>📦</h1>
        <h2 style='color: #00d4ff;'>Gestión de Inventarios TQ</h2>
        <p style='color: #888;'>Ingrese sus credenciales</p>
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
        
        st.info("💡 Credenciales por defecto: admin / TQ2026")

# ============================================
# DASHBOARD PRINCIPAL
# ============================================
def mostrar_dashboard():
    metricas = obtener_metricas()
    
    st.header("📊 Panel de Control en Tiempo Real")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Total Insumos", metricas['total_insumos'])
    col2.metric("⚙️ Total Sistemas", metricas['total_sistemas'])
    col3.metric("🚚 Proveedores", metricas['total_proveedores'])
    col4.metric("💰 Valor Inventario", f"${metricas['valor_total']:,.2f}")
    
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("⚠️ Insumos con Stock Bajo")
        df = run_query("SELECT * FROM inventario")
        if not df.empty:
            stock_bajo = df[df['cantidad'] < df['cantidad_minima']]
            if not stock_bajo.empty:
                st.error(f"¡Tienes {len(stock_bajo)} insumos con stock crítico!")
                st.dataframe(stock_bajo[['id', 'tipo_insumo', 'modelo', 'cantidad', 'cantidad_minima', 'proveedor']].set_index('id'))
            else:
                st.success("✅ Inventario en niveles óptimos")
    
    with c2:
        st.subheader("⚠️ Sistemas con Stock Bajo")
        df_sis = run_query("SELECT * FROM sistema")
        if not df_sis.empty:
            stock_bajo_sis = df_sis[df_sis['cantidad'] < df_sis['cantidad_minima']]
            if not stock_bajo_sis.empty:
                st.warning(f"¡Tienes {len(stock_bajo_sis)} sistemas con stock crítico!")
                st.dataframe(stock_bajo_sis[['id', 'nombre', 'modelo', 'cantidad', 'cantidad_minima']].set_index('id'))
            else:
                st.success("✅ Sistemas en niveles óptimos")
    
    st.markdown("---")
    
    st.subheader("📋 Vista General del Inventario")
    df = run_query("SELECT * FROM inventario")
    if not df.empty:
        buscar = st.text_input("🔍 Búsqueda rápida:", placeholder="Buscar...")
        if buscar:
            df_filtrado = df[df['tipo_insumo'].str.contains(buscar, case=False, na=False) | 
                           df['modelo'].str.contains(buscar, case=False, na=False)]
            st.dataframe(df_filtrado.set_index('id'))
        else:
            st.dataframe(df.set_index('id'))
    
    # Gráficos
    st.subheader("📈 Estadísticas")
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        df = run_query("SELECT tipo_insumo, cantidad FROM inventario ORDER BY cantidad DESC LIMIT 10")
        if not df.empty:
            st.bar_chart(data=df.set_index('tipo_insumo'))
    
    with col_g2:
        df = run_query("SELECT equipo, COUNT(*) as total FROM inventario GROUP BY equipo")
        if not df.empty:
            st.bar_chart(data=df.set_index('equipo'))

# ============================================
# AGREGAR INSUMO
# ============================================
def pagina_agregar_insumo():
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
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            execute_query('''INSERT INTO inventario 
                (tipo_insumo, medidas, eficiencia, modelo, equipo, cantidad, cantidad_minima, 
                 proveedor, costo_unitario, realizado_por, observaciones, fecha_actualizacion, fecha_creacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (tipo, medidas, eficiencia, modelo, equipo, cantidad, cantidad_min,
                 proveedor, costo, realizado_por, observaciones, fecha_actual, fecha_actual))
            
            add_to_historial("AGREGAR INSUMO", f"Insumo: {tipo} | Cantidad: {cantidad}", st.session_state.usuario_actual)
            mostrar_mensaje("✅ Insumo agregado exitosamente!")
            st.rerun()
        elif submit:
            st.warning("Complete los campos obligatorios (*)")

# ============================================
# MODIFICAR INSUMO
# ============================================
def pagina_modificar_insumo():
    st.header("✏️ Modificar Insumo Existente")
    df = get_inventario()
    
    if df.empty:
        st.info("No hay insumos para modificar.")
    else:
        opciones = df.apply(lambda x: f"{x['id']} - {x['tipo_insumo']}", axis=1).tolist()
        seleccion = st.selectbox("Seleccione Insumo", opciones)
        
        if seleccion:
            item_id = int(seleccion.split(" - ")[0])
            item = df[df['id'] == item_id].iloc[0]
            
            with st.form("form_modificar"):
                col1, col2 = st.columns(2)
                with col1:
                    tipo = st.text_input("Tipo de Insumo", value=item['tipo_insumo'])
                    modelo = st.text_input("Modelo", value=item['modelo'])
                    medidas = st.text_input("Medidas", value=item['medidas'])
                    eficiencia = st.text_input("Eficiencia", value=item['eficiencia'])
                
                with col2:
                    equipo = st.text_input("Equipo", value=item['equipo'])
                    cantidad = st.number_input("Cantidad", min_value=0, value=int(item['cantidad']))
                    cantidad_min = st.number_input("Stock Mínimo", min_value=0, value=int(item['cantidad_minima']))
                
                col3, col4 = st.columns(2)
                with col3:
                    proveedor = st.text_input("Proveedor", value=item['proveedor'])
                    costo = st.number_input
