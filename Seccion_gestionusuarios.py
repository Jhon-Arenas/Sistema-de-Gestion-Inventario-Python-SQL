import customtkinter as ctk
from conexion_base import conectar_bd
from tkinter import messagebox
import hashlib # <--- El guardián de las contraseñas

# Usamos tu paleta global
PALETA = {
    "fondo": "#051F20",
    "sidebar": "#173831",
    "botones": "#235347",
    "hover": "#2E6A5C",
    "texto": "#DBF0DD",
    "peligro": "#5C1A1B",
    "exito": "#2D5A27"
}

class SeccionGestionUsuarios(ctk.CTkFrame):
    def __init__(self, master, rol):
        super().__init__(master, fg_color="transparent")
        self.rol = rol.lower()

        # 1. TÍTULO
        ctk.CTkLabel(self, text="🛡️ Control de Acceso y Usuarios", 
                     font=("Roboto", 28, "bold"), text_color=PALETA["texto"]).pack(pady=20)

        # 2. CONTENEDOR DE FORMULARIO
        self.frame_form = ctk.CTkFrame(self, fg_color=PALETA["sidebar"], corner_radius=15)
        self.frame_form.pack(pady=10, padx=40, fill="x")

        # Entradas con estilo
        self.entry_nombre = ctk.CTkEntry(self.frame_form, placeholder_text="Nombre de Usuario", width=200)
        self.entry_nombre.pack(side="left", padx=10, pady=20)

        self.entry_pass = ctk.CTkEntry(self.frame_form, placeholder_text="Contraseña", show="*", width=200)
        self.entry_pass.pack(side="left", padx=10, pady=20)

        self.combo_rol = ctk.CTkComboBox(self.frame_form, values=["Administrador", "Encargado", "Vendedor", "Inventario"], state="readonly")
        self.combo_rol.pack(side="left", padx=10, pady=20)
        self.combo_rol.set("Vendedor")

        self.btn_guardar = ctk.CTkButton(self.frame_form, text="➕ Crear Usuario", 
                                         fg_color=PALETA["exito"], hover_color="#1E4D1A",
                                         command=self.guardar_usuario)
        self.btn_guardar.pack(side="left", padx=10, pady=20)

        # 3. TABLA DE USUARIOS (Para ver y borrar)
        ctk.CTkLabel(self, text="Usuarios Registrados", font=("Roboto", 16, "bold")).pack(pady=(20, 5))
        self.scroll_usuarios = ctk.CTkScrollableFrame(self, fg_color="#0A2A2B", corner_radius=15)
        self.scroll_usuarios.pack(pady=10, padx=40, fill="both", expand=True)

        self.cargar_usuarios()

    def encriptar_password(self, password):
        """Convierte texto plano en un hash seguro SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def guardar_usuario(self):
        nombre = self.entry_nombre.get().strip()
        raw_pass = self.entry_pass.get().strip()
        rol = self.combo_rol.get()

        if not nombre or not raw_pass:
            messagebox.showwarning("Rick, cuidado", "No puedes dejar campos vacíos.")
            return

        # Aplicamos la seguridad antes de guardar
        pass_segura = self.encriptar_password(raw_pass)

        try:
            conn = conectar_bd()
            cursor = conn.cursor()
            # Fíjate que guardamos 'pass_segura', no 'raw_pass'
            cursor.execute("INSERT INTO Usuarios (Nombre_Usuario, Contraseña, Rol) VALUES (?, ?, ?)", 
                           (nombre, pass_segura, rol))
            conn.commit()
            conn.close()

            messagebox.showinfo("Éxito", f"Usuario '{nombre}' listo para trabajar.")
            self.limpiar_campos()
            self.cargar_usuarios()
        except Exception as e:
            messagebox.showerror("Error", f"¿Quizás el nombre ya existe? {e}")

    def cargar_usuarios(self):
        """Muestra quién tiene acceso al sistema"""
        for w in self.scroll_usuarios.winfo_children(): w.destroy()
        
        try:
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute("SELECT Nombre_Usuario, Rol FROM Usuarios")
            for user in cursor.fetchall():
                f = ctk.CTkFrame(self.scroll_usuarios, fg_color=PALETA["sidebar"])
                f.pack(fill="x", pady=2, padx=5)
                
                ctk.CTkLabel(f, text=f"👤 {user[0]}", width=200, anchor="w").pack(side="left", padx=15)
                ctk.CTkLabel(f, text=f"🔑 {user[1]}", width=150).pack(side="left")
                
                # Botón para eliminar (solo si no es el admin principal)
                if user[0] != "admin": 
                    btn_del = ctk.CTkButton(f, text="Eliminar", width=60, height=24, 
                                            fg_color=PALETA["peligro"],
                                            command=lambda u=user[0]: self.eliminar_usuario(u))
                    btn_del.pack(side="right", padx=10)
            conn.close()
        except: pass

    def eliminar_usuario(self, nombre):
        if messagebox.askyesno("Confirmar", f"¿Seguro que quieres quitarle el acceso a {nombre}?"):
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Usuarios WHERE Nombre_Usuario = ?", (nombre,))
            conn.commit()
            conn.close()
            self.cargar_usuarios()

    def limpiar_campos(self):
        self.entry_nombre.delete(0, 'end')
        self.entry_pass.delete(0, 'end')