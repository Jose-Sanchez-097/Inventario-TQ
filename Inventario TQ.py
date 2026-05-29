import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
import hashlib
from io import BytesIO

# ============================================
# CONFIGURACIÓN
# ============================================
st.set_page_config(page_title="📦 Gestión de Inventarios TQ", page_icon="📦", layout="wide", initial_sidebar_state="expanded")

DB_FILE = 'inventario.db'

# ============================================
# CSS PERSONALIZADO
# ============================================
st.markdown("""
<style>
    h1,h2,h3{color:#00d4ff!important}
    div[data-testid="stMetric"]{background:linear-gradient(135deg,#667eea,#764ba2);padding:15px;border-radius:10px}
    .stButton>button{background:linear-gradient(135deg,#667eea,#764ba2);border:none;border-radius:8px;color:white}
</style>
""", unsafe_allow_html=True)

# ============================================
# BASE DE DATOS
# ============================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Tabla inventario
    c.execute('''CREATE TABLE IF NOT EXISTS inventario (
        id INTEGER PRIMARY KEY AUTOINCREMENT, tipo_insumo TEXT NOT NULL, medidas TEXT,
        eficiencia TEXT, modelo TEXT, equipo TEXT, cantidad INTEGER DEFAULT 0,
        cantidad_minima INTEGER DEFAULT 5, proveedor TEXT, costo_unitario REAL DEFAULT 0,
        realizado_por TEXT, observaciones TEXT, fecha_actualizacion TEXT, fecha_creacion TEXT)''')
    # Tabla sistema
    c.execute('''CREATE TABLE IF NOT EXISTS sistema (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, tipo_filtro TEXT,
        modelo TEXT, eficiencia TEXT, medidas TEXT, cantidad INTEGER DEFAULT 0,
        cantidad_minima INTEGER DEFAULT 5, costo_unitario REAL DEFAULT 0,
        fecha_actualizacion TEXT, fecha_creacion TEXT)''')
    # Tabla historial
    c.execute('''CREATE TABLE IF NOT EXISTS historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, accion TEXT, descripcion TEXT, usuario TEXT)''')
    # Tabla usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL, rol TEXT DEFAULT 'usuario', fecha_creacion TEXT)''')
    # Tabla proveedores
    c.execute('''CREATE TABLE IF NOT EXISTS proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, contacto TEXT,
        telefono TEXT, email TEXT, observaciones TEXT, fecha_actualizacion TEXT)''')
    # Tabla ordenes
    c.execute('''CREATE TABLE IF NOT EXISTS ordenes_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT, orden_numero TEXT UNIQUE NOT NULL,
        insumo_id INTEGER, cantidad_solicitada INTEGER, proveedor TEXT, estado TEXT DEFAULT 'pendiente',
        fecha_solicitud TEXT, observaciones TEXT, usuario_solicita TEXT)''')
    # Admin por defecto
    c.execute("SELECT id FROM usuarios WHERE username = 'admin'")
    if not c.fetchone():
        password_admin = hashlib.sha256('TQ2026'.encode()).hexdigest()
        c.execute("INSERT INTO usuarios (username, password, rol, fecha_creacion) VALUES (?, ?, ?, ?)",
                 ('admin', password_admin, 'administrador', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
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

def get_inventario():
    return run_query("SELECT * FROM inventario")

def get_sistema():
    return run_query("SELECT * FROM sistema")

def get_proveedores():
    return run_query("SELECT * FROM proveedores")

def get_historial():
    return run_query("SELECT * FROM historial ORDER BY fecha DESC")

def get_ordenes():
    return run_query("SELECT * FROM ordenes_pedido ORDER BY fecha_solicitud DESC")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_usuario(username, password):
    password_hash = hash_password(password)
    df = run_query("SELECT id, username, rol FROM usuarios WHERE username = ? AND password = ?",
                  (username, password_hash))
    return df.iloc[0] if not df.empty else None

def obtener_metricas():
    df_inv = get_inventario()
    df_sis = get_sistema()
    df_prov = get_proveedores()
    df_ord = run_query("SELECT * FROM ordenes_pedido WHERE estado = 'pendiente'")
    stock_bajo_inv = df_inv[df_inv['cantidad'] < df_inv['cantidad_minima']]
    valor_total = (df_inv['cantidad'] * df_inv['costo_unitario']).sum() + (df_sis['cantidad'] * df_sis['costo_unitario']).sum()
    return {
        'total_insumos': len(df_inv),
        'total_sistemas': len(df_sis),
        'total_proveedores': len(df_prov),
        'pendientes': len(df_ord),
        'stock_bajo_inv': len(stock_bajo_inv),
        'valor_total': valor_total
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
    time.sleep(2)

def generar_excel(df, filename):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=filename)
    return output.getvalue()

# ============================================
# SESIÓN
# ============================================
if 'sesion_iniciada' not in st.session_state:
    st.session_state.sesion_iniciada = False
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None

def cerrar_sesion():
    st.session_state.sesion_iniciada = False
    st.session_state.usuario_actual = None
    st.rerun()

init_db()

# ============================================
# PAGINA LOGIN
# ============================================
def pagina_login():
    st.markdown("""
    <div style='text-align:center;padding:50px;'>
        <h1 style='font-size:60px;'>📦</h1>
        <h2 style='color:#00d4ff;'>Gestión de Inventarios TQ</h2>
        <p style='color:#888;'>Ingrese sus credenciales</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
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
                    add_to_historial("LOGIN", f"Usuario {usuario} inició sesión", usuario)
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")
        st.info("💡 Credenciales: admin / TQ2026")

# ============================================
# DASHBOARD
# ============================================
def mostrar_dashboard():
    metricas = obtener_metricas()
    st.header("📊 Panel de Control en Tiempo Real")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Total Insumos", metricas['total_insumos'])
    col2.metric("⚙️ Total Sistemas", metricas['total_sistemas'])
    col3.metric("🚚 Proveedores", metricas['total_proveedores'])
    col4.metric("💰 Valor Inventario", f"${metricas['valor_total']:,.0f}")
    
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("⚠️ Alerta: Insumos Stock Bajo")
        df = get_inventario()
        if not df.empty:
            stock_bajo = df[df['cantidad'] < df['cantidad_minima']]
            if not stock_bajo.empty:
                st.error(f"¡Tienes {len(stock_bajo)} insumos con stock crítico!")
                st.dataframe(stock_bajo[['tipo_insumo','modelo','cantidad','cantidad_minima','proveedor']])
            else:
                st.success("✅ Inventario en niveles óptimos")
    
    with c2:
        st.subheader("⚠️ Alerta: Sistemas Stock Bajo")
        df_sis = get_sistema()
        if not df_sis.empty:
            stock_bajo_sis = df_sis[df_sis['cantidad'] < df_sis['cantidad_minima']]
            if not stock_bajo_sis.empty:
                st.warning(f"¡Tienes {len(stock_bajo_sis)} sistemas con stock crítico!")
                st.dataframe(stock_bajo_sis[['nombre','modelo','cantidad','cantidad_minima']])
            else:
                st.success("✅ Sistemas en niveles óptimos")
    
    st.markdown("---")
    
    st.subheader("📋 Vista General del Inventario")
    df = get_inventario()
    buscar = st.text_input("🔍 Búsqueda rápida:", placeholder="Buscar en inventario...")
    if buscar:
        df_filtrado = df[df['tipo_insumo'].str.contains(buscar, case=False, na=False) | 
                       df['modelo'].str.contains(buscar, case=False, na=False)]
        st.dataframe(df_filtrado)
    else:
        st.dataframe(df)
    
    # Gráficos
    st.subheader("📈 Estadísticas del Inventario")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        df = run_query("SELECT tipo_insumo, cantidad FROM inventario ORDER BY cantidad DESC LIMIT 10")
        if not df.empty:
            st.bar_chart(df.set_index('tipo_insumo'))
    with col_g2:
        df = run_query("SELECT equipo, COUNT(*) as total FROM inventario GROUP BY equipo")
        if not df.empty:
            st.bar_chart(df.set_index('equipo'))

# ============================================
# AGREGAR INSUMO
# ============================================
def pagina_agregar_insumo():
    st.header("➕ Agregar Nuevo Insumo")
    with st.form("form_agregar"):
        c1, c2 = st.columns(2)
        with c1:
            tipo = st.text_input("Tipo de Insumo *")
            modelo = st.text_input("Modelo")
            medidas = st.text_input("Medidas")
            eficiencia = st.text_input("Eficiencia")
        with c2:
            equipo = st.text_input("Equipo")
            cantidad = st.number_input("Cantidad Actual *", min_value=0, step=1, value=0)
            cantidad_min = st.number_input("Stock Mínimo *", min_value=0, step=1, value=5)
        c3, c4 = st.columns(2)
        with c3:
            proveedor = st.text_input("Proveedor")
            costo = st.number_input("Costo Unitario ($)", min_value=0.0, step=0.01, value=0.0)
        with c4:
            realizado_por = st.text_input("Realizado por")
            observaciones = st.text_area("Observaciones")
        submit = st.form_submit_button("💾 Guardar Insumo", use_container_width=True)
        if submit and tipo:
            fecha = datetime.now().strftime("%Y-%m-%d")
            execute_query('''INSERT INTO inventario 
                (tipo_insumo,medidas,eficiencia,modelo,equipo,cantidad,cantidad_minima,proveedor,costo_unitario,realizado_por,observaciones,fecha_actualizacion,fecha_creacion)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (tipo,medidas,eficiencia,modelo,equipo,cantidad,cantidad_min,proveedor,costo,realizado_por,observaciones,fecha,fecha))
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
        seleccion = st.selectbox("Seleccione Insumo a Modificar", opciones)
        if seleccion:
            item_id = int(seleccion.split(" - ")[0])
            item = df[df['id'] == item_id].iloc[0]
            with st.form("form_modificar"):
                c1, c2 = st.columns(2)
                with c1:
                    tipo = st.text_input("Tipo de Insumo", value=item['tipo_insumo'])
                    modelo = st.text_input("Modelo", value=item['modelo'])
                    medidas = st.text_input("Medidas", value=item['medidas'])
                with c2:
                    equipo = st.text_input("Equipo", value=item['equipo'])
                    cantidad = st.number_input("Cantidad", min_value=0, value=int(item['cantidad']))
                    cantidad_min = st.number_input("Stock Mínimo", min_value=0, value=int(item['cantidad_minima']))
                c3, c4 = st.column(2)
                with c3:
                    proveedor = st.text_input("Proveedor", value=item['proveedor'])
                    costo = st.number_input("Costo", min_value=0.0, value=float(item['costo_unitario']))
                with c4:
                    observaciones = st.text_area("Observaciones", value=item['observaciones'])
                submit = st.form_submit_button("✏️ Actualizar", use_container_width=True)
                if submit:
                    fecha = datetime.now().strftime("%Y-%m-%d")
                    execute_query('''UPDATE inventario SET 
                        tipo_insumo=?,medidas=?,modelo=?,equipo=?,cantidad=?,cantidad_minima=?,
                        proveedor=?,costo_unitario=?,observaciones=?,fecha_actualizacion=? WHERE id=?''',
                        (tipo,medidas,modelo,equipo,cantidad,cantidad_min,proveedor,costo,observaciones,fecha,item_id))
                    add_to_historial("MODIFICAR INSUMO", f"ID: {item_id} | Nuevo: {tipo}", st.session_state.usuario_actual)
                    mostrar_mensaje("✅ Insumo actualizado exitosamente!")
                    st.rerun()

# ============================================
# ELIMINAR INSUMO
# ============================================
def pagina_eliminar_insumo():
    st.header("🗑️ Eliminar Insumo")
    df = get_inventario()
    if df.empty:
        st.info("Inventario vacío.")
    else:
        opciones = df.apply(lambda x: f"{x['id']} - {x['tipo_insumo']}", axis=1).tolist()
        seleccion = st.selectbox("Seleccione Insumo a Eliminar", opciones)
        passwd = st.text_input("Ingrese Contraseña para Confirmar", type="password")
        if st.button("🗑️ Eliminar Definitivamente"):
            if passwd == "TQ2026":
                item_id = int(seleccion.split(" - ")[0])
                nombre = df[df['id'] == item_id]['tipo_insumo'].values[0]
                execute_query("DELETE FROM inventario WHERE id=?", (item_id,))
                add_to_historial("ELIMINAR INSUMO", f"Insumo: {nombre}", st.session_state.usuario_actual)
                mostrar_mensaje("✅ Insumo eliminado!")
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")

# ============================================
# BUSCAR INSUMO
# ============================================
def pagina_buscar_insumo():
    st.header("🔍 Buscar Insumo en Inventario")
    df = get_inventario()
    if df.empty:
        st.info("No hay insumos registrados.")
    else:
        campo_busqueda = st.selectbox("Campo:", ["tipo_insumo","modelo","equipo","medidas","proveedor"])
        texto_busqueda = st.text_input("Buscar:", placeholder="Ingrese texto...")
        if texto_busqueda:
            resultado = df[df[campo_busqueda].str.contains(texto_busqueda, case=False, na=False)]
            if not resultado.empty:
                st.success(f"✅ {len(resultado)} resultado(s)")
                add_to_historial("BUSCAR INSUMO", f"Busqueda: {texto_busqueda}", st.session_state.usuario_actual)
                st.dataframe(resultado
