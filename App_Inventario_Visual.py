import customtkinter as ctk
from tkinter import messagebox, ttk
from conexion_base import conectar_bd
import sqlite3
import hashlib 
from Seccion_productos import SeccionProductos
from Seccion_ventas import SeccionVentas
from Seccion_reportes import SeccionReportes
from Seccion_pedidos import SeccionPedidos
from Seccion_gestionusuarios import SeccionGestionUsuarios
from Seccion_Utilidades import resource_path

# --- 1. PALETA DE COLORES GLOBAL (Tu elección: Bosque Profundo) ---
# Paleta optimizada para Gestión de Inventario (basada en imagen 3.png)
PALETA = {
    "fondo": "#0D1B2A",      # El azul más oscuro (Base de la app)
    "sidebar": "#1B263B",    # Azul medianoche (Menú lateral)
    "botones": "#415A77",    # Azul acero (Acciones principales)
    "hover": "#778DA9",      # Gris azulado claro (Efecto al pasar el mouse)
    "texto": "#E0E1DD",      # Blanco hueso (Lectura perfecta sobre azul)
    "peligro": "#9A031E",    # Rojo vino (Para errores o stock en cero)
    "exito": "#2D5A27",       # Verde bosque (Para ingresos de mercancía)
    "resalte": "#CCAD1F",  # <--- AGREGA ESTA LÍNEA (No olvides la coma arriba)
    "alerta": "#E67E22"
}

# Configuración inicial de CustomTkinter
ctk.set_appearance_mode("dark")

class AppInventario(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Rick's Inventory System v2.0")
        self.geometry("1000x700")
        self.configure(fg_color=PALETA["fondo"])
        
        self.usuario_actual = None
        self.rol_usuario = None
        
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        
        self.mostrar_login()

        try:
            # Usamos resource_path para que encuentre el icono dentro del ejecutable
            self.iconbitmap(resource_path("Logo.ico")) 
        except:
            print("No se pudo cargar el icono, verifica el nombre del archivo.")
            pass

    # --- MÉTODO DE LOGIN CORREGIDO CON HASHING ---
    def validar_acceso(self):
        usuario = self.user_entry.get()
        password = self.pass_entry.get()
        
        # 1. Trituramos la contraseña para poder compararla con la BD
        pass_hasheada = hashlib.sha256(password.encode()).hexdigest()

        conn = conectar_bd()
        if conn:
            cursor = conn.cursor()
            # 2. Buscamos el hash, no la palabra real
            cursor.execute("SELECT Rol FROM Usuarios WHERE Nombre_Usuario = ? AND Contraseña = ?", 
                           (usuario, pass_hasheada))
            resultado = cursor.fetchone()
            conn.close()

            if resultado:
                self.usuario_actual = usuario
                self.rol_usuario = resultado[0]
                self.mostrar_menu_principal()
            else:
                messagebox.showerror("Error", "Rick, el usuario o contraseña son incorrectos.")

    def crear_boton(self, master, texto, comando, color="botones", **kwargs):
        return ctk.CTkButton(
            master, text=texto, command=comando,
            fg_color=PALETA[color], hover_color=PALETA["hover"],
            text_color=PALETA["texto"], font=("Roboto", 13, "bold"),
            **kwargs
        )

    # --- PANTALLA DE LOGIN (Cerebro + Cuerpo) ---
    def mostrar_login(self):
        for widget in self.container.winfo_children(): widget.destroy()

        frame = ctk.CTkFrame(self.container, fg_color=PALETA["sidebar"], width=350, height=450)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(frame, text="BIENVENIDO", font=("Roboto", 24, "bold"), text_color=PALETA["texto"]).pack(pady=(40, 20))
        
        self.user_entry = ctk.CTkEntry(frame, placeholder_text="Usuario", fg_color=PALETA["fondo"], border_color=PALETA["botones"])
        self.user_entry.pack(pady=12, padx=40, fill="x")
        
        self.pass_entry = ctk.CTkEntry(frame, placeholder_text="Contraseña", show="*", fg_color=PALETA["fondo"], border_color=PALETA["botones"])
        self.pass_entry.pack(pady=12, padx=40, fill="x")
        
        self.crear_boton(frame, "INGRESAR", self.validar_acceso, color="exito").pack(pady=30, padx=40, fill="x")

    # --- MENÚ PRINCIPAL ---
    def mostrar_menu_principal(self):
        for widget in self.container.winfo_children(): widget.destroy()

        sidebar = ctk.CTkFrame(self.container, width=200, fg_color=PALETA["sidebar"], corner_radius=0)
        sidebar.pack(side="left", fill="y")
        
        ctk.CTkLabel(sidebar, text=f"👤 {self.usuario_actual}\n[{self.rol_usuario}]", 
                     text_color=PALETA["texto"], font=("Roboto", 14, "bold")).pack(pady=30)

        # --- BOTONES DE NAVEGACIÓN ---
        self.crear_boton(sidebar, "📦 Productos", lambda: self.cambiar_seccion("productos")).pack(pady=10, padx=20, fill="x")
        
        if self.rol_usuario.lower() in ["administrador", "encargado", "vendedor"]:
            self.crear_boton(sidebar, "💰 Ventas", lambda: self.cambiar_seccion("ventas")).pack(pady=10, padx=20, fill="x")

        # --- BOTÓN DE PEDIDOS CON NOTIFICACIÓN (BADGE) ---
        #Botón de pedidos (este es el botón que se va a actualizar con el número rojo) y solo lo ven admin y encargado
        if self.rol_usuario.lower() in ["administrador", "encargado"]:
            # Creamos un frame pequeño para que el botón y el número rojo vivan juntos
            self.frame_pedidos = ctk.CTkFrame(sidebar, fg_color="transparent")
            self.frame_pedidos.pack(pady=10, padx=20, fill="x")

            self.btn_pedidos = self.crear_boton(self.frame_pedidos, "📝 Pedidos", lambda: self.cambiar_seccion("pedidos"))
            self.btn_pedidos.pack(side="left", fill="x", expand=True)

            # Aquí creamos el circulito rojo (Label), pero lo guardamos en self para moverlo
            self.lbl_badge = ctk.CTkLabel(self.frame_pedidos, text="0", width=24, height=24, 
                                        fg_color=PALETA["peligro"], text_color="white", 
                                        corner_radius=12, font=("Roboto", 11, "bold"))
        # No lo empaquetamos (pack) todavía, lo hará la función actualizar_badge_pedidos

        if self.rol_usuario.lower() in ["administrador", "encargado"]:
            self.crear_boton(sidebar, "📊 Reportes", lambda: self.cambiar_seccion("reportes")).pack(pady=10, padx=20, fill="x")

        if self.rol_usuario.lower() == "administrador":
                self.crear_boton(sidebar, "👥 Gestión de Usuarios", lambda: self.cambiar_seccion("usuarios")).pack(pady=10, padx=20, fill="x")

        self.crear_boton(sidebar, "🚪 Cerrar Sesión", self.mostrar_login, color="peligro").pack(side="bottom", pady=20, padx=20, fill="x")

        # Área de trabajo
        self.area_trabajo = ctk.CTkFrame(self.container, fg_color=PALETA["fondo"], corner_radius=0)
        self.area_trabajo.pack(side="right", fill="both", expand=True)
        
        self.label_bienvenida = ctk.CTkLabel(self.area_trabajo, text="Selecciona una opción del menú", text_color=PALETA["texto"])
        self.label_bienvenida.pack(expand=True)

        # Llamamos a actualizar el número rojo apenas abrimos el menú
        self.actualizar_badge_pedidos()

    def cambiar_seccion(self, seccion):
        # 1. Limpiamos
        for widget in self.area_trabajo.winfo_children():
            widget.destroy()

        # 2. EL MAPA (Aquí es donde ocurre la magia que te decía)
        # Esto reemplaza todos los "if seccion == ..."
        mapa_secciones = {
            "productos": SeccionProductos,
            "ventas": SeccionVentas,
            "reportes": SeccionReportes,
            "pedidos": SeccionPedidos,
            "usuarios": SeccionGestionUsuarios
        }

        # 3. Buscamos en el mapa y cargamos
        if seccion in mapa_secciones:
            ClaseSeleccionada = mapa_secciones[seccion]
            pantalla = ClaseSeleccionada(master=self.area_trabajo, rol=self.rol_usuario)
            pantalla.pack(fill="both", expand=True)

    def actualizar_badge_pedidos(self):
        """Esta es la función que cuenta los pedidos y pone el numerito rojo"""
        try:
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Pedidos WHERE estado = 'Pendiente'")
            total = cursor.fetchone()[0]
            conn.close()

            if total > 0:
                self.lbl_badge.configure(text=str(total))
                # .place nos permite ponerlo 'flotando' encima del botón
                self.lbl_badge.place(relx=0.8, rely=0.1) 
            else:
                self.lbl_badge.place_forget() # Si es 0, lo escondemos
        except:
            pass # En caso de error, no hacemos nada (podrías mostrar un mensaje si quieres)
# --- INICIALIZACIÓN DE BASE DE DATOS (Tu cerebro de BD) ---
def inicializar_bd():
    conn = conectar_bd()
    if conn:
        cursor = conn.cursor()
        
        # 1. Tabla de Productos (Stock y Precios)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Productos (
                ID_Producto INTEGER PRIMARY KEY AUTOINCREMENT,
                Nombre TEXT NOT NULL,
                Precio_Costo REAL NOT NULL,
                Stock INTEGER DEFAULT 0,
                Precio REAL
            )
        """)

        # 2. Tabla de Ventas (Cabecera de la factura)
        # Limpiamos columnas redundantes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Ventas (
                ID_Venta INTEGER PRIMARY KEY AUTOINCREMENT,
                Fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                Cliente TEXT,
                Total REAL,
                Metodo_Pago TEXT
            )
        """)

        # 3. TABLA QUE FALTABA: Detalle_Ventas (Los productos de cada venta)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Detalle_Ventas (
                ID_Detalle INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_Venta INTEGER,
                ID_Producto INTEGER,
                Precio_Unitario REAL,
                Cantidad INTEGER,
                Subtotal REAL,
                FOREIGN KEY(ID_Venta) REFERENCES Ventas(ID_Venta),
                FOREIGN KEY(ID_Producto) REFERENCES Productos(ID_Producto)
            )
        """)

        # 4. Tabla de Usuariosv 
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Usuarios (
                Nombre_Usuario TEXT PRIMARY KEY,
                Contraseña TEXT NOT NULL,
                Rol TEXT NOT NULL
            )
        """)

        # 5. Tabla de Pedidos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Pedidos (
                ID_Pedido INTEGER PRIMARY KEY AUTOINCREMENT,
                Nombre_Entidad TEXT,    -- Aquí va el nombre del Cliente o del Proveedor
                Producto TEXT,
                Cantidad INTEGER,
                Estado TEXT DEFAULT 'Pendiente',
                Tipo TEXT               -- 'Cliente' o 'Proveedor'
            )
        """)

        # --- ADMIN POR DEFECTO ---
        cursor.execute("SELECT COUNT(*) FROM Usuarios")
        if cursor.fetchone()[0] == 0:
            admin_pass = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO Usuarios (Nombre_Usuario, Contraseña, Rol) VALUES (?, ?, ?)",
                           ("Jhon", admin_pass, "Administrador"))
            print("Cuentas iniciales creadas.")

        conn.commit()
        conn.close()

if __name__ == "__main__":
    inicializar_bd()  # Crea las tablas si no existen
    app = AppInventario()
    app.mainloop()    # Enciende la interfaz
