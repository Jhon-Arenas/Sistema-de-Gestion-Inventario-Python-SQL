import customtkinter as ctk
import pandas as pd
from tkinter import messagebox
from conexion_base import conectar_bd

# ==========================================================
# CONFIGURACIÓN DE APARIENCIA (AÑADIR ESTO AQUÍ) - NUEVO
# ==========================================================
ctk.set_appearance_mode("dark")  # Fuerza el modo oscuro
ctk.set_default_color_theme("blue") # Define el color azul para los botones
# ==========================================================

print("Buscando conexión a la base de datos...")

from Seccion_gestionusuarios import SeccionGestionUsuarios
from Seccion_reportes import SeccionReportes
from Seccion_productos import SeccionProductos
from Seccion_ventas import SeccionVentas
from Seccion_cargarproductos import SeccionInventario
from Seccion_pedidos import SeccionPedidos

class VentanaSalidaSencion(ctk.CTkToplevel):
    def __init__(self, master, SalidaSesion): # Agregamos 'master'
        super().__init__(master)
        self.master = master # Guardamos la referencia de la ventana principal
        self.title(SalidaSesion)
        self.geometry("300x150")
        self.attributes("-topmost", True)

        self.label = ctk.CTkLabel(self, text="¿Desea cerrar sesión?", font=("Roboto", 14))
        self.label.pack(pady=20)

        self.btn_confirmar = ctk.CTkButton(self, text="Sí, cerrar sesión", command=self.cerrar_sesion)
        self.btn_confirmar.pack(pady=10)

    def cerrar_sesion(self):
        self.destroy()          # Cierra la ventanita de confirmación
        self.master.destroy()   # ¡Cierra la Ventana Principal!
        
        # Volvemos al Login
        nuevo_login = VentanaLogin()
        nuevo_login.mainloop()

class VentanaPrincipal(ctk.CTk):
    def __init__(self, usuario, rol):
        super().__init__()

        # Guardamos en la "mochila" de la clase para que no se pierdan
        self.usuario = usuario
        self.rol = rol
        
        self.title(f"Gestión de Inventario - Bienvenido {self.usuario}")
        self.geometry("900x600")
        
        # 1. Configuración
        self.configure(fg_color="#510B0B") 
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 2. Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=15, fg_color="#262626")
        self.sidebar_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # 3. Botones (Solo los creamos, no les aplicamos lógica aquí)
        self.btn_productos = ctk.CTkButton(self.sidebar_frame, text="📦 Productos", command=self.mostrar_productos)
        self.btn_productos.pack(pady=10, padx=20)

        self.btn_ventas = ctk.CTkButton(self.sidebar_frame, text="💰 Ventas", command=self.mostrar_ventas, fg_color="#28a745")
        self.btn_ventas.pack(pady=10, padx=20)

        # Agregamos el botón de Pedidos después de Ventas
        self.btn_pedidos = ctk.CTkButton(self.sidebar_frame, text="📝 Pedidos", command=self.mostrar_pedidos, fg_color="#E67E22")
        self.btn_pedidos.pack(pady=10, padx=20)

        self.btn_cargar_productos = ctk.CTkButton(self.sidebar_frame, text="📈 Inventario", command=self.cargar_productos, fg_color= "#A00A7A")
        self.btn_cargar_productos.pack(pady=10, padx=20)

        self.btn_reportes = ctk.CTkButton(self.sidebar_frame, text="📊 Reportes", command=self.mostrar_reportes, fg_color="#456E54")
        self.btn_reportes.pack(pady=10, padx=20)

        # El botón de cerrar sesión lo dejamos al final para que siempre esté visible, y con un color rojo para destacarlo
        self.btn_cerrar_sesion = ctk.CTkButton(self.sidebar_frame, text="🚪 Cerrar Sesión", command=self.cerrar_sesion, fg_color="#c62828")
        self.btn_cerrar_sesion.pack(side='bottom', pady=20)                              

        self.btn_gestionusuarios = ctk.CTkButton(self.sidebar_frame, text="👥 Usuarios", command=self.abrir_gestion_usuarios, fg_color="#741EBA")
        self.btn_gestionusuarios.pack(side='bottom', pady=10)

        # 4. Área de Contenido (Escenario)
        self.home_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="transparent")
        self.home_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # 5. Aplicar permisos y mostrar bienvenida
        self.aplicar_permisos()
        self.mostrar_bienvenida()

        # 6. Actualizar el contador de pedidos al entrar
        self.actualizar_badge_pedidos()

    # --- FUNCIONES DE APOYO ---
    def limpiar_escenario(self):
        for widget in self.home_frame.winfo_children():
            widget.destroy()

    def aplicar_permisos(self):
        # Usamos self.rol porque es la variable que guardamos en el __init__
        if self.rol.lower() == "vendedor":
            self.btn_reportes.pack_forget()
            self.btn_gestionusuarios.pack_forget()
            self.btn_cargar_productos.pack_forget()
            
        if self.rol.lower() == "inventario":
            self.btn_ventas.pack_forget()
            self.btn_gestionusuarios.pack_forget()

        # El administrador ve todo, así que no le ocultamos nada.
        # Pero si el rol no es ninguno de los anteriores, por seguridad, ocultamos gestión de usuarios
        if self.rol.lower() != "administrador":
            self.btn_gestionusuarios.pack_forget()

    def mostrar_bienvenida(self):
        self.limpiar_escenario()
        self.label_bienvenida = ctk.CTkLabel(self.home_frame, 
                                            text=f"Sesión activa: {self.usuario}\nRol: {self.rol}", 
                                            font=("Roboto", 18, "bold"))
        self.label_bienvenida.pack(pady=100)

    # --- FUNCIONES DE BOTONES ---
    def mostrar_ventas(self): 
        print("Cambiando a vista de ventas...")
        self.limpiar_escenario()
        nueva_vista = SeccionVentas(master=self.home_frame)
        nueva_vista.pack(fill="both", expand=True)

    def mostrar_pedidos(self):
        print("Abriendo sección de pedidos...")
        self.limpiar_escenario()
        # Instanciamos la clase que creamos en el otro archivo
        ventana_pedidos = SeccionPedidos(master=self.home_frame)
        ventana_pedidos.pack(fill="both", expand=True)

    def actualizar_badge_pedidos(self):
        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            # Contamos cuántos pedidos pendientes hay
            cursor.execute("SELECT COUNT(*) FROM Pedidos WHERE estado = 'Pendiente'")
            cantidad = cursor.fetchone()[0]
            conexion.close()

            # Si hay pedidos, mostramos el número. Si no, solo el texto normal.
            if cantidad > 0:
                self.btn_pedidos.configure(text=f"📝 Pedidos ({cantidad})")
            else:
                self.btn_pedidos.configure(text="📝 Pedidos")
        except Exception as e:
            print(f"Error al actualizar badge: {e}")

    def mostrar_productos(self):
        print("Abriendo ventana de productos...")
        self.limpiar_escenario() # Limpiamos el escenario antes de mostrar la ventana
        ventana_productos = SeccionProductos(master=self.home_frame) # Le pasamos el home_frame como master
        ventana_productos.pack(fill="both", expand=True)

    def cargar_productos(self):
        print("Abriendo ventana de carga de productos...")
        self.limpiar_escenario() # Limpiamos el escenario antes de mostrar la ventana
        ventana_carga = SeccionInventario(master=self.home_frame) # Le pasamos el home_frame como master
        ventana_carga.pack(fill="both", expand=True)

    def mostrar_reportes(self):
        print("Abriendo ventana de reportes...")
        self.limpiar_escenario() # Limpiamos el escenario antes de mostrar la ventana
        ventana_reportes = SeccionReportes(master=self.home_frame) # Le pasamos el home_frame como master
        ventana_reportes.pack(fill="both", expand=True)

    def cerrar_sesion(self):
        ventana_salida = VentanaSalidaSencion(self, "Cerrar Sesión")
        ventana_salida.focus()

    def abrir_gestion_usuarios(self):
        print("Abriendo ventana de gestión de usuarios...")
        self.limpiar_escenario() # Limpiamos el escenario antes de mostrar la ventana
        ventana_gestion = SeccionGestionUsuarios(master=self.home_frame) # Le pasamos el home_frame como master
        ventana_gestion.pack(fill="both", expand=True)

class VentanaLogin(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Inventario - Login")
        self.geometry("400x500")
        self.resizable(False, False)
        self.configure(fg_color="#411111")

        self.frame = ctk.CTkFrame(self, width=320, height=400, corner_radius=15)
        self.frame.place(relx=0.5, rely=0.5, anchor="center")

        self.label = ctk.CTkLabel(self.frame, text="BIENVENIDO", font=("Roboto", 24, "bold"))
        self.label.pack(pady=(40, 20))

        self.user_entry = ctk.CTkEntry(self.frame, placeholder_text="Usuario", width=220)
        self.user_entry.pack(pady=12)

        self.pass_entry = ctk.CTkEntry(self.frame, placeholder_text="Contraseña", show="*", width=220)
        self.pass_entry.pack(pady=12)

        self.btn_login = ctk.CTkButton(self.frame, text="Iniciar Sesión", command=self.validar_acceso)
        self.btn_login.pack(pady=30)

    def validar_acceso(self):
        usuario = self.user_entry.get()
        password = self.pass_entry.get()

        conexion = conectar_bd()
        if conexion:
            cursor = conexion.cursor()
            # IMPORTANTE: Asegúrate de que el SELECT traiga el Nombre y el Rol
            cursor.execute("SELECT Nombre_Usuario, Rol FROM Usuarios WHERE Nombre_Usuario = ? AND Contraseña = ?", (usuario, password))
            resultado = cursor.fetchone()

            if resultado:
                nombre_db, rol_db = resultado[0], resultado[1]
                messagebox.showinfo("Éxito", "¡Inicio de sesión exitoso!")
                
                self.destroy() # Cerramos login
                
                # 🚀 AQUÍ ESTÁ EL TRUCO: Abrimos la principal DESPUÉS de cerrar el login
                app_principal = VentanaPrincipal(nombre_db, rol_db)
                app_principal.mainloop()
            else:
                messagebox.showerror("Error", "Usuario o contraseña incorrectos.")
            conexion.close()

# 2. EJECUCIÓN (Al final del archivo)
def inicializar_base_datos():
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()

        # 1. Tabla Usuarios (Se mantiene igual)
        cursor.execute('''CREATE TABLE IF NOT EXISTS Usuarios (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            Nombre_Usuario TEXT NOT NULL,
            Contraseña TEXT NOT NULL,
            Rol TEXT NOT NULL)''')

        # 2. Tabla Ventas (Cabecera del Ticket)
        # 2. Tabla Ventas (Cabecera del Ticket) - CORREGIDA
        cursor.execute('''CREATE TABLE IF NOT EXISTS Ventas (
            id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER,
            Total_Venta REAL,
            Fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            Nombre_Cliente TEXT,
            Metodo_Pago TEXT,
            FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario))''')

        # 3. NUEVA: Tabla Detalle_Ventas (Los productos del carrito)
        # Aquí es donde se guarda cada renglón de lo que compró el cliente
        cursor.execute('''CREATE TABLE IF NOT EXISTS Detalle_Ventas (
            id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
            id_venta INTEGER,
            id_producto INTEGER,
            Nombre_Producto TEXT,
            Cantidad INTEGER,
            Precio_Unitario REAL,
            Subtotal REAL,
            FOREIGN KEY (id_venta) REFERENCES Ventas(id_venta),
            FOREIGN KEY (id_producto) REFERENCES Productos(ID_Producto))''')

        # 4. Tabla Productos (Se mantiene igual)
        cursor.execute('''CREATE TABLE IF NOT EXISTS Productos (
            ID_Producto INTEGER PRIMARY KEY AUTOINCREMENT,
            Nombre TEXT NOT NULL, 
            Stock INTEGER, 
            Precio REAL)''')
    
        # 5. Tabla Pedidos (Se mantiene igual)
        cursor.execute('''CREATE TABLE IF NOT EXISTS Pedidos (
            id_pedido INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL, producto TEXT NOT NULL,
            cantidad INTEGER, estado TEXT NOT NULL)''')

        #creamos a los nuevos usuarios
        cursor.execute("SELECT COUNT(*) FROM Usuarios")
        if cursor.fetchone()[0] == 0:  # Si la tabla está vacía...
            # Insertamos a Jhon
            cursor.execute("INSERT INTO Usuarios (Nombre_Usuario, Contraseña, Rol) VALUES (?, ?, ?)", 
                           ('Jhon', '1234', 'Administrador'))
            # Insertamos a Angela
            cursor.execute("INSERT INTO Usuarios (Nombre_Usuario, Contraseña, Rol) VALUES (?, ?, ?)", 
                           ('Angela', '0000', 'Administrador'))
            print("✅ Usuarios administradores creados con éxito.")
            print("✅ Base de datos inicializada con nuevas tablas de ventas.")

        conexion.commit()
        conexion.close()
    except Exception as e:
        print(f"Error al inicializar: {e}")

# --- EL BLOQUE FINAL DE EJECUCIÓN ---
if __name__ == "__main__":
    # 1. Primero preparamos el terreno (Base de datos)
    inicializar_base_datos() 
    
    # 2. Luego abrimos la puerta (Login)
    login = VentanaLogin()
    login.mainloop()