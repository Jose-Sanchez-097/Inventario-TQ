import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# ==========================================
# CLASE MODELO: Representa un Insumo
# ==========================================
class Insumo:
    def __init__(self, id_insumo, tipo, medidas, eficiencia, clase, equipo, cantidad_actual, verificado_por, observaciones=""):
        self.id = id_insumo
        self.tipo = tipo
        self.medidas = medidas
        self.eficiencia = eficiencia  
        self.clase = clase            
        self.equipo = equipo          # Cambiado de categoria a equipo
        self.cantidad_actual = cantidad_actual
        self.verificado_por = verificado_por
        self.observaciones = observaciones

    def actualizar_datos_restringidos(self, cantidad_actual, verificado_por, observaciones):
        """ Solo permite modificar cantidad, verificador y observaciones """
        self.cantidad_actual = cantidad_actual
        self.verificado_por = verificado_por
        self.observaciones = observaciones


# ==========================================
# CLASE VISTA/CONTROLADOR: Interfaz Gráfica
# ==========================================
class InventarioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión de Inventario TQ - Control de Stock")
        self.root.geometry("1200x750")
        self.root.configure(bg="#f5f6fa")

        # Base de datos en memoria
        self.inventario = {}
        self.historial = []  
        self.id_counter = 1
        self.MAX_MOVIMIENTOS = 50
        self.CONTRASENA_SEGURIDAD = "TQ2026"  # Clave para historial y eliminación
        self.id_en_edicion = None

        self.crear_estilos()
        self.crear_componentes()

    def crear_estilos(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.style.configure("TLabel", font=("Helvetica", 10), bg="#f5f6fa", fg="#2f3640")
        self.style.configure("TButton", font=("Helvetica", 10, "bold"), padding=6)
        self.style.configure("Treeview", font=("Helvetica", 10), rowheight=25, background="#ffffff")
        self.style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"), background="#dcdde1", foreground="#2f3640")
        self.style.map("Treeview", background=[("selected", "#353b48")], foreground=[("selected", "#ffffff")])

    def registrar_movimiento(self, tipo_accion, id_item, detalle):
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        registro = (fecha_hora, tipo_accion, f"ID: {id_item}", detalle)
        self.historial.insert(0, registro)
        if len(self.historial) > self.MAX_MOVIMIENTOS:
            self.historial = self.historial[:self.MAX_MOVIMIENTOS]
        self.actualizar_tabla_historial()

    def crear_componentes(self):
        main_frame = tk.Frame(self.root, bg="#f5f6fa")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # --- TÍTULO ---
        title = tk.Label(main_frame, text="CONTROL DE INVENTARIO E HISTORIAL TQ", font=("Helvetica", 16, "bold"), bg="#f5f6fa", fg="#2f3640")
        title.pack(anchor="w", pady=(0, 10))

        # --- PANEL SUPERIOR: FORMULARIO ---
        self.form_frame = tk.LabelFrame(main_frame, text=" Datos del Insumo ", font=("Helvetica", 11, "bold"), bg="#f5f6fa", fg="#353b48", padx=15, pady=15)
        self.form_frame.pack(fill=tk.X, pady=(0, 10))

        # Variables de control para los Inputs
        self.var_tipo = tk.StringVar()
        self.var_medidas = tk.StringVar()
        self.var_eficiencia = tk.StringVar()
        self.var_clase = tk.StringVar()
        self.var_equipo = tk.StringVar()  # Cambiado de var_categoria a var_equipo
        self.var_cantidad = tk.StringVar()
        self.var_verificado = tk.StringVar()
        self.var_observaciones = tk.StringVar()

        # Diseño de Entradas del Formulario
        ttk.Label(self.form_frame, text="Tipo de Insumo:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_tipo = ttk.Entry(self.form_frame, textvariable=self.var_tipo, width=22)
        self.entry_tipo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.form_frame, text="Medidas:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.entry_medidas = ttk.Entry(self.form_frame, textvariable=self.var_medidas, width=22)
        self.entry_medidas.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(self.form_frame, text="Eficiencia:").grid(row=0, column=4, sticky="w", padx=5, pady=5)
        self.entry_eficiencia = ttk.Entry(self.form_frame, textvariable=self.var_eficiencia, width=22)
        self.entry_eficiencia.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(self.form_frame, text="Clase:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.entry_clase = ttk.Entry(self.form_frame, textvariable=self.var_clase, width=22)
        self.entry_clase.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self.form_frame, text="Equipo:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.entry_equipo = ttk.Entry(self.form_frame, textvariable=self.var_equipo, width=22)
        self.entry_equipo.grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(self.form_frame, text="Cantidad Actual:").grid(row=1, column=4, sticky="w", padx=5, pady=5)
        self.entry_cantidad = ttk.Entry(self.form_frame, textvariable=self.var_cantidad, width=22)
        self.entry_cantidad.grid(row=1, column=5, padx=5, pady=5)

        ttk.Label(self.form_frame, text="Verificado Por:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.entry_verificado = ttk.Entry(self.form_frame, textvariable=self.var_verificado, width=22)
        self.entry_verificado.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(self.form_frame, text="Observaciones:").grid(row=2, column=2, sticky="w", padx=5, pady=5)
        self.entry_observaciones = ttk.Entry(self.form_frame, textvariable=self.var_observaciones, width=54)
        self.entry_observaciones.grid(row=2, column=3, columnspan=3, sticky="w", padx=5, pady=5)

        # --- BOTONES DE ACCIÓN ---
        btn_frame = tk.Frame(main_frame, bg="#f5f6fa")
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        self.btn_guardar = ttk.Button(btn_frame, text="Agregar Insumo", command=self.guardar_insumo)
        self.btn_guardar.pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="Modificar Seleccionado", command=self.cargar_insumo_seleccionado).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Eliminar (Requiere Clave)", command=self.solicitar_clave_eliminacion).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Limpiar / Cancelar", command=self.limpiar_campos).pack(side=tk.LEFT, padx=5)

        # --- PANEL DE BÚSQUEDA / FILTRADO ---
        search_frame = tk.LabelFrame(main_frame, text=" Filtrar Datos e Inventario ", font=("Helvetica", 10, "bold"), bg="#f5f6fa", fg="#2f3640", padx=10, pady=5)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="Buscar Item:").pack(side=tk.LEFT, padx=5)
        self.var_buscar = tk.StringVar()
        self.var_buscar.trace_add("write", lambda *args: self.actualizar_tabla_vista())
        self.entry_buscar = ttk.Entry(search_frame, textvariable=self.var_buscar, width=40)
        self.entry_buscar.pack(side=tk.LEFT, padx=5, pady=5)
        
        lbl_nota_alerta = tk.Label(search_frame, text="■ Alerta Stock Crítico (< 5 unidades)", fg="#ff7f50", bg="#f5f6fa", font=("Helvetica", 9, "bold"))
        lbl_nota_alerta.pack(side=tk.RIGHT, padx=10)

        # --- PANEL INFERIOR: PESTAÑAS (TABS) ---
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # PESTAÑA 1: INVENTARIO
        self.tab_inventario = tk.Frame(self.notebook, bg="#ffffff")
        self.notebook.add(self.tab_inventario, text=" Inventario Actual ")
        self.configurar_tabla_inventario()

        # PESTAÑA 2: HISTORIAL
        self.tab_historial = tk.Frame(self.notebook, bg="#ffffff")
        self.notebook.add(self.tab_historial, text=" Historial de Movimientos ")
        self.configurar_tabla_historial()

    def configurar_tabla_inventario(self):
        tabla_frame = tk.Frame(self.tab_inventario)
        tabla_frame.pack(fill=tk.BOTH, expand=True)

        columnas = ("id", "tipo", "medidas", "eficiencia", "clase", "equipo", "cant_actual", "verificado", "observaciones")
        self.tabla = ttk.Treeview(tabla_frame, columns=columnas, show="headings")
        
        self.tabla.heading("id", text="ID")
        self.tabla.heading("tipo", text="Tipo Insumo")
        self.tabla.heading("medidas", text="Medidas")
        self.tabla.heading("eficiencia", text="Eficiencia")
        self.tabla.heading("clase", text="Clase")
        self.tabla.heading("equipo", text="Equipo")
        self.tabla.heading("cant_actual", text="Cant. Actual")
        self.tabla.heading("verificado", text="Verificado Por")
        self.tabla.heading("observaciones", text="Observaciones")

        self.tabla.column("id", width=40, anchor="center")
        self.tabla.column("tipo", width=130)
        self.tabla.column("medidas", width=90)
        self.tabla.column("eficiencia", width=90, anchor="center")
        self.tabla.column("clase", width=100)
        self.tabla.column("equipo", width=120)
        self.tabla.column("cant_actual", width=90, anchor="center")
        self.tabla.column("verificado", width=120)
        self.tabla.column("observaciones", width=200)

        self.tabla.tag_configure("alerta_naranja", background="#ffebdb", foreground="#d35400")

        scroll_y = ttk.Scrollbar(tabla_frame, orient=tk.VERTICAL, command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        self.tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tabla.bind("<Double-1>", lambda event: self.cargar_insumo_seleccionado())

    def configurar_tabla_historial(self):
        top_bar = tk.Frame(self.tab_historial, bg="#f5f6fa", pady=5, padx=5)
        top_bar.pack(fill=tk.X)
        
        ttk.Button(top_bar, text="Borrar Historial (Requiere Clave)", command=self.solicitar_borrado_historial).pack(side=tk.RIGHT)
        tk.Label(top_bar, text="Muestra las últimas 50 operaciones", font=("Helvetica", 9, "italic"), bg="#f5f6fa", fg="#7f8c8d").pack(side=tk.LEFT, padx=5)

        historial_frame = tk.Frame(self.tab_historial)
        historial_frame.pack(fill=tk.BOTH, expand=True)

        columnas_h = ("fecha", "accion", "item", "detalle")
        self.tabla_historial = ttk.Treeview(historial_frame, columns=columnas_h, show="headings")
        
        self.tabla_historial.heading("fecha", text="Fecha / Hora")
        self.tabla_historial.heading("accion", text="Acción")
        self.tabla_historial.heading("item", text="Elemento")
        self.tabla_historial.heading("detalle", text="Detalle del Movimiento")

        self.tabla_historial.column("fecha", width=150, anchor="center")
        self.tabla_historial.column("accion", width=120, anchor="center")
        self.tabla_historial.column("item", width=100, anchor="center")
        self.tabla_historial.column("detalle", width=650)

        scroll_h_y = ttk.Scrollbar(historial_frame, orient=tk.VERTICAL, command=self.tabla_historial.yview)
        self.tabla_historial.configure(yscrollcommand=scroll_h_y.set)
        self.tabla_historial.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_h_y.pack(side=tk.RIGHT, fill=tk.Y)

    # ==========================================
    # LÓGICA DE CONTROL, SEGURIDAD Y FILTRADO
    # ==========================================
    def actualizar_tabla_vista(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        
        filtro = self.var_buscar.get().lower()
        
        for insumo in self.inventario.values():
            match = [
                str(insumo.id), insumo.tipo.lower(), insumo.medidas.lower(),
                insumo.eficiencia.lower(), insumo.clase.lower(), insumo.equipo.lower(),
                str(insumo.cantidad_actual), insumo.verificado_por.lower(), insumo.observaciones.lower()
            ]
            
            if any(filtro in campo for campo in match):
                try:
                    cant_num = float(insumo.cantidad_actual)
                    tag_alerta = "alerta_naranja" if cant_num < 5 else ""
                except ValueError:
                    tag_alerta = ""  
                
                self.tabla.insert("", tk.END, values=(
                    insumo.id, insumo.tipo, insumo.medidas, insumo.eficiencia,
                    insumo.clase, insumo.equipo, insumo.cantidad_actual,
                    insumo.verificado_por, insumo.observaciones
                ), tags=(tag_alerta,))

    def actualizar_tabla_historial(self):
        for item in self.tabla_historial.get_children():
            self.tabla_historial.delete(item)
        for mov in self.historial:
            self.tabla_historial.insert("", tk.END, values=mov)

    def guardar_insumo(self):
        if not self.var_tipo.get() or not self.var_verificado.get() or not self.var_cantidad.get():
            messagebox.showwarning("Campos incompletos", "Por favor ingresa Tipo de Insumo, Cantidad y Verificado Por.")
            return

        if self.id_en_edicion is None:
            # CREAR NUEVO INSUMO
            nuevo_insumo = Insumo(
                id_insumo=self.id_counter,
                tipo=self.var_tipo.get(),
                medidas=self.var_medidas.get(),
                eficiencia=self.var_eficiencia.get(),
                clase=self.var_clase.get(),
                equipo=self.var_equipo.get(),
                cantidad_actual=self.var_cantidad.get(),
                verificado_por=self.var_verificado.get(),
                observaciones=self.var_observaciones.get()
            )
            self.inventario[self.id_counter] = nuevo_insumo
            
            detalles = f"Creado: {nuevo_insumo.tipo} | Equipo: {nuevo_insumo.equipo} | Stock: {nuevo_insumo.cantidad_actual} | Por: {nuevo_insumo.verificado_por}"
            self.registrar_movimiento("REGISTRO", self.id_counter, detalles)
            self.id_counter += 1
        else:
            # MODIFICAR EXISTENTE
            insumo = self.inventario[self.id_en_edicion]
            cambios = f"Modificado -> Cant. Anterior: {insumo.cantidad_actual} a Nueva Cant.: {self.var_cantidad.get()} | Modificó: {self.var_verificado.get()}"
            
            insumo.actualizar_datos_restringidos(
                cantidad_actual=self.var_cantidad.get(),
                verificado_por=self.var_verificado.get(),
                observaciones=self.var_observaciones.get()
            )
            self.registrar_movimiento("MODIFICACIÓN", self.id_en_edicion, cambios)
            self.id_en_edicion = None
            self.btn_guardar.config(text="Agregar Insumo")
            self.cambiar_estado_campos("normal") 

        self.actualizar_tabla_vista()
        self.limpiar_campos()

    def cargar_insumo_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Selección requerida", "Selecciona un registro de la lista de inventario.")
            return

        valores = self.tabla.item(seleccion[0], 'values')
        id_insumo = int(valores[0])
        insumo = self.inventario[id_insumo]

        self.id_en_edicion = id_insumo
        self.var_tipo.set(insumo.tipo)
        self.var_medidas.set(insumo.medidas)
        self.var_eficiencia.set(insumo.eficiencia)
        self.var_clase.set(insumo.clase)
        self.var_equipo.set(insumo.equipo)
        self.var_cantidad.set(insumo.cantidad_actual)
        self.var_verificado.set(insumo.verificado_por)
        self.var_observaciones.set(insumo.observaciones)

        self.btn_guardar.config(text="Actualizar Cambios")
        self.cambiar_estado_campos("disabled")

    def cambiar_estado_campos(self, estado):
        """ Controla la edición del formulario para bloquear o habilitar columnas """
        self.entry_tipo.config(state=estado)
        self.entry_medidas.config(state=estado)
        self.entry_eficiencia.config(state=estado)
        self.entry_clase.config(state=estado)
        self.entry_equipo.config(state=estado)

    def solicitar_clave_eliminacion(self):
        """ Ventana intermedia para requerir contraseña antes de eliminar """
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Selección requerida", "Selecciona el insumo que deseas eliminar.")
            return

        valores = self.tabla.item(seleccion[0], 'values')
        id_insumo = int(valores[0])
        
        # Levantar ventana de confirmación de contraseña
        win_pass_del = tk.Toplevel(self.root)
        win_pass_del.title("Autorización de Eliminación")
        win_pass_del.geometry("320x130")
        win_pass_del.resizable(False, False)
        win_pass_del.configure(bg="#f5f6fa")
        win_pass_del.transient(self.root)
        win_pass_del.grab_set()

        tk.Label(win_pass_del, text=f"Clave de seguridad para eliminar ID {id_insumo}: ", bg="#f5f6fa").pack(pady=10)
        entry_pass = ttk.Entry(win_pass_del, show="*", width=25)
        entry_pass.pack(pady=5)
        entry_pass.focus()

        def ejecutar_eliminacion():
            if entry_pass.get() == self.CONTRASENA_SEGURIDAD:
                insumo = self.inventario[id_insumo]
                detalles_el = f"Eliminado: {insumo.tipo} | Estaba asignado a Equipo: {insumo.equipo} | Cargo: {insumo.verificado_por}"
                self.registrar_movimiento("ELIMINACIÓN", id_insumo, detalles_el)
                
                del self.inventario[id_insumo]
                self.cambiar_estado_campos("normal")
                self.actualizar_tabla_vista()
                self.limpiar_campos()
                messagebox.showinfo("Éxito", f"El registro con ID {id_insumo} fue eliminado.")
                win_pass_del.destroy()
            else:
                messagebox.showerror("Acceso Denegado", "Contraseña incorrecta. Eliminación cancelada.")
                win_pass_del.destroy()

        ttk.Button(win_pass_del, text="Confirmar Eliminación", command=ejecutar_eliminacion).pack(pady=5)

    def solicitar_borrado_historial(self):
        win_password = tk.Toplevel(self.root)
        win_password.title("Seguridad")
        win_password.geometry("300x120")
        win_password.resizable(False, False)
        win_password.configure(bg="#f5f6fa")
        win_password.transient(self.root)
        win_password.grab_set()

        tk.Label(win_password, text="Introduce la contraseña para borrar:", bg="#f5f6fa").pack(pady=10)
        entry_pass = ttk.Entry(win_password, show="*", width=25)
        entry_pass.pack(pady=5)
        entry_pass.focus()

        def verificar_clave():
            if entry_pass.get() == self.CONTRASENA_SEGURIDAD:
                self.historial.clear()
                self.actualizar_tabla_historial()
                messagebox.showinfo("Éxito", "Historial eliminado.")
                win_password.destroy()
            else:
                messagebox.showerror("Acceso Denegado", "Contraseña incorrecta.")
                win_password.destroy()

        ttk.Button(win_password, text="Confirmar", command=verificar_clave).pack(pady=5)

    def limpiar_campos(self):
        self.id_en_edicion = None
        self.cambiar_estado_campos("normal")  
        self.var_tipo.set("")
        self.var_medidas.set("")
        self.var_eficiencia.set("")
        self.var_clase.set("")
        self.var_equipo.set("")
        self.var_cantidad.set("")
        self.var_verificado.set("")
        self.var_observaciones.set("")
        self.btn_guardar.config(text="Agregar Insumo")
        self.entry_tipo.focus()


# ==========================================
# INICIO DE LA APLICACIÓN
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = InventarioApp(root)
    root.mainloop()
    
