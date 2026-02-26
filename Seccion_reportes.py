import customtkinter as ctk
import pandas as pd
from conexion_base import conectar_bd
from tkinter import messagebox, filedialog
from datetime import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

PALETA = {
    "fondo": "#051F20",
    "sidebar": "#173831",
    "botones": "#235347",
    "hover": "#2E6A5C",
    "texto": "#DBF0DD",
    "exito": "#2D5A27",
    "resalte": "#E67E22" 
}

class SeccionReportes(ctk.CTkFrame):
    def __init__(self, master, rol):
        super().__init__(master, fg_color="transparent")
        self.rol = rol.lower()
        
        # 1. TÍTULO
        ctk.CTkLabel(self, text="📊 Inteligencia de Negocio", 
                     font=("Roboto", 28, "bold"), text_color=PALETA["texto"]).pack(pady=15)

        # 2. KPIs (Tus tarjetas originales: Ingresos, Ventas y PRODUCTO ESTRELLA)
        self.frame_cards = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_cards.pack(fill="x", padx=40, pady=5)

        self.card_total = self.crear_tarjeta("Ingresos Totales", "$ 0.00", "#4ADE80")
        self.card_cantidad = self.crear_tarjeta("Ventas Realizadas", "0", PALETA["texto"])
        self.card_top = self.crear_tarjeta("⭐ Producto Estrella", "---", PALETA["resalte"])

        # 3. ZONA DE GRÁFICA (Nueva sección para visualizar tendencias)
        self.frame_grafica = ctk.CTkFrame(self, fg_color=PALETA["sidebar"], corner_radius=15, height=200)
        self.frame_grafica.pack(fill="x", padx=40, pady=10)

        # 4. BARRA DE HERRAMIENTAS (Filtros originales)
        self.frame_tools = ctk.CTkFrame(self, fg_color=PALETA["sidebar"], corner_radius=10)
        self.frame_tools.pack(pady=10, padx=40, fill="x")

        self.entry_cliente = ctk.CTkEntry(self.frame_tools, placeholder_text="👤 Buscar Cliente...", width=200)
        self.entry_cliente.pack(side="left", padx=10, pady=10)

        # Botón Actualizar
        self.btn_generar = ctk.CTkButton(self.frame_tools, text="🔄 Actualizar Todo", 
                                         fg_color=PALETA["botones"], width=140,
                                         command=self.generar_reporte)
        self.btn_generar.pack(side="left", padx=5)

        # Botón Excel (¡Aquí está de vuelta!)
        self.btn_excel = ctk.CTkButton(self.frame_tools, text="📉 Exportar Excel", 
                                       fg_color="#1D6F42", hover_color="#145231", width=140,
                                       command=self.exportar_a_excel)
        self.btn_excel.pack(side="left", padx=5)

        # 5. HISTORIAL DETALLADO (Tu lista original)
        ctk.CTkLabel(self, text="📜 Historial Reciente", font=("Roboto", 14, "bold")).pack()
        self.scroll_reporte = ctk.CTkScrollableFrame(self, fg_color="#0A2A2B", corner_radius=15, height=200)
        self.scroll_reporte.pack(pady=10, padx=40, fill="both", expand=True)

        self.generar_reporte()

    def crear_tarjeta(self, titulo, valor_init, color_valor):
        card = ctk.CTkFrame(self.frame_cards, fg_color=PALETA["sidebar"], corner_radius=15)
        card.pack(side="left", padx=10, expand=True, fill="both")
        ctk.CTkLabel(card, text=titulo, font=("Roboto", 11)).pack(pady=(5,0))
        lbl = ctk.CTkLabel(card, text=valor_init, font=("Roboto", 18, "bold"), text_color=color_valor)
        lbl.pack(pady=10)
        return lbl

    def dibujar_grafica(self, df):
        for widget in self.frame_grafica.winfo_children(): widget.destroy()
        if df.empty: return
        
        # Agrupamos por fecha para ver la tendencia de dinero
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        resumen = df.groupby('Fecha')['Total'].sum().reset_index()

        fig = Figure(figsize=(8, 2), dpi=80, facecolor=PALETA["sidebar"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(PALETA["sidebar"])
        ax.plot(resumen['Fecha'].astype(str), resumen['Total'], color="#4ADE80", marker='o', linewidth=2)
        
        ax.tick_params(colors="white", labelsize=7)
        for spine in ax.spines.values(): spine.set_visible(False)
        
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafica)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=5)

    def generar_reporte(self):
        # Limpiar lista
        for widget in self.scroll_reporte.winfo_children(): widget.destroy()
        cliente = self.entry_cliente.get().strip()

        try:
            conn = conectar_bd()
            
            # --- LÓGICA DE PRODUCTO ESTRELLA (Tu código original intacto) ---
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.Nombre, SUM(d.Cantidad) as total 
                FROM Detalle_Ventas d
                JOIN Productos p ON d.ID_Producto = p.ID_Producto
                GROUP BY d.ID_Producto ORDER BY total DESC LIMIT 1
            """)
            top = cursor.fetchone()
            if top: self.card_top.configure(text=f"{top[0]} ({top[1]})")

            # --- LÓGICA DE DATOS CON PANDAS ---
            query = "SELECT * FROM Ventas WHERE 1=1"
            params = []
            if cliente:
                query += " AND Cliente LIKE ?"
                params.append(f'%{cliente}%')
            
            df = pd.read_sql_query(query, conn, params=params)
            
            # Actualizar tarjetas de dinero y cantidad
            self.card_total.configure(text=f"$ {df['Total'].sum():,.2f}")
            self.card_cantidad.configure(text=str(len(df)))

            # Dibujar la gráfica sin borrar nada más
            self.dibujar_grafica(df)

            # Llenar el historial detallado
            for _, v in df.iterrows():
                f = ctk.CTkFrame(self.scroll_reporte, fg_color=PALETA["sidebar"])
                f.pack(fill="x", pady=2, padx=5)
                ctk.CTkLabel(f, text=f"ID: {v['ID_Venta']} | 👤 {v['Cliente']} | 💰 ${v['Total']:.2f}").pack(side="left", padx=10)

            conn.close()
        except Exception as e:
            print(f"Error, Fallo al cargar el reporte: {e}")

    def exportar_a_excel(self):
        try:
            conn = conectar_bd()
            # Usamos pandas para leer la tabla completa o filtrada
            df = pd.read_sql_query("SELECT * FROM Ventas", conn)
            conn.close()

            # Aplicar mismos filtros que en la UI si el usuario escribió algo
            cliente = self.entry_cliente.get()
            if cliente:
                df = df[df['Cliente'].str.contains(cliente, case=False, na=False)]

            if df.empty:
                messagebox.showwarning("Aviso", "No hay datos para exportar.")
                return

            ruta = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                               filetypes=[("Excel", "*.xlsx")],
                                               initialfile=f"Reporte_{datetime.now().strftime('%d_%m_%Y')}.xlsx")
            if ruta:
                df.to_excel(ruta, index=False)
                messagebox.showinfo("Éxito", "Excel guardado.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")