import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Gestion de Inventarios TQ", page_icon="📦", layout="wide", initial_sidebar_state="expanded")

DB_FILE = 'inventario.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inventario (id INTEGER PRIMARY KEY AUTOINCREMENT, tipo_insumo TEXT, medidas TEXT, eficiencia TEXT, modelo TEXT, equipo TEXT, cantidad INTEGER, realizado_por TEXT, observaciones TEXT, fecha_actualizacion TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sistema (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, tipo_filtro TEXT, modelo TEXT, eficiencia TEXT, medidas TEXT, cantidad INTEGER, fecha_actualizacion TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS historial (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, accion TEXT, descripcion TEXT, usuario TEXT)''')
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

def add_to_historial(accion, descripcion, usuario):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execute_query("INSERT INTO historial (fecha, accion, descripcion, usuario) VALUES (?, ?, ?, ?)", (fecha, accion, descripcion, usuario))

init_db()

st.title("📦 Plataforma de Gestion de Inventarios")

menu = st.sidebar.selectbox("Menu Principal", ["🏠 Inicio", "➕ Agregar Insumo", "✏️ Modificar Insumo", "🗑️ Eliminar Insumo", "🔍 Buscar Inventario", "⚙️ Sistema", "🔍 Buscar Sistema", "📜 Historial"])

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
            execute_query("INSERT INTO inventario (tipo_insumo, medidas, eficiencia, modelo, equipo, cantidad, realizado_por, observaciones, fecha_actualizacion) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                        (tipo, medidas, eficiencia, modelo, equipo, cantidad_int, realizado_por, observaciones, fecha_actual))
            add_to_historial("ALTA", f"Insumo: {tipo} (Cant: {cantidad_int})", realizado_por)
            st.success("✅ Insumo agregado exitosamente!")
        elif submit:
            st.warning("Por favor complete los campos obligatorios (*).")

elif menu == "✏️ Modificar Insumo":
    st.header("Modificar Insumo Existente")
    df = get_inventario()
    if df.empty:
        st.info("No hay insumos para modificar.")
    else:
        opciones = df.apply(lambda x: f"{x['id']} - {x['tipo_insumo']} ({x['modelo']})", axis=1).tolist()
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
                passwd = st.text_input("Contraseña (Requerido para modificar)", type="password")
                submit = st.form_submit_button("✏️ Actualizar")
                if submit and passwd == "TQ2026":
                    fecha_actual = datetime.now().strftime("%Y-%m-%d")
                    execute_query("UPDATE inventario SET tipo_insumo=?, medidas=?, eficiencia=?, modelo=?, equipo=?, cantidad=?, observaciones=?, fecha_actualizacion=? WHERE id=?", 
                                (tipo, medidas, eficiencia, modelo, equipo, int(cantidad), observaciones, fecha_actual, item_id))
                    add_to_historial("MODIFICACIÓN", f"ID: {item_id} - {tipo}", "Usuario Admin")
                    st.success("✅ Insumo actualizado.")
                elif submit:
                    st.error("❌ Contraseña incorrecta. Use TQ2026")

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
                item_name = df[df['id'] == item_id]['tipo_insumo'].values[0]
                execute_query("DELETE FROM inventario WHERE id=?", (item_id,))
                add_to_historial("ELIMINACIÓN", f"Insumo ID: {item_id} - {item_name}", "Usuario Admin")
                st.success("✅ Insumo eliminado.")
            else:
                st.error("❌ Contraseña incorrecta.")

elif menu == "🔍 Buscar Inventario":
    st.header("🔍 Buscar Insumo en Inventario")
    df = get_inventario()
    if df.empty:
        st.info("No hay insumos registrados.")
    else:
        col1, col2 = st.columns([1, 2])
        with col1:
            campo_busqueda = st.selectbox("Seleccione campo de búsqueda:", ["tipo_insumo", "modelo", "equipo", "medidas", "eficiencia", "realizado_por"])
            nombres_campos = {"tipo_insumo": "Tipo de Insumo", "modelo": "Modelo", "equipo": "Equipo", "medidas": "Medidas", "eficiencia": "Eficiencia", "realizado_por": "Realizado Por"}
        with col2:
            texto_busqueda = st.text_input(f"Buscar por {nombres_campos[campo_busqueda]}", placeholder=f"Ingrese valor para {nombres_campos[campo_busqueda]}...")
        if texto_busqueda:
            resultado = df[df[campo_busqueda].str.contains(texto_busqueda, case=False, na=False)]
            if not resultado.empty:
                st.success(f"✅ Se encontraron {len(resultado)} resultado(s)")
                st.dataframe(resultado.set_index('id'), use_container_width=True)
            else:
                st.warning(f"⚠️ No se encontraron resultados para '{texto_busqueda}'")
        else:
            st.info("👆 Ingrese un valor para buscar o deje vacío para ver todo")
            st.dataframe(df.set_index('id'), use_container_width=True)

elif menu == "⚙️ Sistema":
    st.header("Gestión de Sistema")
    tab1, tab2, tab3 = st.tabs(["➕ Agregar", "✏️ Modificar", "🗑️ Eliminar"])
    with tab1:
        st.subheader("Agregar Nuevo Sistema")
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
                execute_query("INSERT INTO sistema (nombre, tipo_filtro, modelo, eficiencia, medidas, cantidad, fecha_actualizacion) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                            (nombre, tipo_filtro, modelo, eficiencia, medidas, int(cantidad) if cantidad else 0, fecha_actual))
                add_to_historial("ALTA SISTEMA", f"Sistema: {nombre}", "Usuario")
                st.success("✅ Sistema agregado.")
            elif submit:
                st.warning("Complete los campos obligatorios (*).")
    with tab2:
        st.subheader("Modificar Sistema")
        df_sis = get_sistema()
        if df_sis.empty:
            st.info("No hay sistemas registrados.")
        else:
            opciones_sis = df_sis.apply(lambda x: f"{x['id']} - {x['nombre']}", axis=1).tolist()
            seleccion_sis = st.selectbox("Seleccione Sistema a Modificar", opciones_sis)
            if seleccion_sis:
                sis_id = int(seleccion_sis.split(" - ")[0])
                sis_item = df_sis[df_sis['id'] == sis_id].iloc[0]
                with st.form("form_sistema_mod"):
                    c1, c2 = st.columns(2)
                    nombre = c1.text_input("Nombre", value=sis_item['nombre'])
                    tipo_filtro = c1.text_input("Tipo de Filtro", value=sis_item['tipo_filtro'])
                    modelo = c2.text_input("Modelo", value=sis_item['modelo'])
                    eficiencia = c2.text_input("Eficiencia", value=sis_item['eficiencia'])
                    c3, c4 = st.columns(2)
                    medidas = c3.text_input("Medidas", value=sis_item['medidas'])
                    cantidad = c4.number_input("Cantidad", min_value=0, value=int(sis_item['cantidad']))
                    passwd = st.text_input("Contraseña (TQ2026)", type="password")
                    submit = st.form_submit_button("✏️ Actualizar Sistema")
                    if submit and passwd == "TQ2026":
                        fecha_actual = datetime.now().strftime("%Y-%m-%d")
                        execute_query("UPDATE sistema SET nombre=?, tipo_filtro=?, modelo=?, eficiencia=?, medidas=?, cantidad=?, fecha_actualizacion=? WHERE id=?", 
                                    (nombre, tipo_filtro, modelo, eficiencia, medidas, int(cantidad), fecha_actual, sis_id))
                        add_to_historial("MODIFICACIÓN SISTEMA", f"ID: {sis_id} - {nombre}", "Admin")
                        st.success("✅ Sistema actualizado.")
                    elif submit:
                        st.error("❌ Contraseña incorrecta.")
    with tab3:
        st.subheader("Eliminar Sistema")
        df_sis = get_sistema()
        if df_sis.empty:
            st.info("No hay sistemas.")
        else:
            opciones_sis = df_sis.apply(lambda x: f"{x['id']} - {x['nombre']}", axis=1).tolist()
            seleccion_sis = st.selectbox("Seleccione Sistema a Eliminar", opciones_sis)
            passwd = st.text_input("Contraseña (TQ2026)", type="password")
            if st.button("🗑️ Eliminar Sistema"):
                if passwd == "TQ2026":
                    sis_id = int(seleccion_sis.split(" - ")[0])
                    sis_nombre = df_sis[df_sis['id'] == sis_id]['nombre'].values[0]
                    execute_query("DELETE FROM sistema WHERE id=?", (sis_id,))
                    add_to_historial("ELIMINACIÓN SISTEMA", f"Sistema: {sis_nombre}", "Admin")
                    st.success("✅ Sistema eliminado.")
                else:
                    st.error("❌ Contraseña incorrecta.")

elif menu == "🔍 Buscar Sistema":
    st.header("🔍 Buscar Sistema")
    df_sis = get_sistema()
    if df_sis.empty:
        st.info("No hay sistemas registrados.")
    else:
        col1, col2 = st.columns([1, 2])
        with col1:
            campo_busqueda_sis = st.selectbox("Seleccione campo de búsqueda:", ["nombre", "tipo_filtro", "modelo", "eficiencia", "medidas"])
            nombres_campos_sis = {"nombre": "Nombre del Sistema", "tipo_filtro": "Tipo de Filtro", "modelo": "Modelo", "eficiencia": "Eficiencia", "medidas": "Medidas"}
        with col2:
            texto_busqueda_sis = st.text_input(f"Buscar por {nombres_campos_sis[campo_busqueda_sis]}", placeholder=f"Ingrese valor para {nombres_campos_sis[campo_busqueda_sis]}...")
        if texto_busqueda_sis:
            resultado_sis = df_sis[df_sis[campo_busqueda_sis].str.contains(texto_busqueda_sis, case=False, na=False)]
            if not resultado_sis.empty:
                st.success(f"✅ Se encontraron {len(resultado_sis)} resultado(s)")
                st.dataframe(resultado_sis.set_index('id'), use_container_width=True)
            else:
                st.warning(f"⚠️ No se encontraron resultados para '{texto_busqueda_sis}'")
        else:
            st.info("👆 Ingrese un valor para buscar o deje vacío para ver todo")
            st.dataframe(df_sis.set_index('id'), use_container_width=True)

elif menu ==
