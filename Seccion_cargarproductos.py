import customtkinter as ctk
import pandas as pd
from conexion_base import conectar_bd
from tkinter import messagebox
from tkinter import filedialog

class SeccionInventario(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        # 1. Título
        self.titulo = ctk.CTkLabel(self, text="📦 Gestión de Inventario", font=("Roboto", 24, "bold"))
        self.titulo.pack(pady=20)

        # 2. El Tabview
        self.tabview = ctk.CTkTabview(self, width=600, corner_radius=10)
        self.tabview.pack(padx=20, pady=10, fill="both", expand=True)

        self.tabview.add("Stock Actual")
        self.tabview.add("Reponer Stock")#NUEVA PESTAÑA
        self.tabview.add("Gestionar Producto")
        self.tabview.add("Alertas")

        # LLAMADAS A LAS FUNCIONES
        self.setup_pestana_stock() 
        self.setup_pestana_reponer()  
        self.setup_pestana_gestion() 
        self.setup_pestana_alertas()

    # --- PESTAÑA: REPONER STOCK (NUEVA) ---
    def setup_pestana_reponer(self):
        tab = self.tabview.tab("Reponer Stock")
        
        ctk.CTkLabel(tab, text="📥 Entrada de Mercancía", font=("Roboto", 18, "bold")).pack(pady=15)

        # 1. Buscador simple para encontrar el producto a reponer
        self.reponer_nombre = ctk.CTkEntry(tab, placeholder_text="Escribe nombre del producto...", width=300)
        self.reponer_nombre.pack(pady=10)
        
        # 2. Cantidad a sumar
        self.reponer_cantidad = ctk.CTkEntry(tab, placeholder_text="Cantidad a añadir (ej: 10, 50...)", width=300)
        self.reponer_cantidad.pack(pady=10)

        self.btn_actualizar_stock = ctk.CTkButton(tab, text="Actualizar Existencias", 
                                               fg_color="#2ecc71", 
                                               command=self.ejecutar_reposicion)
        self.btn_actualizar_stock.pack(pady=20)

    def ejecutar_reposicion(self):
        nombre = self.reponer_nombre.get().strip()
        cantidad = self.reponer_cantidad.get().strip()

        if not nombre or not cantidad:
            messagebox.showwarning("Atención", "Escribe el nombre exacto y la cantidad.")
            return

        try:
            cantidad_int = int(cantidad)
            conexion = conectar_bd()
            cursor = conexion.cursor()
            
            # RAZONAMIENTO: Usamos UPDATE para sumar al valor actual
            query = "UPDATE Productos SET Stock = Stock + ? WHERE Nombre = ?"
            cursor.execute(query, (cantidad_int, nombre))
            
            if cursor.rowcount > 0:
                conexion.commit()
                messagebox.showinfo("Éxito", f"Se añadieron {cantidad_int} unidades a {nombre}.")
                self.reponer_nombre.delete(0, 'end')
                self.reponer_cantidad.delete(0, 'end')
                self.mostrar_inventario_pro() # Refresca la tabla
            else:
                messagebox.showwarning("Error", "No se encontró un producto con ese nombre.")
            
            conexion.close()
        except ValueError:
            messagebox.showerror("Error", "La cantidad debe ser un número entero.")
        except Exception as e:
            messagebox.showerror("Error", f"{e}")

    # --- CORRECCIÓN DE ALINEACIÓN EN STOCK ACTUAL ---
    def setup_pestana_stock(self):
        tab = self.tabview.tab("Stock Actual")
        frame_control = ctk.CTkFrame(tab, fg_color="transparent")
        frame_control.pack(fill="x", padx=10, pady=10)

        self.entry_busqueda = ctk.CTkEntry(frame_control, placeholder_text="🔍 Buscar...", width=300)
        self.entry_busqueda.pack(side="left", padx=5)
        self.entry_busqueda.bind("<KeyRelease>", self.filtrar_inventario_tiempo_real)

        self.btn_refrescar = ctk.CTkButton(frame_control, text="🔄", width=40, command=self.mostrar_inventario_pro)
        self.btn_refrescar.pack(side="right")

        # RAZONAMIENTO: Los anchos deben ser iguales aquí y en la función de dibujo
        header_frame = ctk.CTkFrame(tab, fg_color="gray20")
        header_frame.pack(fill="x", padx=10)
        
        ctk.CTkLabel(header_frame, text="ID", width=50).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="PRODUCTO", width=250, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="STOCK", width=80).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="PRECIO", width=100).pack(side="left", padx=5)

        self.scroll_inventario = ctk.CTkScrollableFrame(tab, fg_color="transparent", height=300)
        self.scroll_inventario.pack(fill="both", expand=True, padx=10, pady=5)

    def actualizar_lista_visual(self, dataframe):
        for widget in self.scroll_inventario.winfo_children():
            widget.destroy()
        
        # RAZONAMIENTO: Usamos anchos fijos idénticos al Header
        for _, fila in dataframe.iterrows():
            row = ctk.CTkFrame(self.scroll_inventario, fg_color="transparent")
            row.pack(fill="x", pady=1)
            
            stock_val = int(fila['Stock'])
            color_stock = "#e74c3c" if stock_val < 5 else "white"

            ctk.CTkLabel(row, text=str(fila['ID_Producto']), width=50).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=str(fila['Nombre']), width=250, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=str(stock_val), width=80, text_color=color_stock).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=f"${float(fila['Precio']):.2f}", width=100).pack(side="left", padx=5)
            
            ctk.CTkFrame(self.scroll_inventario, height=1, fg_color="gray30").pack(fill="x", padx=10)

    # --- PESTAÑA 2: GESTIONAR (TU LÓGICA DE CARGA) ---
    def setup_pestana_gestion(self):
        tab = self.tabview.tab("Gestionar Producto")
        ctk.CTkLabel(tab, text="Cargar Nuevo Producto", font=("Roboto", 18, "bold")).pack(pady=15)

        self.entry_nombre = ctk.CTkEntry(tab, placeholder_text="Nombre del Producto", width=300)
        self.entry_nombre.pack(pady=10)
        self.entry_stock = ctk.CTkEntry(tab, placeholder_text="Stock Inicial", width=300)
        self.entry_stock.pack(pady=10)
        self.entry_precio = ctk.CTkEntry(tab, placeholder_text="Precio Unitario", width=300)
        self.entry_precio.pack(pady=10)

        self.frame_botones = ctk.CTkFrame(tab, fg_color="transparent")
        self.frame_botones.pack(pady=20)

        self.btn_añadir = ctk.CTkButton(self.frame_botones, text="+ Añadir", fg_color="#0A98A0", command=self.guardar_producto)
        self.btn_añadir.pack(side="left", padx=10)

        # --- NUEVO BOTÓN DE EXCEL ---
        self.btn_importar = ctk.CTkButton(self.frame_botones, text="📊 Importar Excel", fg_color="#1D6F42", command=self.importar_desde_excel)
        self.btn_importar.pack(side="left", padx=10)

    # --- PESTAÑA 3: ALERTAS (PROFESIONAL) ---
    def setup_pestana_alertas(self):
        tab = self.tabview.tab("Alertas")
        ctk.CTkLabel(tab, text="⚠️ Productos con Stock Crítico (< 5 unidades)", font=("Roboto", 18, "bold"), text_color="#e74c3c").pack(pady=10)
        
        self.btn_check_alertas = ctk.CTkButton(tab, text="🔍 Revisar Estado Crítico", fg_color="#e67e22", command=self.mostrar_alertas_pandas)
        self.btn_check_alertas.pack(pady=10)

        self.scroll_alertas = ctk.CTkScrollableFrame(tab, fg_color="transparent", height=250, border_color="#e74c3c", border_width=1)
        self.scroll_alertas.pack(fill="both", expand=True, padx=10, pady=5)

    # --- MÉTODOS DE LÓGICA (PANDAS Y DB) ---
    # --- MÉTODOS DE LÓGICA (CORREGIDOS) ---
    def filtrar_inventario_tiempo_real(self, event):
        texto_busqueda = self.entry_busqueda.get().strip() # .strip() quita espacios accidentales

        # 1. Si está vacío, mostramos el top 100 y cortamos ejecución
        if not texto_busqueda:
            self.mostrar_inventario_pro()
            return

        try:
            conexion = conectar_bd()
            # RAZONAMIENTO: Usamos LIMIT 50 para que el buscador sea instantáneo
            query = "SELECT ID_Producto, Nombre, Stock, Precio FROM Productos WHERE Nombre LIKE ? LIMIT 50"
            df_filtrado = pd.read_sql_query(query, conexion, params=(f'%{texto_busqueda}%',))
            conexion.close()

            # 2. Solo actualizamos si hay resultados para no limpiar la pantalla en vano
            self.actualizar_lista_visual(df_filtrado)

        except Exception as e:
            print(f"Error en buscador: {e}")

    def mostrar_inventario_pro(self):
        try:
            conexion = conectar_bd()
            # RAZONAMIENTO: El inventario general siempre debe estar limitado para no explotar la RAM
            query = "SELECT ID_Producto, Nombre, Stock, Precio FROM Productos LIMIT 100"
            df = pd.read_sql_query(query, conexion)
            conexion.close()

            self.actualizar_lista_visual(df) # Usamos la misma función de dibujo siempre

        except Exception as e:
            print(f"Error al cargar inventario: {e}")

    def mostrar_alertas_pandas(self):
        # Limpiar scroll de alertas
        for widget in self.scroll_alertas.winfo_children():
            widget.destroy()

        try:
            conexion = conectar_bd()
            df = pd.read_sql_query("SELECT * FROM Productos", conexion)
            conexion.close()

            # FILTRO PANDAS: Solo lo que tenga menos de 5
            criticos = df[df['Stock'] < 5]

            if criticos.empty:
                ctk.CTkLabel(self.scroll_alertas, text="✅ Todo en orden. No hay stock bajo.").pack(pady=20)
            else:
                for _, fila in criticos.iterrows():
                    f = ctk.CTkFrame(self.scroll_alertas, fg_color="#3b201d") # Fondo rojizo sutil
                    f.pack(fill="x", pady=2, padx=5)
                    ctk.CTkLabel(f, text=f"⚠️ {fila['Nombre']}", width=250, anchor="w", text_color="#ff7675").pack(side="left", padx=10)
                    ctk.CTkLabel(f, text=f"Quedan: {fila['Stock']}", font=("Roboto", 12, "bold")).pack(side="right", padx=10)

        except Exception as e:
            messagebox.showerror("Error", f"{e}")

    def guardar_producto(self):
        nombre = self.entry_nombre.get()
        stock = self.entry_stock.get()
        precio = self.entry_precio.get()

        if not nombre or not stock or not precio:
            messagebox.showwarning("Atención", "Completa todos los campos.")
            return

        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            query = "INSERT INTO Productos (Nombre, Stock, Precio) VALUES (?, ?, ?)"
            cursor.execute(query, (nombre, int(stock), float(precio)))
            conexion.commit()
            conexion.close()
            messagebox.showinfo("Éxito", f"Producto '{nombre}' guardado.")
            self.entry_nombre.delete(0, 'end'); self.entry_stock.delete(0, 'end'); self.entry_precio.delete(0, 'end')
        except Exception as e:
            messagebox.showerror("Error", f"{e}")

    def importar_desde_excel(self):
        ruta_archivo = filedialog.askopenfilename(
            title="Selecciona el inventario viejo",
            filetypes=[("Archivos de Excel", "*.xlsx *.xls")]
        )

        if not ruta_archivo:
            return

        conexion = None  # 1. TRUCO DE R: Inicializamos en None para evitar el error
        try:
            # 2. Leer y normalizar el Excel
            df = pd.read_excel(ruta_archivo)
            df.columns = df.columns.str.strip().str.lower()
            
            # 3. Abrir la conexión
            conexion = conectar_bd()

            # 4. CARGA MASIVA
            # Asegúrate que las columnas en el Excel se llamen: nombre, stock, precio
            df.to_sql('Productos', conexion, if_exists='append', index=False)
            
            # 5. Guardar cambios y avisar
            conexion.commit()
            self.mostrar_inventario_pro() 
            messagebox.showinfo("Éxito", "¡Inventario cargado a máxima velocidad!")

        except Exception as e:
            messagebox.showerror("Error de Carga", f"Detalle del error: {e}")
        
        finally:
            # 6. Esto SIEMPRE se ejecuta: Cerramos solo si se logró abrir
            if conexion:
                conexion.close()