import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from contextlib import contextmanager
import os
import time

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Inventario TQ PRO",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "inventario.db"
ADMIN_PASSWORD = "TQ2026"

# =========================================================
# CONEXIÓN A BASE DE DATOS
# =========================================================

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row

    try:
        yield conn
        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        conn.close()

# =========================================================
# INICIALIZAR BASE DE DATOS
# =========================================================

def init_db():

    with get_connection() as conn:

        cursor = conn.cursor()

        # TABLA INVENTARIO
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_insumo TEXT NOT NULL,
            medidas TEXT,
            eficiencia TEXT,
            modelo TEXT,
            equipo TEXT,
            cantidad INTEGER DEFAULT 0,
            realizado_por TEXT,
            observaciones TEXT,
            fecha_actualizacion TEXT
        )
        """)

        # TABLA SISTEMAS
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sistema (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo_filtro TEXT,
            modelo TEXT,
            eficiencia TEXT,
            medidas TEXT,
            cantidad INTEGER DEFAULT 0,
            fecha_actualizacion TEXT
        )
        """)

        # TABLA HISTORIAL
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            accion TEXT,
            descripcion TEXT,
            usuario TEXT
        )
        """)

# =========================================================
# FUNCIONES GENERALES
# =========================================================

def mostrar_exito(mensaje):
    success = st.empty()
    success.success(mensaje)
    time.sleep(2)
    success.empty()

def validar_texto(texto, minimo=1, maximo=100):

    if texto is None:
        return False

    texto = texto.strip()

    if len(texto) < minimo:
        return False

    if len(texto) > maximo:
        return False

    return True

def validar_cantidad(cantidad):
    return cantidad >= 0

# =========================================================
# HISTORIAL
# =========================================================

def registrar_historial(accion, descripcion, usuario):

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:

        conn.execute("""
        INSERT INTO historial
        (fecha, accion, descripcion, usuario)
        VALUES (?, ?, ?, ?)
        """, (fecha, accion, descripcion, usuario))

# =========================================================
# CRUD INVENTARIO
# =========================================================

def obtener_inventario():

    with get_connection() as conn:

        data = conn.execute("""
        SELECT * FROM inventario
        ORDER BY id DESC
        """).fetchall()

        return pd.DataFrame([dict(x) for x in data])

def agregar_insumo(data):

    with get_connection() as conn:

        conn.execute("""
        INSERT INTO inventario (
            tipo_insumo,
            medidas,
            eficiencia,
            modelo,
            equipo,
            cantidad,
            realizado_por,
            observaciones,
            fecha_actualizacion
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            data['tipo_insumo'],
            data['medidas'],
            data['eficiencia'],
            data['modelo'],
            data['equipo'],
            data['cantidad'],
            data['realizado_por'],
            data['observaciones'],
            data['fecha_actualizacion']

        ))

    registrar_historial(
        "AGREGAR INSUMO",
        f"Insumo agregado: {data['tipo_insumo']} | Cantidad: {data['cantidad']}",
        data['realizado_por']
    )

def actualizar_insumo(item_id, data):

    with get_connection() as conn:

        conn.execute("""
        UPDATE inventario
        SET
            tipo_insumo=?,
            medidas=?,
            eficiencia=?,
            modelo=?,
            equipo=?,
            cantidad=?,
            observaciones=?,
            fecha_actualizacion=?
        WHERE id=?
        """, (

            data['tipo_insumo'],
            data['medidas'],
            data['eficiencia'],
            data['modelo'],
            data['equipo'],
            data['cantidad'],
            data['observaciones'],
            data['fecha_actualizacion'],
            item_id

        ))

    registrar_historial(
        "MODIFICAR INSUMO",
        f"Insumo ID {item_id} actualizado",
        "Usuario"
    )

def eliminar_insumo(item_id):

    with get_connection() as conn:

        item = conn.execute("""
        SELECT * FROM inventario
        WHERE id=?
        """, (item_id,)).fetchone()

        conn.execute("""
        DELETE FROM inventario
        WHERE id=?
        """, (item_id,))

    registrar_historial(
        "ELIMINAR INSUMO",
        f"Insumo eliminado: {item['tipo_insumo']}",
        "Administrador"
    )

# =========================================================
# CRUD SISTEMA
# =========================================================

def obtener_sistemas():

    with get_connection() as conn:

        data = conn.execute("""
        SELECT * FROM sistema
        ORDER BY id DESC
        """).fetchall()

        return pd.DataFrame([dict(x) for x in data])

def agregar_sistema(data):

    with get_connection() as conn:

        conn.execute("""
        INSERT INTO sistema (
            nombre,
            tipo_filtro,
            modelo,
            eficiencia,
            medidas,
            cantidad,
            fecha_actualizacion
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (

            data['nombre'],
            data['tipo_filtro'],
            data['modelo'],
            data['eficiencia'],
            data['medidas'],
            data['cantidad'],
            data['fecha_actualizacion']

        ))

    registrar_historial(
        "AGREGAR SISTEMA",
        f"Sistema agregado: {data['nombre']}",
        "Usuario"
    )

# =========================================================
# INICIAR BASE DE DATOS
# =========================================================

init_db()

# =========================================================
# INTERFAZ
# =========================================================

st.title("📦 Sistema Profesional de Inventario TQ")

menu = st.sidebar.selectbox(

    "Menú Principal",

    [

        "🏠 Inicio",
        "➕ Agregar Insumo",
        "✏️ Modificar Insumo",
        "🗑️ Eliminar Insumo",
        "🔍 Buscar Inventario",
        "➕ Agregar Sistema",
        "🔍 Buscar Sistema",
        "📜 Historial"

    ]

)

# =========================================================
# INICIO
# =========================================================

if menu == "🏠 Inicio":

    st.header("Dashboard General")

    df = obtener_inventario()
    df_sistemas = obtener_sistemas()

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Insumos", len(df))
    col2.metric("Total Sistemas", len(df_sistemas))

    if not df.empty:
        stock_bajo = len(df[df['cantidad'] < 5])
    else:
        stock_bajo = 0

    col3.metric("Stock Bajo", stock_bajo)

    st.markdown("---")

    # ALERTAS
    st.subheader("⚠️ Alertas de Stock")

    if not df.empty:

        low_stock = df[df['cantidad'] < 5]

        if not low_stock.empty:

            st.warning(f"Existen {len(low_stock)} insumos con stock crítico")

            st.dataframe(
                low_stock.set_index('id'),
                use_container_width=True
            )

        else:
            st.success("Inventario en niveles óptimos")

    st.markdown("---")

    st.subheader("📋 Inventario General")

    if not df.empty:

        st.dataframe(
            df.set_index('id'),
            use_container_width=True
        )

    else:
        st.info("No hay datos registrados")

# =========================================================
# AGREGAR INSUMO
# =========================================================

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

        cantidad = c4.number_input(
            "Cantidad *",
            min_value=0,
            step=1
        )

        realizado_por = st.text_input("Realizado por")

        observaciones = st.text_area("Observaciones")

        submit = st.form_submit_button("💾 Guardar")

        if submit:

            if not validar_texto(tipo):

                st.error("Ingrese un tipo de insumo válido")

            elif not validar_cantidad(cantidad):

                st.error("Cantidad inválida")

            else:

                data = {

                    'tipo_insumo': tipo.strip(),
                    'medidas': medidas.strip(),
                    'eficiencia': eficiencia.strip(),
                    'modelo': modelo.strip(),
                    'equipo': equipo.strip(),
                    'cantidad': int(cantidad),
                    'realizado_por': realizado_por.strip(),
                    'observaciones': observaciones.strip(),
                    'fecha_actualizacion': datetime.now().strftime("%Y-%m-%d")

                }

                agregar_insumo(data)

                mostrar_exito("✅ Insumo agregado correctamente")

                st.rerun()

# =========================================================
# MODIFICAR INSUMO
# =========================================================

elif menu == "✏️ Modificar Insumo":

    st.header("Modificar Insumo")

    df = obtener_inventario()

    if df.empty:

        st.info("No existen insumos")

    else:

        opciones = df.apply(
            lambda x: f"{x['id']} - {x['tipo_insumo']}",
            axis=1
        ).tolist()

        seleccion = st.selectbox(
            "Seleccione un insumo",
            opciones
        )

        item_id = int(seleccion.split(" - ")[0])

        item = df[df['id'] == item_id].iloc[0]

        with st.form("form_modificar"):

            c1, c2 = st.columns(2)

            tipo = c1.text_input(
                "Tipo",
                value=item['tipo_insumo']
            )

            modelo = c1.text_input(
                "Modelo",
                value=item['modelo']
            )

            medidas = c2.text_input(
                "Medidas",
                value=item['medidas']
            )

            eficiencia = c2.text_input(
                "Eficiencia",
                value=item['eficiencia']
            )

            c3, c4 = st.columns(2)

            equipo = c3.text_input(
                "Equipo",
                value=item['equipo']
            )

            cantidad = c4.number_input(
                "Cantidad",
                min_value=0,
                value=int(item['cantidad'])
            )

            observaciones = st.text_area(
                "Observaciones",
                value=item['observaciones']
            )

            submit = st.form_submit_button("✏️ Actualizar")

            if submit:

                data = {

                    'tipo_insumo': tipo.strip(),
                    'medidas': medidas.strip(),
                    'eficiencia': eficiencia.strip(),
                    'modelo': modelo.strip(),
                    'equipo': equipo.strip(),
                    'cantidad': int(cantidad),
                    'observaciones': observaciones.strip(),
                    'fecha_actualizacion': datetime.now().strftime("%Y-%m-%d")

                }

                actualizar_insumo(item_id, data)

                mostrar_exito("✅ Insumo actualizado")

                st.rerun()

# =========================================================
# ELIMINAR INSUMO
# =========================================================

elif menu == "🗑️ Eliminar Insumo":

    st.header("Eliminar Insumo")

    df = obtener_inventario()

    if df.empty:

        st.info("Inventario vacío")

    else:

        opciones = df.apply(
            lambda x: f"{x['id']} - {x['tipo_insumo']}",
            axis=1
        ).tolist()

        seleccion = st.selectbox(
            "Seleccione Insumo",
            opciones
        )

        password = st.text_input(
            "Contraseña Administrador",
            type="password"
        )

        if st.button("🗑️ Eliminar"):

            if password == ADMIN_PASSWORD:

                item_id = int(seleccion.split(" - ")[0])

                eliminar_insumo(item_id)

                mostrar_exito("✅ Insumo eliminado")

                st.rerun()

            else:

                st.error("❌ Contraseña incorrecta")

# =========================================================
# BUSCAR INVENTARIO
# =========================================================

elif menu == "🔍 Buscar Inventario":

    st.header("Buscar Inventario")

    df = obtener_inventario()

    if df.empty:

        st.info("No hay registros")

    else:

        campo = st.selectbox(

            "Campo de búsqueda",

            [

                "tipo_insumo",
                "modelo",
                "equipo",
                "medidas",
                "eficiencia",
                "realizado_por"

            ]

        )

        texto = st.text_input(
            "Buscar",
            placeholder="Ingrese texto..."
        )

        if texto:

            resultado = df[
                df[campo].astype(str).str.contains(
                    texto,
                    case=False,
                    na=False
                )
            ]

            registrar_historial(
                "BUSCAR INVENTARIO",
                f"Búsqueda: {texto}",
                "Usuario"
            )

            if not resultado.empty:

                st.success(
                    f"Se encontraron {len(resultado)} resultado(s)"
                )

                st.dataframe(
                    resultado.set_index('id'),
                    use_container_width=True
                )

            else:

                st.warning("No se encontraron resultados")

        else:

            st.dataframe(
                df.set_index('id'),
                use_container_width=True
            )

# =========================================================
# AGREGAR SISTEMA
# =========================================================

elif menu == "➕ Agregar Sistema":

    st.header("Agregar Nuevo Sistema")

    with st.form("form_sistema"):

        c1, c2 = st.columns(2)

        nombre = c1.text_input("Nombre Sistema *")
        tipo_filtro = c1.text_input("Tipo Filtro")

        modelo = c2.text_input("Modelo")
        eficiencia = c2.text_input("Eficiencia")

        c3, c4 = st.columns(2)

        medidas = c3.text_input("Medidas")

        cantidad = c4.number_input(
            "Cantidad",
            min_value=0,
            step=1
        )

        submit = st.form_submit_button("💾 Guardar")

        if submit:

            if not validar_texto(nombre):

                st.error("Nombre inválido")

            else:

                data = {

                    'nombre': nombre.strip(),
                    'tipo_filtro': tipo_filtro.strip(),
                    'modelo': modelo.strip(),
                    'eficiencia': eficiencia.strip(),
                    'medidas': medidas.strip(),
                    'cantidad': int(cantidad),
                    'fecha_actualizacion': datetime.now().strftime("%Y-%m-%d")

                }

                agregar_sistema(data)

                mostrar_exito("✅ Sistema agregado")

                st.rerun()

# =========================================================
# BUSCAR SISTEMA
# =========================================================

elif menu == "🔍 Buscar Sistema":

    st.header("Buscar Sistema")

    df = obtener_sistemas()

    if df.empty:

        st.info("No existen sistemas")

    else:

        campo = st.selectbox(

            "Campo búsqueda",

            [

                "nombre",
                "tipo_filtro",
                "modelo",
                "eficiencia",
                "medidas"

            ]

        )

        texto = st.text_input(
            "Buscar Sistema"
        )

        if texto:

            resultado = df[
                df[campo].astype(str).str.contains(
                    texto,
                    case=False,
                    na=False
                )
            ]

            registrar_historial(
                "BUSCAR SISTEMA",
                f"Búsqueda sistema: {texto}",
                "Usuario"
            )

            if not resultado.empty:

                st.success(
                    f"Se encontraron {len(resultado)} resultado(s)"
                )

                st.dataframe(
                    resultado.set_index('id'),
                    use_container_width=True
                )

            else:

                st.warning("Sin resultados")

        else:

            st.dataframe(
                df.set_index('id'),
                use_container_width=True
            )

# =========================================================
# HISTORIAL
# =========================================================

elif menu == "📜 Historial":

    st.header("Historial de Movimientos")

    with get_connection() as conn:

        data = conn.execute("""
        SELECT * FROM historial
        ORDER BY fecha DESC
        """).fetchall()

    df_hist = pd.DataFrame([dict(x) for x in data])

    if not df_hist.empty:

        st.dataframe(
            df_hist.set_index('id'),
            use_container_width=True
        )

    else:

        st.info("No hay movimientos registrados")
        
