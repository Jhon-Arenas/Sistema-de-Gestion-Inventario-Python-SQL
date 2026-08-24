import customtkinter as ctk
import pandas as pd
from conexion_base import conectar_bd
from tkinter import messagebox, filedialog

# Paleta optimizada para Gestión de Inventario
PALETA = {
    "fondo": "#0D1B2A",      # Azul oscuro
    "sidebar": "#1B263B",    # Azul medianoche
    "botones": "#415A77",    # Azul acero
    "hover": "#778DA9",      # Gris azulado
    "texto": "#E0E1DD",      # Blanco hueso
    "peligro": "#9A031E",    # Rojo vino
    "exito": "#2D5A27",      # Verde bosque
    "resalte": "#CCAD1F",    # Amarillo/Dorado
    "alerta": "#E67E22"      # Naranja
}

class SeccionProductos(ctk.CTkFrame):
    def __init__(self, master, rol):
        super().__init__(master, fg_color="transparent")
        self.rol = rol.lower()

        # --- CABECERA ---
        ctk.CTkLabel(self, text="📦 Control de Inventario", 
                     font=("Roboto", 28, "bold"), 
                     text_color=PALETA["texto"]).pack(pady=20)

        # --- ORGANIZADOR POR PESTAÑAS ---
        self.tabview = ctk.CTkTabview(self, 
                                      segmented_button_selected_color=PALETA["botones"],
                                      segmented_button_selected_hover_color=PALETA["hover"],
                                      text_color=PALETA["texto"])
        self.tabview.pack(padx=20, pady=10, fill="both", expand=True)

        # Pestañas según rol
        self.tabview.add("Stock Actual")
        self.setup_pestana_stock() 

        if self.rol in ["administrador", "encargado"]:
            self.tabview.add("Reponer Stock")
            self.tabview.add("Nuevo Producto")
            self.tabview.add("Alertas")

            self.setup_pestana_reponer()  
            self.setup_pestana_nuevo() 
            self.setup_pestana_alertas()
        
        self.actualizar_tabla()

    # --- 1. PESTAÑA: STOCK ACTUAL ---
    def setup_pestana_stock(self):
        tab = self.tabview.tab("Stock Actual")
        
        search_frame = ctk.CTkFrame(tab, fg_color="transparent")
        search_frame.pack(pady=10, fill="x", padx=10)

        self.entry_busqueda = ctk.CTkEntry(search_frame, placeholder_text="🔍 Buscar producto...", 
                                          fg_color=PALETA["sidebar"], border_color=PALETA["botones"])
        self.entry_busqueda.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_busqueda.bind("<KeyRelease>", lambda e: self.actualizar_tabla())

        ctk.CTkButton(search_frame, text="🔄", width=40, 
                      fg_color=PALETA["botones"], command=self.actualizar_tabla).pack(side="right")

        # --- ENCABEZADO DE TABLA ---
        self.header_frame = ctk.CTkFrame(tab, fg_color=PALETA["botones"], corner_radius=5)
        self.header_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        ctk.CTkLabel(self.header_frame, text="ID", width=50, font=("Roboto", 11, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(self.header_frame, text="PRODUCTO", font=("Roboto", 11, "bold"), anchor="w").pack(side="left", padx=10, expand=True, fill="x")
        ctk.CTkLabel(self.header_frame, text="STOCK", width=70, font=("Roboto", 11, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(self.header_frame, text="P. VENTA", width=90, font=("Roboto", 11, "bold")).pack(side="left", padx=5)

        if self.rol != "vendedor":
            ctk.CTkLabel(self.header_frame, text="P. COSTO", width=90, font=("Roboto", 11, "bold")).pack(side="left", padx=5)
            ctk.CTkLabel(self.header_frame, text="ACCIÓN", width=110, font=("Roboto", 11, "bold")).pack(side="left", padx=5)

        self.scroll_inventario = ctk.CTkScrollableFrame(tab, fg_color="#0A2A2B")
        self.scroll_inventario.pack(fill="both", expand=True, padx=10, pady=5)

    def actualizar_tabla(self, event=None):
        for widget in self.scroll_inventario.winfo_children(): widget.destroy()
        termino = self.entry_busqueda.get().strip()
        
        try:
            conn = conectar_bd()
            query = "SELECT ID_Producto, Nombre, Stock, Precio, Precio_Costo FROM Productos WHERE Nombre LIKE ? LIMIT 30"
            df = pd.read_sql_query(query, conn, params=(f'%{termino}%',))
            conn.close()

            for idx, r in df.iterrows():
                color_texto = PALETA["texto"]
                if r['Stock'] < 5: color_texto = PALETA["alerta"]

                fila = ctk.CTkFrame(self.scroll_inventario, fg_color=PALETA["sidebar"] if idx % 2 == 0 else "transparent")
                fila.pack(fill="x", pady=1, padx=5)

                ctk.CTkLabel(fila, text=str(r['ID_Producto']), width=50, text_color=color_texto).pack(side="left", padx=5)
                ctk.CTkLabel(fila, text=str(r['Nombre']), anchor="w", text_color=color_texto, font=("Roboto", 13)).pack(side="left", padx=10, expand=True, fill="x")
                ctk.CTkLabel(fila, text=str(r['Stock']), width=70, text_color=color_texto, font=("Roboto", 12, "bold")).pack(side="left", padx=5)
                ctk.CTkLabel(fila, text=f"$ {r['Precio']:.2f}", width=90, text_color=color_texto).pack(side="left", padx=5)

                if self.rol != "vendedor":
                    ctk.CTkLabel(fila, text=f"$ {r['Precio_Costo']:.2f}", width=90, text_color="#AAB7B8").pack(side="left", padx=5)
                    
                    # Contenedor de acciones
                    f_acciones = ctk.CTkFrame(fila, fg_color="transparent", width=110)
                    f_acciones.pack(side="left", padx=5)

                    # Se extrae el ID numérico directo
                    id_prod = int(r['ID_Producto'])

                    # Botón Editar
                    ctk.CTkButton(f_acciones, text="✏️", width=30, height=25, fg_color=PALETA["botones"], 
                                   command=lambda id_p=id_prod: self.abrir_ventana_edicion(id_p)).pack(side="left", padx=2)
                    
                    # Botón Reservar
                    ctk.CTkButton(f_acciones, text="📌", width=30, height=25, fg_color=PALETA["resalte"], 
                                   command=lambda p=r.to_dict(): self.solicitar_reserva(p)).pack(side="left", padx=2)
                
        except Exception as e: print(f"Error: {e}")

    # --- VENTANA DE EDICIÓN ---
    # --- VENTANA DE EDICIÓN ---
    def abrir_ventana_edicion(self, id_producto):
        try:
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute("SELECT ID_Producto, Nombre, Stock, Precio, Precio_Costo FROM Productos WHERE ID_Producto = ?", (id_producto,))
            datos = cursor.fetchone()
            conn.close()

            if not datos:
                messagebox.showerror("Error", "No se encontró el producto en la base de datos.")
                return

            prod_id, nombre, stock, precio, costo = datos

        except Exception as e:
            messagebox.showerror("Error de conexión", f"No se pudieron cargar los datos: {e}")
            return

        # 1. Crear ventana emergente
        ventana = ctk.CTkToplevel(self)
        ventana.title(f"Editando: {nombre}")
        ventana.geometry("400x520")
        ventana.configure(fg_color=PALETA["sidebar"])
        
        # Vincular con la ventana principal para mantener orden jerárquico
        ventana.transient(self.winfo_toplevel())

        # 2. Construir los widgets PRIMERO
        ctk.CTkLabel(ventana, text="✏️ Modificar Producto", font=("Roboto", 20, "bold"), text_color=PALETA["texto"]).pack(pady=15)
        
        ctk.CTkLabel(ventana, text="Nombre del producto:", text_color=PALETA["texto"]).pack(anchor="w", padx=50)
        en = ctk.CTkEntry(ventana, width=300, height=35)
        en.insert(0, str(nombre))
        en.pack(pady=(2, 8))

        ctk.CTkLabel(ventana, text="Stock actual:", text_color=PALETA["texto"]).pack(anchor="w", padx=50)
        es = ctk.CTkEntry(ventana, width=300, height=35)
        es.insert(0, str(stock))
        es.pack(pady=(2, 8))

        ctk.CTkLabel(ventana, text="Precio de Venta ($):", text_color=PALETA["texto"]).pack(anchor="w", padx=50)
        ep = ctk.CTkEntry(ventana, width=300, height=35)
        ep.insert(0, str(precio))
        ep.pack(pady=(2, 8))

        ctk.CTkLabel(ventana, text="Precio de Costo ($):", text_color=PALETA["texto"]).pack(anchor="w", padx=50)
        ec = ctk.CTkEntry(ventana, width=300, height=35)
        ec.insert(0, str(costo))
        ec.pack(pady=(2, 8))

        def confirmar():
            try:
                conn = conectar_bd()
                cursor = conn.cursor()
                cursor.execute("""UPDATE Productos 
                                  SET Nombre=?, Stock=?, Precio=?, Precio_Costo=? 
                                  WHERE ID_Producto=?""", 
                               (en.get().strip(), int(es.get().strip()), float(ep.get().strip()), float(ec.get().strip()), prod_id))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Éxito", "Producto actualizado correctamente.")
                self.actualizar_tabla()
                ventana.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Verifica los datos ingresados:\n{e}")

        ctk.CTkButton(ventana, text="💾 Guardar Cambios", fg_color=PALETA["exito"], 
                      height=40, width=200, command=confirmar).pack(pady=20)

        # 3. Forzar el renderizado completo ANTES de bloquear interacción
        ventana.update_idletasks()
        ventana.grab_set()
        ventana.focus_force()
        

    # --- LÓGICA DE RESERVA ---
    def solicitar_reserva(self, producto_dict):
        id_prod = producto_dict['ID_Producto']
        nombre_prod = producto_dict['Nombre']
        stock_actual = producto_dict['Stock']

        dialogo_cliente = ctk.CTkInputDialog(
            text=f"Reservar '{nombre_prod}'\nStock disponible: {stock_actual}\n\nIngresa el nombre del Cliente:", 
            title="Reservar Producto"
        )
        nombre_cliente = dialogo_cliente.get_input()

        if not nombre_cliente or not nombre_cliente.strip():
            return

        dialogo_cant = ctk.CTkInputDialog(
            text=f"¿Cuántas unidades deseas reservar para {nombre_cliente}?", 
            title="Cantidad a Reservar"
        )
        cant_str = dialogo_cant.get_input()

        if not cant_str or not cant_str.isdigit():
            messagebox.showwarning("Atención", "Ingresa un número entero válido.")
            return

        cantidad = int(cant_str)

        if cantidad <= 0:
            messagebox.showwarning("Atención", "La cantidad debe ser mayor a 0.")
            return

        if cantidad > stock_actual:
            messagebox.showwarning("Stock Insuficiente", f"No puedes reservar {cantidad} unidades. Stock disponible: {stock_actual}")
            return

        try:
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Pedidos (Tipo, Nombre_Entidad, Producto, Cantidad, Estado) VALUES (?, ?, ?, ?, ?)",
                ("Cliente", nombre_cliente.strip(), id_prod, cantidad, "Pendiente")
            )
            conn.commit()
            conn.close()

            messagebox.showinfo("Éxito", f"Reserva registrada para {nombre_cliente} ({cantidad} unidad/es).")
            
            try:
                self.master.master.master.actualizar_badge_pedidos()
            except: pass

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la reserva: {e}")

    # --- 2. PESTAÑA: REPONER STOCK ---
    def setup_pestana_reponer(self):
        tab = self.tabview.tab("Reponer Stock")
        ctk.CTkLabel(tab, text="📥 Entrada de Mercancía", font=("Roboto", 22, "bold"), text_color=PALETA["texto"]).pack(pady=30)
        
        self.reponer_id = ctk.CTkEntry(tab, placeholder_text="ID del producto", width=350, height=40)
        self.reponer_id.pack(pady=10)
        
        self.reponer_cantidad = ctk.CTkEntry(tab, placeholder_text="Cantidad a añadir", width=350, height=40)
        self.reponer_cantidad.pack(pady=10)
        
        ctk.CTkButton(tab, text="Actualizar Existencias", font=("Roboto", 14, "bold"),
                      fg_color=PALETA["exito"], height=45, width=350,
                      command=self.ejecutar_reposicion).pack(pady=30)

    def ejecutar_reposicion(self):
        idx, cant = self.reponer_id.get().strip(), self.reponer_cantidad.get().strip()
        if not idx or not cant: return
        try:
            conn = conectar_bd(); cursor = conn.cursor()
            cursor.execute("UPDATE Productos SET Stock = Stock + ? WHERE ID_Producto = ?", (int(cant), idx))
            if cursor.rowcount > 0:
                conn.commit()
                messagebox.showinfo("Éxito", "Stock actualizado correctamente.")
                self.reponer_id.delete(0, 'end'); self.reponer_cantidad.delete(0, 'end')
                self.actualizar_tabla()
            else:
                messagebox.showwarning("Error", "No se encontró un producto con ese ID.")
            conn.close()
        except: messagebox.showerror("Error", "Asegúrate de ingresar solo números.")

    # --- 3. PESTAÑA: NUEVO PRODUCTO ---
    def setup_pestana_nuevo(self):
        tab = self.tabview.tab("Nuevo Producto")
        ctk.CTkLabel(tab, text="Registro de Productos", font=("Roboto", 22, "bold"), text_color=PALETA["texto"]).pack(pady=20)

        self.entry_nombre = ctk.CTkEntry(tab, placeholder_text="Nombre del Producto", width=400, height=35)
        self.entry_nombre.pack(pady=8)
        
        self.entry_stock = ctk.CTkEntry(tab, placeholder_text="Stock Inicial", width=400, height=35)
        self.entry_stock.pack(pady=8)
        
        f_precios = ctk.CTkFrame(tab, fg_color="transparent")
        f_precios.pack(pady=10)

        self.entry_costo = ctk.CTkEntry(f_precios, placeholder_text="Costo Compra ($)", width=195, height=35)
        self.entry_costo.pack(side="left", padx=5)
        
        self.entry_precio = ctk.CTkEntry(f_precios, placeholder_text="Precio Venta ($)", width=195, height=35)
        self.entry_precio.pack(side="left", padx=5)

        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(pady=30)
        
        ctk.CTkButton(btn_frame, text="+ Guardar Manual", width=180, height=40,
                      fg_color=PALETA["botones"], command=self.guardar_producto).pack(side="left", padx=10)
        
        ctk.CTkButton(btn_frame, text="📊 Importar Excel", width=180, height=40,
                      fg_color="#1D6F42", command=self.importar_desde_excel).pack(side="left", padx=10)

    def guardar_producto(self):
        nom, sto, pre, cos = self.entry_nombre.get(), self.entry_stock.get(), self.entry_precio.get(), self.entry_costo.get()
        if not all([nom, sto, pre, cos]): 
            messagebox.showwarning("Atención", "Rellena todos los campos incluyendo el costo.")
            return
        try:
            conn = conectar_bd(); cursor = conn.cursor()
            cursor.execute("INSERT INTO Productos (Nombre, Stock, Precio, Precio_Costo) VALUES (?, ?, ?, ?)", 
                           (nom, int(sto), float(pre), float(cos)))
            conn.commit(); conn.close()
            messagebox.showinfo("Éxito", f"Producto '{nom}' registrado.")
            for e in [self.entry_nombre, self.entry_stock, self.entry_precio, self.entry_costo]: e.delete(0, 'end')
            self.actualizar_tabla()
        except Exception as e: messagebox.showerror("Error", f"Verifica los datos: {e}")

    def importar_desde_excel(self):
        ruta = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls")])
        if not ruta: return
        try:
            df = pd.read_excel(ruta)
            df.columns = df.columns.str.strip().str.lower()
            conn = conectar_bd()
            df.to_sql('Productos', conn, if_exists='append', index=False)
            conn.close()
            messagebox.showinfo("Éxito", "¡Inventario cargado desde Excel!")
            self.actualizar_tabla()
        except Exception as e: 
            messagebox.showerror("Error Excel", f"El Excel debe tener: nombre, stock, precio, precio_costo\n{e}")

    # --- 4. PESTAÑA: ALERTAS ---
    def setup_pestana_alertas(self):
        tab = self.tabview.tab("Alertas")
        ctk.CTkLabel(tab, text="⚠️ Stock Crítico", font=("Roboto", 24, "bold"), text_color=PALETA["alerta"]).pack(pady=20)
        
        self.scroll_alertas = ctk.CTkScrollableFrame(tab, fg_color="transparent", border_color=PALETA["alerta"], border_width=1)
        self.scroll_alertas.pack(fill="both", expand=True, padx=40, pady=10)
        
        ctk.CTkButton(tab, text="🔄 Escanear Inventario", fg_color=PALETA["botones"], 
                      command=self.mostrar_alertas_pandas).pack(pady=20)

    def mostrar_alertas_pandas(self):
        for w in self.scroll_alertas.winfo_children(): w.destroy()
        try:
            conn = conectar_bd()
            df = pd.read_sql_query("SELECT * FROM Productos WHERE Stock < 5", conn)
            conn.close()
            
            if df.empty: 
                ctk.CTkLabel(self.scroll_alertas, text="✅ Todo el stock está en niveles óptimos.", 
                             text_color=PALETA["exito"], font=("Roboto", 14)).pack(pady=40)
                return

            for _, fila in df.iterrows():
                f = ctk.CTkFrame(self.scroll_alertas, fg_color="#3b201d")
                f.pack(fill="x", pady=3, padx=10)
                
                ctk.CTkLabel(f, text=f"⚠️ {fila['Nombre']}", anchor="w", 
                             text_color="#ff7675", font=("Roboto", 13, "bold")).pack(side="left", padx=15, expand=True, fill="x")
                
                ctk.CTkLabel(f, text=f"Stock actual: {fila['Stock']}", 
                             text_color="white").pack(side="right", padx=20)
        except Exception as e: print(e)