import customtkinter as ctk
import pandas as pd
from conexion_base import conectar_bd
from tkinter import messagebox, filedialog

# Paleta "Bosque Profundo"
PALETA = {
    "fondo": "#051F20",
    "sidebar": "#173831",
    "botones": "#235347",
    "hover": "#2E6A5C",
    "texto": "#DBF0DD",
    "alerta": "#FF4444",
    "exito": "#2D5A27"
}

class SeccionProductos(ctk.CTkFrame):
    def __init__(self, master, rol):
        super().__init__(master, fg_color="transparent")
        self.rol = rol.lower()

        # --- CABECERA ---
        ctk.CTkLabel(self, text="📦 Control de Inventario Pro", 
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

        header_frame = ctk.CTkFrame(tab, fg_color=PALETA["botones"], corner_radius=5)
        header_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        # 🆕 Encabezados (Añadimos COSTO para admin/encargado)
        headers = [("ID", 40), ("PRODUCTO", 220), ("STOCK", 70), ("P. VENTA", 90)]
        if self.rol != "vendedor":
            headers.append(("P. COSTO", 90)) # Ver el costo en la lista
            headers.append(("ACCION", 60))

        for texto, ancho in headers:
            ctk.CTkLabel(header_frame, text=texto, width=ancho, font=("Roboto", 11, "bold"),
                         text_color=PALETA["texto"]).pack(side="left", padx=5)

        self.scroll_inventario = ctk.CTkScrollableFrame(tab, fg_color="#0A2A2B")
        self.scroll_inventario.pack(fill="both", expand=True, padx=10, pady=5)

    def actualizar_tabla(self, event=None):
        for widget in self.scroll_inventario.winfo_children(): widget.destroy()
        termino = self.entry_busqueda.get().strip()
        
        try:
            conn = conectar_bd()
            # 🆕 Traemos también el Precio_Costo
            query = "SELECT ID_Producto, Nombre, Stock, Precio, Precio_Costo FROM Productos WHERE Nombre LIKE ? LIMIT 30"
            df = pd.read_sql_query(query, conn, params=(f'%{termino}%',))
            conn.close()

            for _, r in df.iterrows():
                color_texto = PALETA["texto"]
                if r['Stock'] < 5: color_texto = PALETA["alerta"]

                fila = ctk.CTkFrame(self.scroll_inventario, fg_color="transparent")
                fila.pack(fill="x", pady=1)

                ctk.CTkLabel(fila, text=str(r['ID_Producto']), width=40, text_color=color_texto).pack(side="left", padx=5)
                ctk.CTkLabel(fila, text=str(r['Nombre']), width=220, anchor="w", text_color=color_texto).pack(side="left", padx=5)
                ctk.CTkLabel(fila, text=str(r['Stock']), width=70, text_color=color_texto).pack(side="left", padx=5)
                ctk.CTkLabel(fila, text=f"$ {r['Precio']:.2f}", width=90, text_color=color_texto).pack(side="left", padx=5)

                if self.rol != "vendedor":
                    # 🆕 Mostrar costo solo a superiores
                    ctk.CTkLabel(fila, text=f"$ {r['Precio_Costo']:.2f}", width=90, text_color="#AAB7B8").pack(side="left", padx=5)
                    ctk.CTkButton(fila, text="✏️", width=30, fg_color=PALETA["botones"], 
                                   command=lambda p=r: self.abrir_ventana_edicion(p)).pack(side="left", padx=5)
                
                ctk.CTkFrame(self.scroll_inventario, height=1, fg_color=PALETA["sidebar"]).pack(fill="x", padx=10)
        except Exception as e: print(f"Error: {e}")

    # --- 2. PESTAÑA: REPONER STOCK ---
    def setup_pestana_reponer(self):
        tab = self.tabview.tab("Reponer Stock")
        ctk.CTkLabel(tab, text="📥 Entrada de Mercancía", font=("Roboto", 20, "bold")).pack(pady=20)
        self.reponer_id = ctk.CTkEntry(tab, placeholder_text="ID del producto", width=300)
        self.reponer_id.pack(pady=10)
        self.reponer_cantidad = ctk.CTkEntry(tab, placeholder_text="Cantidad a añadir", width=300)
        self.reponer_cantidad.pack(pady=10)
        ctk.CTkButton(tab, text="Actualizar Existencias", fg_color=PALETA["exito"],
                      command=self.ejecutar_reposicion).pack(pady=20)

    def ejecutar_reposicion(self):
        idx, cant = self.reponer_id.get().strip(), self.reponer_cantidad.get().strip()
        if not idx or not cant: return
        try:
            conn = conectar_bd(); cursor = conn.cursor()
            cursor.execute("UPDATE Productos SET Stock = Stock + ? WHERE ID_Producto = ?", (int(cant), idx))
            if cursor.rowcount > 0:
                conn.commit()
                messagebox.showinfo("Éxito", "Stock actualizado")
                self.reponer_id.delete(0, 'end'); self.reponer_cantidad.delete(0, 'end')
                self.actualizar_tabla()
            conn.close()
        except: messagebox.showerror("Error", "Datos inválidos")

    # --- 3. PESTAÑA: NUEVO PRODUCTO ---
    def setup_pestana_nuevo(self):
        tab = self.tabview.tab("Nuevo Producto")
        ctk.CTkLabel(tab, text="Registro de Productos", font=("Roboto", 20, "bold")).pack(pady=15)

        self.entry_nombre = ctk.CTkEntry(tab, placeholder_text="Nombre del Producto", width=350)
        self.entry_nombre.pack(pady=5)
        self.entry_stock = ctk.CTkEntry(tab, placeholder_text="Stock Inicial", width=350)
        self.entry_stock.pack(pady=5)
        
        # 🆕 Campos de Precio (Costo vs Venta)
        f_precios = ctk.CTkFrame(tab, fg_color="transparent")
        f_precios.pack(pady=5)

        self.entry_costo = ctk.CTkEntry(f_precios, placeholder_text="Precio Costo (Tú compras)", width=170)
        self.entry_costo.pack(side="left", padx=5)
        
        self.entry_precio = ctk.CTkEntry(f_precios, placeholder_text="Precio Venta (Público)", width=170)
        self.entry_precio.pack(side="left", padx=5)

        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="+ Guardar Manual", fg_color=PALETA["botones"], command=self.guardar_producto).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="📊 Importar Excel", fg_color="#1D6F42", command=self.importar_desde_excel).pack(side="left", padx=10)

    def guardar_producto(self):
        nom, sto, pre, cos = self.entry_nombre.get(), self.entry_stock.get(), self.entry_precio.get(), self.entry_costo.get()
        if not all([nom, sto, pre, cos]): 
            messagebox.showwarning("Atención", "Llena todos los campos incluyendo el costo.")
            return
        try:
            conn = conectar_bd(); cursor = conn.cursor()
            # 🆕 INSERT con Precio_Costo
            cursor.execute("INSERT INTO Productos (Nombre, Stock, Precio, Precio_Costo) VALUES (?, ?, ?, ?)", 
                           (nom, int(sto), float(pre), float(cos)))
            conn.commit(); conn.close()
            messagebox.showinfo("Éxito", f"{nom} registrado")
            for e in [self.entry_nombre, self.entry_stock, self.entry_precio, self.entry_costo]: e.delete(0, 'end')
            self.actualizar_tabla()
        except Exception as e: messagebox.showerror("Error", f"Verifica los datos: {e}")

    def importar_desde_excel(self):
        ruta = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls")])
        if not ruta: return
        try:
            df = pd.read_excel(ruta)
            df.columns = df.columns.str.strip().str.lower()
            # 💡 Nota: El Excel ahora debe tener una columna 'precio_costo'
            conn = conectar_bd()
            df.to_sql('Productos', conn, if_exists='append', index=False)
            conn.close()
            messagebox.showinfo("Éxito", "¡Excel importado!")
            self.actualizar_tabla()
        except Exception as e: messagebox.showerror("Error Excel", f"Asegúrate de tener las columnas: nombre, stock, precio, precio_costo\n{e}")

    # --- 4. PESTAÑA: ALERTAS ---
    def setup_pestana_alertas(self):
        tab = self.tabview.tab("Alertas")
        ctk.CTkLabel(tab, text="⚠️ Stock Crítico", font=("Roboto", 20, "bold"), text_color=PALETA["alerta"]).pack(pady=20)
        self.scroll_alertas = ctk.CTkScrollableFrame(tab, fg_color="transparent", border_color=PALETA["alerta"], border_width=1)
        self.scroll_alertas.pack(fill="both", expand=True, padx=20, pady=10)
        ctk.CTkButton(tab, text="🔄 Escanear", command=self.mostrar_alertas_pandas).pack(pady=10)

    def mostrar_alertas_pandas(self):
        for w in self.scroll_alertas.winfo_children(): w.destroy()
        try:
            conn = conectar_bd()
            df = pd.read_sql_query("SELECT * FROM Productos WHERE Stock < 5", conn)
            conn.close()
            if df.empty: ctk.CTkLabel(self.scroll_alertas, text="✅ Todo en orden").pack(pady=20)
            for _, fila in df.iterrows():
                f = ctk.CTkFrame(self.scroll_alertas, fg_color="#3b201d")
                f.pack(fill="x", pady=2, padx=5)
                ctk.CTkLabel(f, text=f"⚠️ {fila['Nombre']}", width=200, anchor="w", text_color="#ff7675").pack(side="left", padx=10)
                ctk.CTkLabel(f, text=f"Stock: {fila['Stock']}").pack(side="right", padx=10)
        except Exception as e: print(e)

    # --- VENTANA EDICIÓN (Actualizada con Costo) ---
    def abrir_ventana_edicion(self, datos):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Editar Producto")
        ventana.geometry("350x450")
        ventana.grab_set()

        ctk.CTkLabel(ventana, text="Modificar Datos", font=("Roboto", 16, "bold")).pack(pady=20)
        
        en = ctk.CTkEntry(ventana, width=250, placeholder_text="Nombre"); en.insert(0, datos['Nombre']); en.pack(pady=5)
        es = ctk.CTkEntry(ventana, width=250, placeholder_text="Stock"); es.insert(0, str(datos['Stock'])); es.pack(pady=5)
        ep = ctk.CTkEntry(ventana, width=250, placeholder_text="P. Venta"); ep.insert(0, str(datos['Precio'])); ep.pack(pady=5)
        
        # 🆕 Campo de costo en la edición
        ec = ctk.CTkEntry(ventana, width=250, placeholder_text="P. Costo"); 
        ec.insert(0, str(datos['Precio_Costo'])); ec.pack(pady=5)

        def confirmar():
            try:
                conn = conectar_bd(); cursor = conn.cursor()
                # 🆕 UPDATE con Precio_Costo
                cursor.execute("""UPDATE Productos 
                                  SET Nombre=?, Stock=?, Precio=?, Precio_Costo=? 
                                  WHERE ID_Producto=?""", 
                               (en.get(), int(es.get()), float(ep.get()), float(ec.get()), datos['ID_Producto']))
                conn.commit(); conn.close()
                self.actualizar_tabla(); ventana.destroy()
                messagebox.showinfo("Éxito", "Producto actualizado")
            except Exception as e: messagebox.showerror("Error", f"Datos incorrectos\n{e}")

        ctk.CTkButton(ventana, text="Guardar Cambios", fg_color=PALETA["exito"], command=confirmar).pack(pady=25)