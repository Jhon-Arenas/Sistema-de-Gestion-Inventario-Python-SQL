import customtkinter as ctk
from conexion_base import conectar_bd
from tkinter import messagebox

PALETA = {
    "fondo": "#051F20",
    "sidebar": "#173831",
    "botones": "#235347",
    "hover": "#2E6A5C",
    "texto": "#DBF0DD",
    "alerta": "#FF4444",
    "exito": "#27ae60",
    "resalte": "#E67E22"
}

class SeccionPedidos(ctk.CTkFrame):
    def __init__(self, master, rol):
        super().__init__(master, fg_color="transparent")
        self.rol = rol.lower()

        # 1. TÍTULO
        self.lbl_titulo = ctk.CTkLabel(self, text="📝 Gestión de Pedidos con Stock en Vivo", 
                                       font=("Roboto", 28, "bold"), text_color=PALETA["texto"])
        self.lbl_titulo.pack(pady=20)

        # 2. FORMULARIO
        self.frame_formulario = ctk.CTkFrame(self, fg_color=PALETA["sidebar"], corner_radius=15)
        self.frame_formulario.pack(fill="x", padx=40, pady=10)

        self.tipo_var = ctk.StringVar(value="Cliente")
        self.seg_button = ctk.CTkSegmentedButton(self.frame_formulario, 
                                                 values=["Cliente", "Proveedor"],
                                                 variable=self.tipo_var,
                                                 selected_color=PALETA["resalte"])
        self.seg_button.pack(pady=(15, 0))

        self.f_inputs = ctk.CTkFrame(self.frame_formulario, fg_color="transparent")
        self.f_inputs.pack(pady=10)

        self.entry_entidad = ctk.CTkEntry(self.f_inputs, placeholder_text="Nombre Cliente/Prov...", width=180)
        self.entry_entidad.pack(side="left", padx=5)

        self.entry_id_prod = ctk.CTkEntry(self.f_inputs, placeholder_text="ID Prod.", width=80)
        self.entry_id_prod.pack(side="left", padx=5)
        self.entry_id_prod.bind("<KeyRelease>", self.buscar_nombre_producto)

        self.entry_cantidad = ctk.CTkEntry(self.f_inputs, placeholder_text="Cant.", width=70)
        self.entry_cantidad.pack(side="left", padx=5)

        self.btn_guardar = ctk.CTkButton(self.f_inputs, text="💾 Registrar", 
                                         fg_color=PALETA["botones"], command=self.registrar_pedido)
        self.btn_guardar.pack(side="left", padx=10)

        self.lbl_info_prod = ctk.CTkLabel(self.frame_formulario, text="Introduce un ID válido", 
                                          font=("Roboto", 12, "italic"), text_color=PALETA["resalte"])
        self.lbl_info_prod.pack(pady=(0, 10))

        # 3. TABLA (CABECERA)
        self.frame_header = ctk.CTkFrame(self, fg_color=PALETA["botones"], corner_radius=5)
        self.frame_header.pack(fill="x", padx=40, pady=(20, 0))

        # --- CAMBIO AQUÍ: Añadimos "Stock Act." a la lista de columnas ---
        columnas = [
            ("ID", 40), ("Tipo", 80), ("Entidad", 130), 
            ("Producto", 130), ("Cant.", 50), ("Stock Act.", 80), 
            ("Estado", 90), ("Acción", 110)
        ]
        
        for texto, ancho in columnas:
            lbl = ctk.CTkLabel(self.frame_header, text=texto, width=ancho, font=("Roboto", 11, "bold"), text_color=PALETA["texto"])
            lbl.pack(side="left", padx=5)

        self.tabla_pedidos = ctk.CTkScrollableFrame(self, fg_color="#0A2A2B", corner_radius=15)
        self.tabla_pedidos.pack(pady=(0, 20), padx=40, fill="both", expand=True)

        self.actualizar_lista_pedidos()

    def buscar_nombre_producto(self, event):
        id_buscado = self.entry_id_prod.get()
        if id_buscado.isdigit():
            try:
                conn = conectar_bd()
                cursor = conn.cursor()
                cursor.execute("SELECT Nombre, Stock FROM Productos WHERE ID_Producto = ?", (id_buscado,))
                resultado = cursor.fetchone()
                conn.close()
                if resultado:
                    # --- CAMBIO AQUÍ: También mostramos el stock en la etiqueta de confirmación ---
                    self.lbl_info_prod.configure(text=f"✅ {resultado[0]} (Stock actual: {resultado[1]})", text_color="#27ae60")
                else:
                    self.lbl_info_prod.configure(text="❌ ID no existe", text_color="#FF4444")
            except: pass
        else:
            self.lbl_info_prod.configure(text="Introduce solo números", text_color=PALETA["alerta"])

    def actualizar_lista_pedidos(self):
        for widget in self.tabla_pedidos.winfo_children():
            widget.destroy()

        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            
            # --- CAMBIO AQUÍ: El INNER JOIN ahora también trae 'prod.Stock' ---
            query = """
                SELECT p.ID_Pedido, p.Tipo, p.Nombre_Entidad, prod.Nombre, p.Cantidad, p.Estado, prod.Stock 
                FROM Pedidos p
                INNER JOIN Productos prod ON p.Producto = prod.ID_Producto
                WHERE p.Estado = 'Pendiente'
            """
            cursor.execute(query)
            filas = cursor.fetchall()

            for fila in filas:
                f_row = ctk.CTkFrame(self.tabla_pedidos, fg_color=PALETA["sidebar"], height=45)
                f_row.pack(fill="x", pady=2, padx=5)

                ctk.CTkLabel(f_row, text=fila[0], width=40).pack(side="left", padx=5)
                ctk.CTkLabel(f_row, text=fila[1], width=80).pack(side="left", padx=5)
                ctk.CTkLabel(f_row, text=fila[2], width=130, anchor="w").pack(side="left", padx=5)
                ctk.CTkLabel(f_row, text=fila[3], width=130, anchor="w").pack(side="left", padx=5)
                ctk.CTkLabel(f_row, text=fila[4], width=50).pack(side="left", padx=5)
                
                # --- CAMBIO AQUÍ: Nueva celda que muestra el Stock que hay actualmente en la tabla Productos ---
                stock_actual = fila[6]
                color_stock = PALETA["texto"] if stock_actual >= fila[4] else "#FF4444"
                ctk.CTkLabel(f_row, text=stock_actual, width=80, text_color=color_stock, font=("Roboto", 11, "bold")).pack(side="left", padx=5)

                ctk.CTkLabel(f_row, text=fila[5], width=90, text_color="#E67E22").pack(side="left", padx=5)

                btn_texto = "📥 Recibir" if fila[1] == "Proveedor" else "✔️ Entregar"
                btn_check = ctk.CTkButton(f_row, text=btn_texto, width=110, height=28,
                                          fg_color=PALETA["exito"] if fila[1] == "Proveedor" else "#2980b9",
                                          command=lambda p=fila[0]: self.completar_pedido_directo(p))
                btn_check.pack(side="right", padx=10)

            conexion.close()
        except Exception as e:
            print(f"Error en tabla: {e}")

    def registrar_pedido(self):
        # ... (Este método se mantiene igual que el anterior, usando el ID_Producto)
        tipo = self.tipo_var.get()
        entidad = self.entry_entidad.get()
        id_p = self.entry_id_prod.get()
        cant = self.entry_cantidad.get()

        if not entidad or not id_p or not cant:
            messagebox.showwarning("Atención", "Rellena todos los campos Rick.")
            return

        try:
            conexion = conectar_bd() 
            cursor = conexion.cursor()
            cursor.execute("INSERT INTO Pedidos (Tipo, Nombre_Entidad, Producto, Cantidad, Estado) VALUES (?, ?, ?, ?, ?)", 
                           (tipo, entidad, id_p, int(cant), "Pendiente"))
            conexion.commit()
            conexion.close() 

            self.entry_id_prod.delete(0, 'end')
            self.entry_entidad.delete(0, 'end')
            self.entry_cantidad.delete(0, 'end')
            self.lbl_info_prod.configure(text="Introduce un ID válido")
            self.actualizar_lista_pedidos()
            self.notificar_al_main()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    def completar_pedido_directo(self, id_ped):
        # ... (Este método se mantiene igual, ya funciona con ID)
        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            cursor.execute("SELECT Tipo, Producto, Cantidad FROM Pedidos WHERE ID_Pedido = ?", (id_ped,))
            res = cursor.fetchone()

            if res:
                tipo, id_producto, cant = res
                if tipo == "Cliente":
                    cursor.execute("UPDATE Productos SET Stock = Stock - ? WHERE ID_Producto = ? AND Stock >= ?", 
                                   (cant, id_producto, cant))
                    if cursor.rowcount == 0:
                        messagebox.showwarning("Stock Insuficiente", "No hay suficiente stock para completar la entrega.")
                        conexion.close()
                        return
                else:
                    cursor.execute("UPDATE Productos SET Stock = Stock + ? WHERE ID_Producto = ?", (cant, id_producto))

                cursor.execute("UPDATE Pedidos SET Estado = 'Completado' WHERE ID_Pedido = ?", (id_ped,))
                conexion.commit()
                messagebox.showinfo("Éxito", "Inventario actualizado.")
            
            conexion.close()
            self.actualizar_lista_pedidos()
            self.notificar_al_main()
        except Exception as e:
            messagebox.showerror("Error", f"Fallo: {e}")

    def notificar_al_main(self):
        try:
            objetivo = self.master.master.master
            if hasattr(objetivo, 'actualizar_badge_pedidos'):
                objetivo.actualizar_badge_pedidos()
        except: pass
        