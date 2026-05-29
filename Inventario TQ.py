import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time

st.set_page_config(page_title="Gestion de Inventarios TQ", page_icon="📦", layout="wide", initial_sidebar_state="expanded")

DB_FILE = 'inventario.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventario'")
    if not c.fetchone():
        c.execute('''CREATE TABLE inventario (id INTEGER PRIMARY KEY AUTOINCREMENT, tipo_insumo TEXT NOT NULL, medidas TEXT, eficiencia TEXT, modelo TEXT, equipo TEXT, cantidad INTEGER DEFAULT 0, realizado_por TEXT, observaciones TEXT, fecha_actualizacion TEXT)''')
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sistema'")
    if not c.fetchone():
        c.execute('''CREATE TABLE sistema (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, tipo_filtro TEXT, modelo TEXT, eficiencia TEXT, medidas TEXT, cantidad INTEGER DEFAULT 0, fecha_actualizacion TEXT)''')
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='historial'")
    if not c.fetchone():
        # Cambiar nombre del campo "accion" a "cantidad_filtros"
        c.execute('''CREATE TABLE historial (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, cantidad_filtros TEXT, descripcion TEXT, usuario TEXT)''')
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

def add_to_historial(cantidad_filtros, descripcion, usuario):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execute_query("INSERT INTO historial (fecha, cantidad_filtros, descripcion, usuario) VALUES (?, ?, ?, ?)", (fecha, cantidad_filtros, descripcion, usuario))

def mostrar_mensaje_exito(mensaje):
    success_placeholder = st.empty()
    success_placeholder.success(mensaje)
    time.sleep(5)
    success_placeholder.empty()

init_db()

st.title("📦 Plataforma de Gestion de Inventarios")

menu = st.sidebar.selectbox("Menu Principal", ["🏠 Inicio", "➕ Agregar Insumo", "✏️ Modificar Insumo", "🗑️ Eliminar Insumo", "🔍 Buscar Inventario", "➕ Agregar Sistema", "🔍 Buscar Sistema", "📜 Historial"])

if menu == "🏠 Inicio":
    st.header("Panel de Control en Tiempo Real")
    df = get_inventario()
    df_sis = get_sistema()
    col1, col2 = st.columns(2)
    col1.metric("Total Insumos", len(df))
    col2.metric("Total Sistemas", len(df_sis))
    st.markdown("---")
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
    st.subheader("📋 Vista General del Inventario")
    st.dataframe(df.set_index('id'), use_container_width=True)

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
        realizado_por = st.text_input("Realizado por")
        observaciones = st.text_area("Observaciones")
        submit = st.form_submit_button("💾 Guardar Insumo")
        if submit and tipo:
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            cantidad_int = int(cantidad) if cantidad else 0
            sql = f"""INSERT INTO inventario (tipo_insumo, medidas, eficiencia, modelo, equipo, cantidad, realizado_por, observaciones, fecha_actualizacion) VALUES ('{tipo}', '{medidas if medidas else ''}', '{eficiencia if eficiencia else ''}', '{modelo if modelo else ''}', '{equipo if equipo else ''}', {cantidad_int}, '{realizado_por if realizado_por else ''}', '{observaciones if observaciones else ''}', '{fecha_actual}')"""
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute(sql)
            conn.commit()
            conn.close()
            # Historial: cantidad en cantidad_filtros, equipo en descripcion
            add_to_historial(f"Cantidad: {cantidad_int}", f"Insumo: {tipo} | Equipo: {equipo if equipo else 'N/A'} | Modelo: {modelo if modelo else 'N/A'}", realizado_por if realizado_por else "Usuario")
            mostrar_mensaje_exito("✅ Insumo agregado exitosamente!")
            st.rerun()
        elif submit:
            st.warning("Por favor complete los campos obligatorios (*).")

elif menu == "✏️ Modificar Insumo":
    st.header("Modificar Insumo Existente")
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
                tipo = c1.text_input("Tipo de Insumo", value=item['tipo_insumo'])
                modelo = c1.text_input("Modelo", value=item['modelo'])
                medidas = c2.text_input("Medidas", value=item['medidas'])
                eficiencia = c2.text_input("Eficiencia", value=item['eficiencia'])
                c3, c4 = st.columns(2)
                equipo = c3.text_input("Equipo", value=item['equipo'])
                cantidad = c4.number_input("Cantidad Actual", min_value=0, value=int(item['cantidad']))
                observaciones = st.text_area("Observaciones", value=item['observaciones'])
                submit = st.form_submit_button("✏️ Actualizar")
                if submit:
                    fecha_actual = datetime.now().strftime("%Y-%m-%d")
                    cantidad_actual = int(cantidad)
                    sql = f"""UPDATE inventario SET tipo_insumo='{tipo}', medidas='{medidas if medidas else ''}', eficiencia='{eficiencia if eficiencia else ''}', modelo='{modelo if modelo else ''}', equipo='{equipo if equipo else ''}', cantidad={cantidad_actual}, observaciones='{observaciones if observaciones else ''}', fecha_actualizacion='{fecha_actual}' WHERE id={item_id}"""
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute(sql)
                    conn.commit()
                    conn.close()
                    # Historial: cantidad en cantidad_filtros, equipo en descripcion
                    add_to_historial(f"Cantidad: {cantidad_actual}", f"ID: {item_id} | Insumo: {tipo} | Equipo: {equipo if equipo else 'N/A'} | Modelo: {modelo if modelo else 'N/A'}", "Usuario")
                    mostrar_mensaje_exito("✅ Insumo actualizado exitosamente!")
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
                cantidad_insumo = df[df['id'] == item_id]['cantidad'].values[0]
                equipo_insumo = df[df['id'] == item_id]['equipo'].values[0]
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute(f"DELETE FROM inventario WHERE id={item_id}")
                conn.commit()
                conn.close()
                # Historial: cantidad en cantidad_filtros, equipo en descripcion
                add_to_historial(f"Cantidad: {cantidad_insumo}", f"ID: {item_id} | Insumo: {nombre_insumo} | Equipo: {equipo_insumo if equipo_insumo else 'N/A'}", "Admin")
                mostrar_mensaje_exito("✅ Insumo eliminado exitosamente!")
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta.")

elif menu == "🔍 Buscar Inventario":
    st.header("🔍 Buscar Insumo en Inventario")
    df = get_inventario()
    if df.empty:
        st.info("No hay insumos registrados.")
    else:
        campo_busqueda = st.selectbox("Seleccione campo de búsqueda:", ["tipo_insumo", "modelo", "equipo", "medidas", "eficiencia", "realizado_por"])
        texto_busqueda = st.text_input("Buscar:", placeholder="Ingrese texto a buscar...")
        if texto_busqueda:
            resultado = df[df[campo_busqueda].str.contains(texto_busqueda, case=False, na=False)]
            if not resultado.empty:
                st.success(f"✅ Se encontraron {len(resultado)} resultado(s)")
                # Historial
                add_to_historial(f"Resultados: {len(resultado)}", f"Busqueda: {texto_busqueda} | Campo: {campo_busqueda}", "Usuario")
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
        submit = st.form_submit_button("💾 Guardar Sistema")
        if submit and nombre:
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            cantidad_int = int(cantidad) if cantidad else 0
            sql = f"""INSERT INTO sistema (nombre, tipo_filtro, modelo, eficiencia, medidas, cantidad, fecha_actualizacion) VALUES ('{nombre}', '{tipo_filtro if tipo_filtro else ''}', '{modelo if modelo else ''}', '{eficiencia if eficiencia else ''}', '{medidas if medidas else ''}', {cantidad_int}, '{fecha_actual}')"""
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute(sql)
            conn.commit()
            conn.close()
            # Historial
            add_to_historial(f"Cantidad: {cantidad_int}", f"Sistema: {nombre} | Tipo Filtro: {tipo_filtro if tipo_filtro else 'N/A'}", "Usuario")
            mostrar_mensaje_exito("✅ Sistema agregado exitosamente!")
            st.rerun()
        elif submit:
            st.warning("Complete los campos obligatorios (*).")

elif menu == "🔍 Buscar Sistema":
    st.header("🔍 Buscar Sistema")
    df_sis = get_sistema()
    if df_sis.empty:
        st.info("No hay sistemas registrados.")
    else:
        campo_busqueda_sis = st.selectbox("Seleccione campo de búsqueda:", ["nombre", "tipo_filtro", "modelo", "eficiencia", "medidas"])
        texto_busqueda_sis = st.text_input("Buscar:", placeholder="Ingrese texto a buscar...")
        if texto_busqueda_sis:
            resultado_sis = df_sis[df_sis[campo_busqueda_sis].str.contains(texto_busqueda_sis, case=False, na=False)]
            if not resultado_sis.empty:
                st.success(f"✅ Se encontraron {len(resultado_sis)} resultado(s)")
                # Historial
                add_to_historial(f"Resultados: {len(resultado_sis)}", f"Busqueda: {texto_busqueda_sis} | Campo: {campo_busqueda_sis}", "Usuario")
                st.dataframe(resultado_sis.set_index('id'), use_container_width=True)
            else:
                st.warning(f"⚠️ No se encontraron resultados")
        else:
            st.dataframe(df_sis.set_index('id'), use_container_width=True)

elif menu == "📜 Historial":
    st.header("📜 Historial de Movimientos")
    df_hist = run_query("SELECT * FROM historial ORDER BY fecha DESC")
    if df_hist.empty:
        st.info("Sin movimientos registrados.")
    else:
        # Renombrar columnas para mostrar
        df_hist = df_hist.rename(columns={'cantidad_filtros': 'Cantidad de Filtros'})
        st.dataframe(df_hist.set_index('id'), use_container_width=True)
