import customtkinter as ctk
from conexion_base import conectar_bd
from tkinter import messagebox
import pandas as pd

PALETA = {
    "fondo": "#051F20",
    "sidebar": "#173831",
    "botones": "#235347",
    "hover": "#2E6A5C",
    "texto": "#DBF0DD",
    "peligro": "#5C1A1B",
    "exito": "#2D5A27"
}

class SeccionVentas(ctk.CTkFrame):
    def __init__(self, master, rol):
        super().__init__(master, fg_color="transparent")
        self.rol = rol.lower()
        self.carrito = [] 

        # --- CABECERA ---
        self.titulo_label = ctk.CTkLabel(self, text="💰 Punto de Venta", 
                                        font=("Roboto", 28, "bold"), 
                                        text_color=PALETA["texto"])
        self.titulo_label.pack(pady=20)

        self.tabview = ctk.CTkTabview(self, segmented_button_fg_color=PALETA["sidebar"],
                                      segmented_button_selected_color=PALETA["botones"])
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)

        self.tab_venta = self.tabview.add("🛒 Nueva Venta")
        self.tab_historial = self.tabview.add("📜 Historial")

        self.configurar_pestaña_venta()
        self.configurar_pestaña_historial()
        
        # Cargar historial inicial
        self.actualizar_historial_pro()

    def configurar_pestaña_venta(self):
        cont_venta = ctk.CTkFrame(self.tab_venta, fg_color="transparent")
        cont_venta.pack(fill="both", expand=True)

        # --- PANEL IZQUIERDO ---
        self.frame_datos = ctk.CTkFrame(cont_venta, fg_color=PALETA["sidebar"], width=300)
        self.frame_datos.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(self.frame_datos, text="Buscar Producto", font=("Roboto", 16, "bold")).pack(pady=(10, 0))
        
        self.entry_buscar_nombre = ctk.CTkEntry(self.frame_datos, placeholder_text="Escribe nombre...", fg_color=PALETA["fondo"])
        self.entry_buscar_nombre.pack(pady=5, padx=20, fill="x")
        self.entry_buscar_nombre.bind("<KeyRelease>", lambda e: self.sugerir_productos())

        self.label_sugerencia = ctk.CTkLabel(self.frame_datos, text="ID Sugerido: ---", font=("Roboto", 11), text_color="#AAA")
        self.label_sugerencia.pack()

        ctk.CTkLabel(self.frame_datos, text="Detalles de Venta", font=("Roboto", 16, "bold")).pack(pady=(20, 10))
        
        self.entry_id_producto = ctk.CTkEntry(self.frame_datos, placeholder_text="ID Confirmado", fg_color=PALETA["fondo"])
        self.entry_id_producto.pack(pady=5, padx=20, fill="x")
        
        self.entry_cantidad = ctk.CTkEntry(self.frame_datos, placeholder_text="Cantidad", fg_color=PALETA["fondo"])
        self.entry_cantidad.pack(pady=5, padx=20, fill="x")
        self.entry_cantidad.insert(0, "1")

        self.entry_cliente = ctk.CTkEntry(self.frame_datos, placeholder_text="Cliente", fg_color=PALETA["fondo"])
        self.entry_cliente.pack(pady=5, padx=20, fill="x")

        self.combo_pago = ctk.CTkComboBox(self.frame_datos, values=["Efectivo", "Transferencia", "Pago Móvil", "Divisas"], fg_color=PALETA["fondo"])
        self.combo_pago.pack(pady=5, padx=20, fill="x")
        self.combo_pago.set("Efectivo")

        ctk.CTkButton(self.frame_datos, text="➕ Añadir al Carrito", fg_color=PALETA["botones"], 
                      command=self.añadir_al_carrito).pack(pady=20, padx=20, fill="x")

        # --- PANEL DERECHO ---
        self.frame_carrito = ctk.CTkFrame(cont_venta, fg_color="#0A2A2B")
        self.frame_carrito.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(self.frame_carrito, text="📦 Detalle de Factura", font=("Roboto", 18, "bold")).pack(pady=10)
        
        self.tabla_carrito = ctk.CTkScrollableFrame(self.frame_carrito, fg_color="transparent")
        self.tabla_carrito.pack(fill="both", expand=True, padx=10, pady=5)

        self.label_total = ctk.CTkLabel(self.frame_carrito, text="TOTAL: $0.00", font=("Roboto", 22, "bold"), text_color=PALETA["texto"])
        self.label_total.pack(pady=5)

        self.btn_finalizar = ctk.CTkButton(self.frame_carrito, text="✅ Procesar Pago", 
                                          fg_color=PALETA["exito"], font=("Roboto", 14, "bold"),
                                          command=self.finalizar_venta)
        self.btn_finalizar.pack(pady=10, padx=20, fill="x")

        # Solo para Encargados y Administradores
        if self.rol in ["encargado", "administrador"]:
            self.btn_descuento = ctk.CTkButton(self.frame_carrito, text="🏷️ Aplicar Descuento", 
                                              fg_color=PALETA["hover"], font=("Roboto", 14, "bold"),
                                              command=self.aplicar_descuento)
            self.btn_descuento.pack(pady=10, padx=20, fill="x")

        self.btn_limpiar = ctk.CTkButton(self.frame_carrito, text="🗑️ Vaciar Todo", 
                                        fg_color=PALETA["peligro"], command=self.limpiar_carrito_total)
        self.btn_limpiar.pack(pady=(0, 15), padx=20, fill="x")

    def sugerir_productos(self):
        nombre = self.entry_buscar_nombre.get().strip()
        if len(nombre) < 2: 
            self.label_sugerencia.configure(text="ID Sugerido: ---")
            return
        
        try:
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute("SELECT ID_Producto, Nombre FROM Productos WHERE Nombre LIKE ? LIMIT 1", (f'%{nombre}%',))
            res = cursor.fetchone()
            conn.close()
            
            if res:
                self.label_sugerencia.configure(text=f"Sugerido: {res[1]} (ID: {res[0]})", text_color="#4ade80")
                self.entry_id_producto.delete(0, 'end')
                self.entry_id_producto.insert(0, str(res[0]))
            else:
                self.label_sugerencia.configure(text="No encontrado", text_color="#FF4444")
        except: pass

    def añadir_al_carrito(self):
        id_p = self.entry_id_producto.get().strip()
        cant = self.entry_cantidad.get().strip()
        if not id_p or not cant: return

        try:
            cant = int(cant)
            conn = conectar_bd(); cursor = conn.cursor()
            cursor.execute("SELECT Nombre, Precio, Stock FROM Productos WHERE ID_Producto = ?", (id_p,))
            res = cursor.fetchone()
            conn.close()

            if res:
                nom, pre, stock = res
                if cant > stock:
                    messagebox.showerror("Sin Stock", f"Solo hay {stock} disponibles.")
                    return
                
                for item in self.carrito:
                    if item['id'] == id_p:
                        item['cantidad'] += cant
                        item['subtotal'] = item['cantidad'] * item['precio']
                        self.actualizar_vista_carrito()
                        return

                self.carrito.append({"id": id_p, "nombre": nom, "cantidad": cant, "precio": pre, "subtotal": pre*cant})
                self.actualizar_vista_carrito()
            else:
                messagebox.showerror("Error", "ID no encontrado.")
        except: messagebox.showerror("Error", "Dato inválido.")

    def actualizar_vista_carrito(self):
        for widget in self.tabla_carrito.winfo_children(): widget.destroy()
        total = 0
        for i, item in enumerate(self.carrito):
            f = ctk.CTkFrame(self.tabla_carrito, fg_color=PALETA["botones"])
            f.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(f, text=f"{item['nombre']} x{item['cantidad']}").pack(side="left", padx=10)
            ctk.CTkLabel(f, text=f"${item['subtotal']:.2f}").pack(side="left", padx=20)
            ctk.CTkButton(f, text="❌", width=25, fg_color=PALETA["peligro"], command=lambda idx=i: self.quitar_item(idx)).pack(side="right", padx=5)
            total += item['subtotal']
        self.label_total.configure(text=f"TOTAL: ${total:.2f}")

    def quitar_item(self, index):
        self.carrito.pop(index)
        self.actualizar_vista_carrito()

    # Añadimos un wallet de Descuentos
    def aplicar_descuento(self):
        if not self.carrito: 
            messagebox.showwarning("Carrito vacío", "No hay productos para aplicar descuento.")
            return
            
        dialog = ctk.CTkInputDialog(text="Ingresa el % de descuento (0-100):", title="Descuento")
        input_val = dialog.get_input()
        
        if input_val is None: return # El usuario canceló

        try:
            desc_val = float(input_val)
            if not (0 < desc_val <= 100):
                messagebox.showerror("Error", "Ingrese un valor entre 0 y 100.")
                return
            
            # Aplicamos el descuento sobre el subtotal original o recalculamos
            # Nota: Considera si quieres aplicar esto a todo el carrito o ítem por ítem
            for item in self.carrito:
                # Aquí multiplicamos para reducir el valor
                item['subtotal'] = item['subtotal'] * (1 - desc_val / 100)
            
            self.actualizar_vista_carrito()
            messagebox.showinfo("Éxito", f"Descuento de {desc_val}% aplicado.")
        except ValueError:
            messagebox.showerror("Error", "El valor ingresado no es un número.")

    def finalizar_venta(self):
        if not self.carrito: return
        cliente = self.entry_cliente.get().strip() or "General"
        metodo = self.combo_pago.get()
        total = sum(item['subtotal'] for item in self.carrito)

        if not messagebox.askyesno("Confirmar", f"¿Procesar venta por ${total:.2f}?"): return

        try:
            conn = conectar_bd(); cursor = conn.cursor()
            # 1. Registrar venta
            cursor.execute("INSERT INTO Ventas (Cliente, Total, Metodo_Pago) VALUES (?, ?, ?)", (cliente, total, metodo))
            id_venta = cursor.lastrowid

            # 2. Detalles y Stock
            for item in self.carrito:
                cursor.execute("INSERT INTO Detalle_Ventas (ID_Venta, ID_Producto, Cantidad, Subtotal) VALUES (?, ?, ?, ?)",
                               (id_venta, item['id'], item['cantidad'], item['subtotal']))
                cursor.execute("UPDATE Productos SET Stock = Stock - ? WHERE ID_Producto = ?", (item['cantidad'], item['id']))

            conn.commit(); conn.close()
            messagebox.showinfo("Éxito", "Venta completada.")
            self.carrito = []; self.actualizar_vista_carrito()
            self.actualizar_historial_pro()
        except Exception as e:
            messagebox.showerror("Error", f"Error en BD: {e}")

    def configurar_pestaña_historial(self):
        self.frame_historial = ctk.CTkFrame(self.tab_historial, fg_color="transparent")
        self.frame_historial.pack(fill="both", expand=True)
        ctk.CTkButton(self.frame_historial, text="🔄 Refrescar", command=self.actualizar_historial_pro).pack(pady=10)
        self.scroll_historial = ctk.CTkScrollableFrame(self.frame_historial, fg_color=PALETA["sidebar"])
        self.scroll_historial.pack(fill="both", expand=True, padx=20, pady=10)

    def actualizar_historial_pro(self):
        for w in self.scroll_historial.winfo_children(): w.destroy()
        try:
            conn = conectar_bd()
            df = pd.read_sql_query("SELECT * FROM Ventas ORDER BY ID_Venta DESC LIMIT 30", conn)
            conn.close()
            for _, r in df.iterrows():
                f = ctk.CTkFrame(self.scroll_historial, fg_color=PALETA["fondo"])
                f.pack(fill="x", pady=2, padx=5)
                ctk.CTkLabel(f, text=f"#{r['ID_Venta']} | {r['Cliente']} | ${r['Total']:.2f} | {r['Metodo_Pago']}").pack(side="left", padx=15)
        except: pass

    def limpiar_carrito_total(self):
        self.carrito = []; self.actualizar_vista_carrito()