import customtkinter as ctk
from conexion_base import conectar_bd
from tkinter import messagebox

class SeccionProductos(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        # --- CABECERA ---
        self.titulo = ctk.CTkLabel(self, text="📦 Control de Inventario", font=("Roboto", 24, "bold"))
        self.titulo.pack(pady=10)

        # --- BUSCADOR ---
        self.search_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.search_frame.pack(pady=10, fill="x", padx=20)

        self.entry_busqueda = ctk.CTkEntry(self.search_frame, placeholder_text="🔍 Buscar producto por nombre...", width=400)
        self.entry_busqueda.pack(side="left", padx=10)
        
        # Filtrado dinámico
        self.entry_busqueda.bind("<KeyRelease>", self.filtrar_dinamico)

        # --- TABLA ---
        # 1. Contenedor principal
        self.tabla_container = ctk.CTkScrollableFrame(self, fg_color="#1e1e1e", corner_radius=10)
        self.tabla_container.pack(expand=True, fill="both", padx=20, pady=10)

        # 2. Encabezados fijos
        self.crear_encabezado()
        
        # 3. Frame DONDE VIVIRÁN LAS FILAS (Esto facilita limpiar solo los datos)
        self.frame_datos = ctk.CTkFrame(self.tabla_container, fg_color="transparent")
        self.frame_datos.pack(fill="both", expand=True)

        # Cargar datos iniciales
        self.actualizar_tabla()

    def filtrar_dinamico(self, event):
        # Razonamiento: Capturamos el evento para llamar a la tabla
        self.actualizar_tabla()

    def crear_encabezado(self):
        header_frame = ctk.CTkFrame(self.tabla_container, fg_color="#333333", corner_radius=5)
        header_frame.pack(fill="x", pady=(0, 5))
        
        # RAZONAMIENTO: Los anchos deben coincidir exactamente con los de la tabla de datos
        # (ID, PRODUCTO, STOCK, PRECIO, ESTADO)
        headers = [("ID", 50), ("PRODUCTO", 250), ("STOCK", 80), ("PRECIO", 100), ("ESTADO", 120)]
        for texto, ancho in headers:
            # Usamos anchor="w" en PRODUCTO y ESTADO para que el título también esté a la izquierda
            anclaje = "w" if texto in ["PRODUCTO", "ESTADO"] else "center"
            lbl = ctk.CTkLabel(header_frame, text=texto, width=ancho, font=("Roboto", 12, "bold"), anchor=anclaje)
            lbl.pack(side="left", padx=5, pady=5)

    def actualizar_tabla(self):
        for widget in self.frame_datos.winfo_children():
            widget.destroy()

        termino = self.entry_busqueda.get().strip()

        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            query = """SELECT ID_Producto, Nombre, Stock, Precio 
                       FROM Productos 
                       WHERE Nombre LIKE ? 
                       ORDER BY Nombre ASC LIMIT 50"""
            cursor.execute(query, ('%' + termino + '%',))
            resultados = cursor.fetchall()

            for r in resultados:
                # 1. Configuración de la fila de datos
                color_texto = "#FFFFFF"
                status_text = "✅ Ok"
                if r[2] < 5:
                    color_texto = "#FF4444"
                    status_text = "⚠️ Bajo Stock"

                # 2. CREAR LA FILA (Solo una vez)
                fila = ctk.CTkFrame(self.frame_datos, fg_color="transparent")
                fila.pack(fill="x", pady=1)

                # 3. INSERTAR DATOS (Con los mismos anchos del encabezado)
                ctk.CTkLabel(fila, text=str(r[0]), width=50).pack(side="left", padx=5)
                ctk.CTkLabel(fila, text=str(r[1]), width=250, anchor="w").pack(side="left", padx=5)
                ctk.CTkLabel(fila, text=str(r[2]), width=80, text_color=color_texto).pack(side="left", padx=5)
                ctk.CTkLabel(fila, text=f"$ {float(r[3]):>8.2f}", width=100).pack(side="left", padx=5)
                ctk.CTkLabel(fila, text=status_text, width=120, text_color=color_texto, anchor="w").pack(side="left", padx=5)

                # Divisor
                ctk.CTkFrame(self.frame_datos, height=1, fg_color="#333333").pack(fill="x", padx=10)

            conexion.close()
        except Exception as e:
            print(f"Error en SeccionProductos: {e}")