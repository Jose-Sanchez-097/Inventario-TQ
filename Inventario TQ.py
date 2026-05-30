
import sqlite3
from contextlib import contextmanager

DB_FILE = 'data/inventario.db'

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

from database.db import get_connection


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute('''
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
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            accion TEXT,
            descripcion TEXT,
            usuario TEXT
        )
        ''')

def validar_texto(texto: str, minimo=1, maximo=100):
    if not texto:
        return False

    texto = texto.strip()

    if len(texto) < minimo:
        return False

    if len(texto) > maximo:
        return False

    return True


def validar_cantidad(cantidad):
    return cantidad >= 0

import os
from dotenv import load_dotenv

load_dotenv()


def validar_admin(password):
    return password == os.getenv("ADMIN_PASSWORD")

from datetime import datetime
from database.db import get_connection


def registrar_historial(accion, descripcion, usuario):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:conn.execute(""" INSERT INTO historial (fecha, accion, descripcion, usuario) VALUES (?, ?, ?, ?) """),
            (fecha, accion, descripcion, usuario)

from database.db import get_connection
from modules.historial import registrar_historial


class InventarioService:

    @staticmethod
    def obtener_todos():
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM inventario ORDER BY id DESC"
            ).fetchall()

    @staticmethod
    def agregar(data):
        with get_connection() as conn:
            conn.execute(
                """
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
                """,
                (
                    data['tipo_insumo'],
                    data['medidas'],
                    data['eficiencia'],
                    data['modelo'],
                    data['equipo'],
                    data['cantidad'],
                    data['realizado_por'],
                    data['observaciones'],
                    data['fecha_actualizacion']
                )
            )

        registrar_historial(
            "AGREGAR INSUMO",
            f"Insumo agregado: {data['tipo_insumo']}",
            data['realizado_por']
        )

    @staticmethod
    def actualizar(item_id, data):
        with get_connection() as conn:
            conn.execute(
                """
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
                """,
                (
                    data['tipo_insumo'],
                    data['medidas'],
                    data['eficiencia'],
                    data['modelo'],
                    data['equipo'],
                    data['cantidad'],
                    data['observaciones'],
                    data['fecha_actualizacion'],
                    item_id
                )
            )

        registrar_historial(
            "MODIFICAR INSUMO",
            f"ID {item_id} actualizado",
            "Usuario"
        )

    @staticmethod
    def eliminar(item_id, usuario="Admin"):
        with get_connection() as conn:
            conn.execute(
                "DELETE FROM inventario WHERE id=?",
                (item_id,)
            )

        registrar_historial(
            "ELIMINAR INSUMO",
            f"ID eliminado: {item_id}",
            usuario
        )

import streamlit as st
import pandas as pd
from datetime import datetime

from database.init_db import init_db
from services.inventario_service import InventarioService
from utils.validators import validar_texto, validar_cantidad
from utils.security import validar_admin


st.set_page_config(
    page_title="Inventario TQ PRO",
    page_icon="📦",
    layout="wide"
)


init_db()


st.title("📦 Sistema Profesional de Inventarios")

menu = st.sidebar.selectbox(
    "Menú",
    [
        "Inicio",
        "Agregar Insumo",
        "Modificar Insumo",
        "Eliminar Insumo"
    ]
)


if menu == "Inicio":

    st.header("Dashboard")

    datos = InventarioService.obtener_todos()

    if datos:
        df = pd.DataFrame([dict(x) for x in datos])

        col1, col2 = st.columns(2)

        col1.metric("Total Insumos", len(df))

        stock_bajo = len(df[df['cantidad'] < 5])

        col2.metric("Stock Bajo", stock_bajo)

        st.subheader("Inventario")
        st.dataframe(df, use_container_width=True)

    else:
        st.info("No hay datos registrados")


elif menu == "Agregar Insumo":

    st.header("Agregar Nuevo Insumo")

    with st.form("agregar_form"):

        col1, col2 = st.columns(2)

        tipo = col1.text_input("Tipo Insumo")
        modelo = col1.text_input("Modelo")

        medidas = col2.text_input("Medidas")
        eficiencia = col2.text_input("Eficiencia")

        equipo = st.text_input("Equipo")

        cantidad = st.number_input(
            "Cantidad",
            min_value=0,
            step=1
        )

        realizado_por = st.text_input("Realizado por")

        observaciones = st.text_area("Observaciones")

        submit = st.form_submit_button("Guardar")

        if submit:

            if not validar_texto(tipo):
                st.error("Tipo de insumo inválido")

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

                InventarioService.agregar(data)

                st.success("✅ Insumo agregado correctamente")

                st.rerun()


elif menu == "Modificar Insumo":

    st.header("Modificar Insumo")

    datos = InventarioService.obtener_todos()

    if datos:

        df = pd.DataFrame([dict(x) for x in datos])

        opciones = df.apply(
            lambda x: f"{x['id']} - {x['tipo_insumo']}",
            axis=1
        ).tolist()

        seleccionado = st.selectbox(
            "Seleccione",
            opciones
        )

        item_id = int(seleccionado.split(" - ")[0])

        item = df[df['id'] == item_id].iloc[0]

        with st.form("editar_form"):

            tipo = st.text_input(
                "Tipo",
                value=item['tipo_insumo']
            )

            cantidad = st.number_input(
                "Cantidad",
                min_value=0,
                value=int(item['cantidad'])
            )

            submit = st.form_submit_button("Actualizar")

            if submit:

                data = {
                    'tipo_insumo': tipo,
                    'medidas': item['medidas'],
                    'eficiencia': item['eficiencia'],
                    'modelo': item['modelo'],
                    'equipo': item['equipo'],
                    'cantidad': int(cantidad),
                    'observaciones': item['observaciones'],
                    'fecha_actualizacion': datetime.now().strftime("%Y-%m-%d")
                }

                InventarioService.actualizar(item_id, data)

                st.success("✅ Actualizado correctamente")

                st.rerun()


elif menu == "Eliminar Insumo":

    st.header("Eliminar Insumo")

    datos = InventarioService.obtener_todos()

    if datos:

        df = pd.DataFrame([dict(x) for x in datos])

        opciones = df.apply(
            lambda x: f"{x['id']} - {x['tipo_insumo']}",
            axis=1
        ).tolist()

        seleccionado = st.selectbox(
            "Seleccione",
            opciones
        )

        password = st.text_input(
            "Contraseña admin",
            type="password"
        )

        if st.button("Eliminar"):

            if validar_admin(password):

                item_id = int(seleccionado.split(" - ")[0])

                InventarioService.eliminar(item_id)

                st.success("✅ Eliminado correctamente")

                st.rerun()

            else:
                st.error("❌ Contraseña incorrecta")
