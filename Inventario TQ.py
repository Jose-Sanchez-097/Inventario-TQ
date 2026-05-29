import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
import os
import hashlib
from io import BytesIO
import shutil

st.set_page_config(page_title="📦 Gestión de Inventarios TQ", page_icon="📦", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>h1,h2,h3{color:#00d4ff!important}div[data-testid="stMetric"]{background:linear-gradient(135deg,#667eea,#764ba2);padding:20px;border-radius:15px}.stButton>button{background:linear-gradient(135deg,#667eea,#764ba2);border:none;border-radius:10px;color:white;font-weight:bold}</style>""", unsafe_allow_html=True)

DB_FILE = 'inventario.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inventario (id INTEGER PRIMARY KEY AUTOINCREMENT, tipo_insumo TEXT NOT NULL, medidas TEXT, eficiencia TEXT, modelo TEXT, equipo TEXT, cantidad INTEGER DEFAULT 0, cantidad_minima INTEGER DEFAULT 5, proveedor TEXT, costo_unitario REAL DEFAULT 0, realizado_por TEXT, observaciones TEXT, fecha_actualizacion TEXT, fecha_creacion TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sistema (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, tipo_filtro TEXT, modelo TEXT, eficiencia TEXT, medidas TEXT, cantidad INTEGER DEFAULT 0, cantidad_minima INTEGER DEFAULT 5, costo_unitario REAL DEFAULT 0, fecha_actualizacion TEXT, fecha_creacion TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS historial (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, accion TEXT, descripcion TEXT, usuario TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, rol TEXT DEFAULT 'usuario', fecha_creacion TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS proveedores (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, contacto TEXT, telefono TEXT, email TEXT, direccion TEXT, observaciones TEXT, fecha_actualizacion TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ordenes_pedido (id INTEGER PRIMARY KEY AUTOINCREMENT, orden_numero TEXT UNIQUE NOT NULL, insumo_id INTEGER, cantidad_solicitada INTEGER, proveedor TEXT, estado TEXT DEFAULT 'pendiente', fecha_solicitud TEXT, fecha_entrega TEXT, observaciones TEXT, usuario_solicita TEXT)''')
    c.execute("SELECT id FROM usuarios WHERE username = 'admin'")
    if not c.fetchone():
        password_admin = hashlib.sha256('TQ2026'.encode()).hexdigest()
        c.execute("INSERT INTO usuarios (username, password, rol, fecha_creacion) VALUES (?, ?, ?, ?)", ('admin', password_admin, 'administrador', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
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

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_usuario(username, password):
    password_hash = hash_password(password)
    df = run_query("SELECT id, username, rol FROM usuarios WHERE username = ? AND password = ?", (username, password_hash))
    return df.iloc[0] if not df.empty else None

def obtener_metricas():
    df_inv = run_query("SELECT * FROM inventario")
    df_sis = run_query("SELECT * FROM sistema")
    df_prov = run_query("SELECT * FROM proveedores")
    df_ord = run_query("SELECT * FROM ordenes_pedido WHERE estado = 'pendiente'")
    stock_bajo_inv = df_inv[df_inv['cantidad'] < df_inv['cantidad_minima']]
    valor_total = (df_inv['cantidad'] * df_inv['costo_unitario']).sum() + (df_sis['cantidad'] * df_sis['costo_unitario']).sum()
    return {'total_insumos': len(df_inv), 'total_sistemas': len(df_sis), 'total_proveedores': len(df_prov), 'pendientes': len(df_ord), 'stock_bajo_inv': len(stock_bajo_inv), 'valor_total': valor_total}

def add_to_historial(accion, descripcion, usuario):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execute_query("INSERT INTO historial (fecha, accion, descripcion, usuario) VALUES (?, ?, ?, ?)", (fecha, accion, descripcion, usuario))

def mostrar_mensaje(mensaje, tipo='success'):
    if tipo == 'success': st.success(mensaje)
    elif tipo == 'error': st.error(mensaje)
    elif tipo == 'warning': st.warning(mensaje)
    time.sleep(3)

def generar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventario')
    return output.getvalue()

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
    st.markdown("""<div style='text-align:center;padding:50px;'><h1 style='font-size:60px;'>📦</h1><h2 style='color:#00d4ff;'>Gestión de Inventarios TQ</h2><p style='color:#888;'>Ingrese sus credenciales</p></div>""", unsafe_allow_html=True)
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

def mostrar_dashboard():
    metricas = obtener_metricas()
    st.header("📊 Panel de Control")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Insumos", metricas['total_insumos'])
    col2.metric("⚙️ Sistemas", metricas['total_sistemas'])
    col3.metric("🚚 Proveedores", metricas['total_proveedores'])
    col4.metric("💰 Valor", f"${metricas['valor_total']:,.0f}")
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("⚠️ Stock Bajo - Insumos")
        df = get_inventario()
        if not df.empty:
            stock_bajo = df[df['cantidad'] < df['cantidad_minima']]
            if not stock_bajo.empty:
                st.error(f"¡{len(stock_bajo)} insumos críticos!")
                st.dataframe(stock_bajo[['tipo_insumo','modelo','cantidad','cantidad_minima','proveedor']])
            else:
                st.success("✅ Niveles óptimos")
    with c2:
        st.subheader("⚠️ Stock Bajo - Sistemas")
        df_sis = get_sistema()
        if not df_sis.empty:
            stock_bajo_sis = df_sis[df_sis['cantidad'] < df_sis['cantidad_minima']]
            if not stock_bajo_sis.empty:
                st.warning(f"¡{len(stock_bajo_sis)} sistemas críticos!")
                st.dataframe(stock_bajo_sis[['nombre','modelo','cantidad','cantidad_minima']])
            else:
                st.success("✅ Niveles óptimos")
    st.markdown("---")
    st.subheader("📋 Inventario Completo")
    df = get_inventario()
    buscar = st.text_input("🔍 Buscar:", placeholder="Buscar en inventario...")
    if buscar:
        df_filtrado = df[df['tipo_insumo'].str.contains(buscar, case=False, na=False) | df['modelo'].str.contains(buscar, case=False, na=False)]
        st.dataframe(df_filtrado)
    else:
        st.dataframe(df)
    # Gráficos
    st.subheader("📈 Estadísticas")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        df = run_query("SELECT tipo_insumo, cantidad FROM inventario ORDER BY cantidad DESC LIMIT 10")
        if not df.empty:
            st.bar_chart(df.set_index('tipo_insumo'))
    with col_g2:
        df = run_query("SELECT equipo, COUNT(*) as total FROM inventario GROUP BY equipo")
        if not df.empty:
            st.bar_chart(df.set_index('equipo'))

def pagina_agregar_insumo():
    st.header("➕ Agregar Insumo")
    with st.form("form_agregar"):
        c1, c2 = st.columns(2)
        with c1:
            tipo = st.text_input("Tipo *")
            modelo = st.text_input("Modelo")
            medidas = st.text_input("Medidas")
            eficiencia = st.text_input("Eficiencia")
        with c2:
            equipo = st.text_input("Equipo")
            cantidad = st.number_input("Cantidad *", min_value=0, step=1, value=0)
            cantidad_min = st.number_input("Stock Mínimo", min_value=0, step=1, value=5)
        c3, c4 = st.columns(2)
        with c3:
            proveedor = st.text_input("Proveedor")
            costo = st.number_input("Costo Unitario", min_value=0.0, step=0.01, value=0.0)
        with c4:
            realizado_por = st.text_input("Registrado por")
            observaciones = st.text_area("Observaciones")
        submit = st.form_submit_button("💾 Guardar", use_container_width=True)
        if submit and tipo:
            fecha = datetime.now().strftime("%Y-%m-%d")
            execute_query('''INSERT INTO inventario (tipo_insumo,medidas,eficiencia,modelo,equipo,cantidad,cantidad_minima,proveedor,costo_unitario,realizado_por,observaciones,fecha_actualizacion,fecha_creacion) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (tipo,medidas,eficiencia,modelo,equipo,cantidad,cantidad_min,proveedor,costo,realizado_por,observaciones,fecha,fecha))
            add_to_historial("AGREGAR", f"Insumo: {tipo}", st.session_state.usuario_actual)
            mostrar_mensaje("✅ Agregado!")
            st.rerun()
        elif submit:
            st.warning("Complete campos requeridos")

def pagina_modificar_insumo():
    st.header("✏️ Modificar Insumo")
    df = get_inventario()
    if df.empty:
        st.info("No hay insumos.")
    else:
        opciones = df.apply(lambda x: f"{x['id']} - {x['tipo_insumo']}", axis=1).tolist()
        seleccion = st.selectbox("Seleccionar", opciones)
        if seleccion:
            item_id = int(seleccion.split(" - ")[0])
            item = df[df['id'] == item_id].iloc[0]
            with st.form("form_mod"):
                c1, c2 = st.columns(2)
                with c1:
                    tipo = st.text_input("Tipo", value=item['tipo_insumo'])
                    modelo = st.text_input("Modelo", value=item['modelo'])
                    medidas = st.text_input("Medidas", value=item['medidas'])
                with c2:
                    equipo = st.text_input("Equipo", value=item['equipo'])
                    cantidad = st.number_input("Cantidad", min_value=0, value=int(item['cantidad']))
                    cantidad_min = st.number_input("Stock Mínimo", min_value=0, value=int(item['cantidad_minima']))
                c3, c4 = st.columns(2)
                with c3:
                    proveedor = st.text_input("Proveedor", value=item['proveedor'])
                    costo = st.number_input("Costo", min_value=0.0, value=float(item['costo_unitario']))
                with c4:
                    observaciones = st.text_area("Observaciones", value=item['observaciones'])
                submit = st.form_submit_button("✏️ Actualizar")
                if submit:
                    fecha = datetime.now().strftime("%Y-%m-%d")
                    execute_query('''UPDATE inventario SET tipo_insumo=?,medidas=?,modelo=?,equipo=?,cantidad=?,cantidad_minima=?,proveedor=?,costo_unitario=?,observaciones=?,fecha_actualizacion=? WHERE id=?''', (tipo,medidas,modelo,equipo,cantidad,cantidad_min,proveedor,costo,observaciones,fecha,item_id))
                    add_to_historial("MODIFICAR", f"ID: {item_id}", st.session_state.usuario_actual)
                    mostrar_mensaje("✅ Actualizado!")
                    st.rerun()

def pagina_eliminar_insumo():
    st.header("🗑️ Eliminar Insumo")
    df = get_inventario()
    if df.empty:
        st.info("Inventario vacío.")
    else:
        opciones = df.apply(lambda x: f"{x['id']} - {x['tipo_insumo']}", axis=1).tolist()
        seleccion = st.selectbox("Seleccionar", opciones)
        passwd = st.text_input("Contraseña para confirmar", type="password")
        if st.button("🗑️ Eliminar"):
            if passwd == "TQ2026":
                item_id = int(seleccion.split(" - ")[0])
                nombre = df[df['id'] == item_id]['tipo_insumo'].values[0]
                execute_query("DELETE FROM inventario WHERE id=?", (item_id,))
                add_to_historial("ELIMINAR", f"Insumo: {nombre}", st.session_state.usuario_actual)
                mostrar_mensaje("✅ Eliminado!")
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")

def pagina_buscar_inventario():
    st.header("🔍 Buscar Inventario")
    df = get_inventario()
    if df.empty:
        st.info("Sin registros.")
    else:
        campo = st.selectbox("Campo", ["tipo_insumo","modelo","equipo","medidas","proveedor"])
        texto = st.text_input("Buscar:", placeholder="...")
        if texto:
            resultado = df[df[campo].str.contains(texto, case=False, na=False)]
            if not resultado.empty:
                st.success(f"✅ {len(resultado)} resultados")
                st.dataframe(resultado)
            else:
                st.warning("Sin resultados")
        else:
            st.dataframe(df)

def pagina_agregar_sistema():
    st.header("➕ Agregar Sistema")
    with st.form("form_sistema"):
        c1, c2 = st.columns(2)
        with c1:
            nombre = st.text_input("Nombre *")
            tipo_filtro = st.text_input("Tipo Filtro")
            modelo = st.text_input("Modelo")
        with c2:
            eficiencia = st.text_input("Eficiencia")
            medidas = st.text_input("Medidas")
            cantidad = st.number_input("Cantidad *", min_value=0, step=1, value=0)
            cantidad_min = st.number_input("Stock Mínimo", min_value=0, step=1, value=5)
        costo = st.number_input("Costo Unitario", min_value=0.0, step=0.01, value=0.0)
        submit = st.form_submit_button("💾 Guardar", use_container_width=True)
        if submit and nombre:
            fecha = datetime.now().strftime("%Y-%m-%d")
            execute_query('''INSERT INTO sistema (nombre,tipo_filtro,modelo,eficiencia,medidas,cantidad,cantidad_minima,costo_unitario,fecha_actualizacion,fecha_creacion) VALUES (?,?,?,?,?,?,?,?,?,?)''', (nombre,tipo_filtro,modelo,eficiencia,medidas,cantidad,cantidad_min,costo,fecha,fecha))
            add_to_historial("AGREGAR SISTEMA", f"Sistema: {nombre}", st.session_state.usuario_actual)
            mostrar_mensaje("✅ Sistema agregado!")
            st.rerun()
        elif submit:
            st.warning("Complete nombre requerido")

def pagina_buscar_sistema():
    st.header("🔍 Buscar Sistema")
    df_sis = get_sistema()
    if df_sis.empty:
        st.info("Sin sistemas.")
    else:
        campo = st.selectbox("Campo", ["nombre","tipo_filtro","modelo","eficiencia"])
