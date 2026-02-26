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
    def __init__(self, master, rol): # <--- 1. RECIBIMOS EL ROL
        super().__init__(master, fg_color="transparent")
        self.rol = rol.lower()

        # --- CABECERA ---
        self.titulo = ctk.CTkLabel(self, text="📦 Control de Inventario Pro", 
                                   font=("Roboto", 28, "bold"), 
                                   text_color=PALETA["texto"])
        self.titulo.pack(pady=20)

        # --- ORGANIZADOR POR PESTAÑAS ---
        self.tabview = ctk.CTkTabview(self, 
                                      segmented_button_selected_color=PALETA["botones"],
                                      segmented_button_selected_hover_color=PALETA["hover"],
                                      text_color=PALETA["texto"])
        self.tabview.pack(padx=20, pady=10, fill="both", expand=True)

        # --- 2. FILTRO DE PESTAÑAS SEGÚN ROL ---
        # Todos ven el Stock
        self.tabview.add("Stock Actual")
        self.setup_pestana_stock() 

        # Solo Admin y Encargado ven el resto
        if self.rol in ["administrador", "encargado"]:
            self.tabview.add("Reponer Stock")
            self.tabview.add("Nuevo Producto")
            self.tabview.add("Alertas")

            self.setup_pestana_reponer()  
            self.setup_pestana_nuevo() 
            self.setup_pestana_alertas()
        
        # Carga inicial de datos
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

        btn_refrescar = ctk.CTkButton(search_frame, text="🔄", width=40, 
                                      fg_color=PALETA["botones"], command=self.actualizar_tabla)
        btn_refrescar.pack(side="right")

        header_frame = ctk.CTkFrame(tab, fg_color=PALETA["botones"], corner_radius=5)
        header_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        # Ajustamos el ancho de los encabezados si quitamos el botón de acción
        headers = [("ID", 50), ("PRODUCTO", 250), ("STOCK", 80), ("PRECIO", 100)]
        if self.rol != "vendedor":
            headers.append(("ACCION", 80))

        for texto, ancho in headers:
            ctk.CTkLabel(header_frame, text=texto, width=ancho, font=("Roboto", 12, "bold"),
                         text_color=PALETA["texto"]).pack(side="left", padx=5)

        self.scroll_inventario = ctk.CTkScrollableFrame(tab, fg_color="#0A2A2B")
        self.scroll_inventario.pack(fill="both", expand=True, padx=10, pady=5)

    def actualizar_tabla(self, event=None):
        for widget in self.scroll_inventario.winfo_children():
            widget.destroy()

        termino = self.entry_busqueda.get().strip()
        
        try:
            conexion = conectar_bd()
            query = "SELECT ID_Producto, Nombre, Stock, Precio FROM Productos WHERE Nombre LIKE ? LIMIT 20"
            df = pd.read_sql_query(query, conexion, params=(f'%{termino}%',))
            conexion.close()

            for _, r in df.iterrows():
                color_texto = PALETA["texto"]
                if r['Stock'] < 5: color_texto = PALETA["alerta"]

                fila = ctk.CTkFrame(self.scroll_inventario, fg_color="transparent")
                fila.pack(fill="x", pady=1)

                ctk.CTkLabel(fila, text=str(r['ID_Producto']), width=50, text_color=color_texto).pack(side="left", padx=5)
                ctk.CTkLabel(fila, text=str(r['Nombre']), width=250, anchor="w", text_color=color_texto).pack(side="left", padx=5)
                ctk.CTkLabel(fila, text=str(r['Stock']), width=80, text_color=color_texto).pack(side="left", padx=5)
                ctk.CTkLabel(fila, text=f"$ {float(r['Precio']):.2f}", width=100, text_color=color_texto).pack(side="left", padx=5)

                # --- 3. FILTRO DE BOTÓN DE EDICIÓN ---
                if self.rol != "vendedor":
                    ctk.CTkButton(fila, text="✏️", width=30, fg_color=PALETA["botones"], 
                                   command=lambda p=r: self.abrir_ventana_edicion(p)).pack(side="left", padx=5)
                
                ctk.CTkFrame(self.scroll_inventario, height=1, fg_color=PALETA["sidebar"]).pack(fill="x", padx=10)
        
        except Exception as e: 
            print(f"Error en tabla: {e}")

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
        idx = self.reponer_id.get().strip()
        cant = self.reponer_cantidad.get().strip()
        if not idx or not cant: return
        try:
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute("UPDATE Productos SET Stock = Stock + ? WHERE ID_Producto = ?", (int(cant), idx))
            if cursor.rowcount > 0:
                conn.commit()
                messagebox.showinfo("Éxito", f"Stock actualizado para ID {idx}")
                self.reponer_id.delete(0, 'end')
                self.reponer_cantidad.delete(0, 'end')
                self.actualizar_tabla()
            else:
                messagebox.showwarning("Error", "ID no encontrado")
            conn.close()
        except: messagebox.showerror("Error", "Ingresa valores válidos")

    # --- 3. PESTAÑA: NUEVO PRODUCTO ---
    def setup_pestana_nuevo(self):
        tab = self.tabview.tab("Nuevo Producto")
        ctk.CTkLabel(tab, text="Registro de Productos", font=("Roboto", 20, "bold")).pack(pady=20)

        self.entry_nombre = ctk.CTkEntry(tab, placeholder_text="Nombre del Producto", width=300)
        self.entry_nombre.pack(pady=10)
        self.entry_stock = ctk.CTkEntry(tab, placeholder_text="Stock Inicial", width=300)
        self.entry_stock.pack(pady=10)
        self.entry_precio = ctk.CTkEntry(tab, placeholder_text="Precio Unitario", width=300)
        self.entry_precio.pack(pady=10)

        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="+ Guardar Manual", fg_color=PALETA["botones"], 
                      command=self.guardar_producto).pack(side="left", padx=10)
        
        ctk.CTkButton(btn_frame, text="📊 Importar Excel", fg_color="#1D6F42", 
                      command=self.importar_desde_excel).pack(side="left", padx=10)

    def guardar_producto(self):
        nom, sto, pre = self.entry_nombre.get(), self.entry_stock.get(), self.entry_precio.get()
        if not nom or not sto or not pre: return
        try:
            conn = conectar_bd(); cursor = conn.cursor()
            cursor.execute("INSERT INTO Productos (Nombre, Stock, Precio) VALUES (?, ?, ?)", (nom, int(sto), float(pre)))
            conn.commit(); conn.close()
            messagebox.showinfo("Éxito", f"{nom} guardado")
            self.entry_nombre.delete(0, 'end'); self.entry_stock.delete(0, 'end'); self.entry_precio.delete(0, 'end')
            self.actualizar_tabla()
        except Exception as e: messagebox.showerror("Error", str(e))

    def importar_desde_excel(self):
        ruta = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls")])
        if not ruta: return
        try:
            df = pd.read_excel(ruta)
            df.columns = df.columns.str.strip().str.lower()
            conn = conectar_bd()
            df.to_sql('Productos', conn, if_exists='append', index=False)
            conn.commit(); conn.close()
            messagebox.showinfo("Éxito", "¡Excel importado!")
            self.actualizar_tabla()
        except Exception as e: messagebox.showerror("Error Excel", f"Revisa las columnas\n{e}")

    # --- 4. PESTAÑA: ALERTAS ---
    def setup_pestana_alertas(self):
        tab = self.tabview.tab("Alertas")
        ctk.CTkLabel(tab, text="⚠️ Estado Crítico de Inventario", font=("Roboto", 20, "bold"), 
                     text_color=PALETA["alerta"]).pack(pady=20)
        
        self.scroll_alertas = ctk.CTkScrollableFrame(tab, fg_color="transparent", border_color=PALETA["alerta"], border_width=1)
        self.scroll_alertas.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkButton(tab, text="🔄 Escanear Inventario", command=self.mostrar_alertas_pandas).pack(pady=10)

    def mostrar_alertas_pandas(self):
        for w in self.scroll_alertas.winfo_children(): w.destroy()
        try:
            conn = conectar_bd()
            df = pd.read_sql_query("SELECT * FROM Productos WHERE Stock < 5", conn)
            conn.close()
            if df.empty:
                ctk.CTkLabel(self.scroll_alertas, text="✅ Todo en orden").pack(pady=20)
            for _, fila in df.iterrows():
                f = ctk.CTkFrame(self.scroll_alertas, fg_color="#3b201d")
                f.pack(fill="x", pady=2, padx=5)
                ctk.CTkLabel(f, text=f"⚠️ {fila['Nombre']}", width=200, anchor="w", text_color="#ff7675").pack(side="left", padx=10)
                ctk.CTkLabel(f, text=f"Stock: {fila['Stock']}").pack(side="right", padx=10)
        except Exception as e: print(e)

    # --- VENTANA EDICIÓN ---
    def abrir_ventana_edicion(self, datos):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Editar")
        ventana.geometry("300x350")
        ventana.grab_set()

        ctk.CTkLabel(ventana, text="Editar Producto", font=("Roboto", 16, "bold")).pack(pady=20)
        en = ctk.CTkEntry(ventana, width=200); en.insert(0, datos['Nombre']); en.pack(pady=5)
        es = ctk.CTkEntry(ventana, width=200); es.insert(0, str(datos['Stock'])); es.pack(pady=5)
        ep = ctk.CTkEntry(ventana, width=200); ep.insert(0, str(datos['Precio'])); ep.pack(pady=5)

        def confirmar():
            try:
                conn = conectar_bd(); cursor = conn.cursor()
                cursor.execute("UPDATE Productos SET Nombre=?, Stock=?, Precio=? WHERE ID_Producto=?", 
                               (en.get(), int(es.get()), float(ep.get()), datos['ID_Producto']))
                conn.commit(); conn.close()
                self.actualizar_tabla(); ventana.destroy()
                messagebox.showinfo("Éxito", "Actualizado")
            except Exception as e: messagebox.showerror("Error", f"Revisa los campos\n{e}")

        ctk.CTkButton(ventana, text="Guardar", fg_color=PALETA["exito"], command=confirmar).pack(pady=20)
