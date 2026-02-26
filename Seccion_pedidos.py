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
    "exito": "#27ae60"
}

class SeccionPedidos(ctk.CTkFrame):
    def __init__(self, master, rol):
        super().__init__(master, fg_color="transparent")
        self.rol = rol.lower()

        # 1. TÍTULO
        self.lbl_titulo = ctk.CTkLabel(self, text="📝 Registro de Pedidos Pendientes", 
                                       font=("Roboto", 28, "bold"), text_color=PALETA["texto"])
        self.lbl_titulo.pack(pady=20)

        # 2. FORMULARIO
        self.frame_formulario = ctk.CTkFrame(self, fg_color=PALETA["sidebar"], corner_radius=15)
        self.frame_formulario.pack(fill="x", padx=40, pady=10)

        self.entry_cliente = ctk.CTkEntry(self.frame_formulario, placeholder_text="Nombre del cliente...", width=200)
        self.entry_cliente.pack(side="left", padx=10, pady=20)

        self.entry_producto = ctk.CTkEntry(self.frame_formulario, placeholder_text="Producto...", width=200)
        self.entry_producto.pack(side="left", padx=10, pady=20)

        self.entry_cantidad = ctk.CTkEntry(self.frame_formulario, placeholder_text="Cant.", width=80)
        self.entry_cantidad.pack(side="left", padx=10, pady=20)

        self.btn_guardar = ctk.CTkButton(self.frame_formulario, text="💾 Registrar", 
                                         fg_color=PALETA["botones"], hover_color=PALETA["hover"],
                                         command=self.registrar_pedido)
        self.btn_guardar.pack(side="left", padx=10, pady=20)

        # 3. TABLA (CABECERA)
        self.frame_header = ctk.CTkFrame(self, fg_color=PALETA["botones"], corner_radius=5)
        self.frame_header.pack(fill="x", padx=40, pady=(20, 0))

        columnas = [("ID", 50), ("Cliente", 180), ("Producto", 180), ("Cant.", 80), ("Estado", 100), ("Acción", 110)]
        for texto, ancho in columnas:
            lbl = ctk.CTkLabel(self.frame_header, text=texto, width=ancho, font=("Roboto", 12, "bold"), text_color=PALETA["texto"])
            lbl.pack(side="left", padx=5)

        # 4. CUERPO SCROLLABLE
        self.tabla_pedidos = ctk.CTkScrollableFrame(self, fg_color="#0A2A2B", corner_radius=15)
        self.tabla_pedidos.pack(pady=(0, 20), padx=40, fill="both", expand=True)

        self.actualizar_lista_pedidos()

    def actualizar_lista_pedidos(self):
        """Limpia y recarga la lista de pedidos pendientes."""
        for widget in self.tabla_pedidos.winfo_children():
            widget.destroy()

        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            cursor.execute("SELECT * FROM Pedidos WHERE estado = 'Pendiente'")
            filas = cursor.fetchall()

            for fila in filas:
                f_row = ctk.CTkFrame(self.tabla_pedidos, fg_color=PALETA["sidebar"], height=45)
                f_row.pack(fill="x", pady=2, padx=5)

                ctk.CTkLabel(f_row, text=fila[0], width=50, text_color=PALETA["texto"]).pack(side="left", padx=5)
                ctk.CTkLabel(f_row, text=fila[1], width=180, anchor="w", text_color=PALETA["texto"]).pack(side="left", padx=5)
                ctk.CTkLabel(f_row, text=fila[2], width=180, anchor="w", text_color=PALETA["texto"]).pack(side="left", padx=5)
                ctk.CTkLabel(f_row, text=fila[3], width=80, text_color=PALETA["texto"]).pack(side="left", padx=5)
                
                lbl_estado = ctk.CTkLabel(f_row, text="⏳ " + fila[4], width=100, text_color="#E67E22", font=("Roboto", 11, "bold"))
                lbl_estado.pack(side="left", padx=5)

                btn_check = ctk.CTkButton(f_row, text="✔️ Entregar", width=90, height=28,
                                          fg_color=PALETA["exito"], hover_color="#219150",
                                          command=lambda p=fila[0]: self.completar_pedido_directo(p))
                btn_check.pack(side="right", padx=10)

            conexion.close()
        except Exception as e:
            print(f"Error al construir tabla: {e}")

    def registrar_pedido(self):
        nombre = self.entry_cliente.get()
        prod = self.entry_producto.get()
        cant = self.entry_cantidad.get()

        if not nombre.strip() or not prod.strip() or not cant.strip():
            messagebox.showwarning("Atención", "Por favor, completa todos los campos.")
            return

        try:
            conexion = conectar_bd() 
            cursor = conexion.cursor()
            cursor.execute("INSERT INTO Pedidos (cliente, producto, cantidad, estado) VALUES (?, ?, ?, ?)", 
                           (nombre, prod, int(cant), "Pendiente"))
            conexion.commit()
            conexion.close() 

            self.entry_cliente.delete(0, 'end')
            self.entry_producto.delete(0, 'end')
            self.entry_cantidad.delete(0, 'end')

            self.actualizar_lista_pedidos()
            self.notificar_al_main()

        except ValueError:
            messagebox.showerror("Error", "La cantidad debe ser un número.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    def completar_pedido_directo(self, id_ped):
        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()

            cursor.execute("SELECT producto, cantidad FROM Pedidos WHERE id_pedido = ?", (id_ped,))
            resultado = cursor.fetchone()

            if resultado:
                nombre_producto, cantidad_pedida = resultado[0], resultado[1]

                # Descontar del inventario
                cursor.execute("""
                    UPDATE Productos 
                    SET Cantidad = Cantidad - ? 
                    WHERE Nombre_Producto = ? AND Cantidad >= ?
                """, (cantidad_pedida, nombre_producto, cantidad_pedida))

                if cursor.rowcount == 0:
                    messagebox.showwarning("Stock Insuficiente", 
                        f"No hay suficiente stock de '{nombre_producto}' para completar este pedido.")
                    conexion.close()
                    return

                cursor.execute("UPDATE Pedidos SET estado = 'Entregado' WHERE id_pedido = ?", (id_ped,))
                conexion.commit()
                messagebox.showinfo("Éxito", "Pedido entregado e inventario actualizado.")
            
            conexion.close()
            self.actualizar_lista_pedidos()
            self.notificar_al_main()

        except Exception as e:
            messagebox.showerror("Error", f"Fallo en la entrega: {e}")

    # Busca esta parte en Seccion_pedidos.py y cámbiala por esto:
    def notificar_al_main(self):
        """Sube por la jerarquía de masters hasta encontrar la función del Badge"""
        try:
            # Intentamos subir hasta llegar a AppInventario
            # self.master es area_trabajo
            # self.master.master es container
            # self.master.master.master es AppInventario
            objetivo = self.master.master.master
        
            if hasattr(objetivo, 'actualizar_badge_pedidos'):
                objetivo.actualizar_badge_pedidos()
        except Exception as e:
            print(f"Nota: No se pudo notificar al main: {e}")
            