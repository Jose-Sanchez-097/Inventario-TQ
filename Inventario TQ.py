import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from contextlib import contextmanager
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
# RESET DB
# =========================================================

RESET_DB = True

# =========================================================
# CONEXIÓN SQLITE
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
# CREAR BASE DE DATOS
# =========================================================

def init_db():

    with get_connection() as conn:

        cursor = conn.cursor()

        # -------------------------------------------------
        # BORRAR TABLAS (SOLO DESARROLLO)
        # -------------------------------------------------

        if RESET_DB:

            cursor.execute("DROP TABLE IF EXISTS inventario")
            cursor.execute("DROP TABLE IF EXISTS sistema")
            cursor.execute("DROP TABLE IF EXISTS historial")

        # -------------------------------------------------
        # TABLA INVENTARIO
        # -------------------------------------------------

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            articulo TEXT NOT NULL,
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

        # -------------------------------------------------
        # TABLA SISTEMA
        # -------------------------------------------------

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

        # -------------------------------------------------
        # TABLA HISTORIAL
        # -------------------------------------------------

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
# VALIDACIONES
# =========================================================

def validar_texto(texto, minimo=1, maximo=100):

    if texto is None:
        return False

    texto = texto.strip()

    if len(texto) < minimo:
        return False

    if len(texto) > maximo:
        return False

    return True

# =========================================================
# MENSAJES
# =========================================================

def mostrar_exito(mensaje):

    success = st.empty()

    success.success(mensaje)

    time.sleep(2)

    success.empty()

# =========================================================
# HISTORIAL
# =========================================================

def registrar_historial(accion, descripcion, usuario):

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:

        conn.execute("""
        INSERT INTO historial (

            fecha,
            accion,
            descripcion,
            usuario

        )
        VALUES (?, ?, ?, ?)
        """, (

            fecha,
            accion,
            descripcion,
            usuario

        ))

# =========================================================
# INVENTARIO
# =========================================================

def obtener_inventario():

    with get_connection() as conn:

        rows = conn.execute("""
        SELECT * FROM inventario
        ORDER BY id DESC
        """).fetchall()

    return pd.DataFrame([dict(x) for x in rows])

# ---------------------------------------------------------

def agregar_articulo(data):

    try:

        with get_connection() as conn:

            conn.execute("""
            INSERT INTO inventario (

                articulo,
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

                data["articulo"],
                data["medidas"],
                data["eficiencia"],
                data["modelo"],
                data["equipo"],
                data["cantidad"],
                data["realizado_por"],
                data["observaciones"],
                data["fecha_actualizacion"]

            ))

        registrar_historial(

            "AGREGAR ARTICULO",
            f"Articulo agregado: {data['articulo']}",
            data["realizado_por"]

        )

        return True, "Articulo agregado correctamente"

    except Exception as e:

        return False, str(e)

# ---------------------------------------------------------

def actualizar_articulo(item_id, data):

    try:

        with get_connection() as conn:

            conn.execute("""
            UPDATE inventario
            SET

                articulo=?,
                medidas=?,
                eficiencia=?,
                modelo=?,
                equipo=?,
                cantidad=?,
                observaciones=?,
                fecha_actualizacion=?

            WHERE id=?
            """, (

                data["articulo"],
                data["medidas"],
                data["eficiencia"],
                data["modelo"],
                data["equipo"],
                data["cantidad"],
                data["observaciones"],
                data["fecha_actualizacion"],
                item_id

            ))

        registrar_historial(

            "MODIFICAR ARTICULO",
            f"Articulo actualizado ID {item_id}",
            "Usuario"

        )

        return True, "Articulo actualizado"

    except Exception as e:

        return False, str(e)

# ---------------------------------------------------------

def eliminar_articulo(item_id):

    try:

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

            "ELIMINAR ARTICULO",
            f"Articulo eliminado: {item['articulo']}",
            "Administrador"

        )

        return True, "Articulo eliminado"

    except Exception as e:

        return False, str(e)

# =========================================================
# SISTEMAS
# =========================================================

def obtener_sistemas():

    with get_connection() as conn:

        rows = conn.execute("""
        SELECT * FROM sistema
        ORDER BY id DESC
        """).fetchall()

    return pd.DataFrame([dict(x) for x in rows])

# ---------------------------------------------------------

def agregar_sistema(data):

    try:

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

                data["nombre"],
                data["tipo_filtro"],
                data["modelo"],
                data["eficiencia"],
                data["medidas"],
                data["cantidad"],
                data["fecha_actualizacion"]

            ))

        registrar_historial(

            "AGREGAR SISTEMA",
            f"Sistema agregado: {data['nombre']}",
            "Usuario"

        )

        return True, "Sistema agregado"

    except Exception as e:

        return False, str(e)

# =========================================================
# INICIALIZAR DB
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
        "➕ Agregar Articulo",
        "✏️ Modificar Articulo",
        "🗑️ Eliminar Articulo",
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

    st.header("Dashboard")

    df = obtener_inventario()
    df_sis = obtener_sistemas()

    c1, c2, c3 = st.columns(3)

    c1.metric("Total Articulos", len(df))
    c2.metric("Total Sistemas", len(df_sis))

    if not df.empty:
        stock_bajo = len(df[df["cantidad"] < 5])
    else:
        stock_bajo = 0

    c3.metric("Stock Bajo", stock_bajo)

    st.markdown("---")

    if not df.empty:

        low_stock = df[df["cantidad"] < 5]

        if not low_stock.empty:

            st.warning(
                f"Existen {len(low_stock)} articulos con stock crítico"
            )

            st.dataframe(
                low_stock.set_index("id"),
                use_container_width=True
            )

    st.markdown("---")

    st.subheader("Inventario General")

    if not df.empty:

        st.dataframe(
            df.set_index("id"),
            use_container_width=True
        )

    else:

        st.info("No existen registros")

# =========================================================
# AGREGAR ARTICULO
# =========================================================

elif menu == "➕ Agregar Articulo":

    st.header("Agregar Nuevo Articulo")

    with st.form("agregar_form"):

        c1, c2 = st.columns(2)

        articulo = c1.text_input("Articulo *")
        modelo = c1.text_input("Modelo")

        medidas = c2.text_input("Medidas")
        eficiencia = c2.text_input("Eficiencia")

        c3, c4 = st.columns(2)

        equipo = c3.text_input("Equipo")

        cantidad = c4.number_input(
            "Cantidad",
            min_value=0,
            step=1
        )

        realizado_por = st.text_input("Realizado Por")

        observaciones = st.text_area("Observaciones")

        submit = st.form_submit_button("💾 Guardar")

        if submit:

            if not validar_texto(articulo):

                st.error("Articulo inválido")

            else:

                data = {

                    "articulo": articulo.strip(),
                    "medidas": medidas.strip(),
                    "eficiencia": eficiencia.strip(),
                    "modelo": modelo.strip(),
                    "equipo": equipo.strip(),
                    "cantidad": int(cantidad),
                    "realizado_por": realizado_por.strip(),
                    "observaciones": observaciones.strip(),
                    "fecha_actualizacion": datetime.now().strftime("%Y-%m-%d")

                }

                ok, mensaje = agregar_articulo(data)

                if ok:

                    mostrar_exito("✅ " + mensaje)

                    st.rerun()

                else:

                    st.error(mensaje)

# =========================================================
# MODIFICAR ARTICULO
# =========================================================

elif menu == "✏️ Modificar Articulo":

    st.header("Modificar Articulo")

    df = obtener_inventario()

    if df.empty:

        st.info("No existen articulos")

    else:

        opciones = df.apply(
            lambda x: f"{x['id']} - {x['articulo']}",
            axis=1
        ).tolist()

        seleccion = st.selectbox(
            "Seleccione Articulo",
            opciones
        )

        item_id = int(seleccion.split(" - ")[0])

        item = df[df["id"] == item_id].iloc[0]

        with st.form("modificar_form"):

            articulo = st.text_input(
                "Articulo",
                value=item["articulo"]
            )

            modelo = st.text_input(
                "Modelo",
                value=item["modelo"]
            )

            medidas = st.text_input(
                "Medidas",
                value=item["medidas"]
            )

            eficiencia = st.text_input(
                "Eficiencia",
                value=item["eficiencia"]
            )

            equipo = st.text_input(
                "Equipo",
                value=item["equipo"]
            )

            cantidad = st.number_input(
                "Cantidad",
                min_value=0,
                value=int(item["cantidad"])
            )

            observaciones = st.text_area(
                "Observaciones",
                value=item["observaciones"]
            )

            submit = st.form_submit_button("✏️ Actualizar")

            if submit:

                data = {

                    "articulo": articulo.strip(),
                    "medidas": medidas.strip(),
                    "eficiencia": eficiencia.strip(),
                    "modelo": modelo.strip(),
                    "equipo": equipo.strip(),
                    "cantidad": int(cantidad),
                    "observaciones": observaciones.strip(),
                    "fecha_actualizacion": datetime.now().strftime("%Y-%m-%d")

                }

                ok, mensaje = actualizar_articulo(
                    item_id,
                    data
                )

                if ok:

                    mostrar_exito("✅ " + mensaje)

                    st.rerun()

                else:

                    st.error(mensaje)

# =========================================================
# ELIMINAR ARTICULO
# =========================================================

elif menu == "🗑️ Eliminar Articulo":

    st.header("Eliminar Articulo")

    df = obtener_inventario()

    if df.empty:

        st.info("Inventario vacío")

    else:

        opciones = df.apply(
            lambda x: f"{x['id']} - {x['articulo']}",
            axis=1
        ).tolist()

        seleccion = st.selectbox(
            "Seleccione Articulo",
            opciones
        )

        password = st.text_input(
            "Contraseña Administrador",
            type="password"
        )

        if st.button("🗑️ Eliminar"):

            if password == ADMIN_PASSWORD:

                item_id = int(seleccion.split(" - ")[0])

                ok, mensaje = eliminar_articulo(item_id)

                if ok:

                    mostrar_exito("✅ " + mensaje)

                    st.rerun()

                else:

                    st.error(mensaje)

            else:

                st.error("❌ Contraseña incorrecta")
