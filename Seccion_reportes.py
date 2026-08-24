import customtkinter as ctk
import pandas as pd
from conexion_base import conectar_bd
from tkinter import messagebox, filedialog
from datetime import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class SeccionReportes(ctk.CTkFrame):
    def __init__(self, master, rol):
        super().__init__(master, fg_color="transparent")
        self.rol = rol.lower()
        
        ctk.CTkLabel(self, text="📊 Inteligencia Financiera", font=("Roboto", 28, "bold"), text_color="#DBF0DD").pack(pady=10)

        self.frame_tools = ctk.CTkFrame(self, fg_color="#173831", corner_radius=10)
        self.frame_tools.pack(pady=5, padx=40, fill="x")

        fecha_hoy = datetime.now().strftime('%Y-%m-%d')
        
        ctk.CTkLabel(self.frame_tools, text="📅 Desde:").pack(side="left", padx=5)
        self.ent_inicio = ctk.CTkEntry(self.frame_tools, width=100); self.ent_inicio.insert(0, fecha_hoy); self.ent_inicio.pack(side="left", padx=5, pady=10)

        ctk.CTkLabel(self.frame_tools, text="Hasta:").pack(side="left", padx=5)
        self.ent_fin = ctk.CTkEntry(self.frame_tools, width=100); self.ent_fin.insert(0, fecha_hoy); self.ent_fin.pack(side="left", padx=5)

        ctk.CTkButton(self.frame_tools, text="🔄 Filtrar", fg_color="#235347", command=self.generar_reporte).pack(side="left", padx=15)
        ctk.CTkButton(self.frame_tools, text="📉 Excel", width=80, fg_color="#1D6F42", command=self.exportar_a_excel).pack(side="left", padx=5)

        self.frame_cards = ctk.CTkFrame(self, fg_color="transparent"); self.frame_cards.pack(fill="x", padx=40, pady=10)
        self.card_ventas = self.crear_tarjeta("Ventas Brutas", "$ 0.00", "#4ADE80")
        self.card_costos = self.crear_tarjeta("Inversión", "$ 0.00", "#E74C3C")
        self.card_ganancia = self.crear_tarjeta("Ganancia Real", "$ 0.00", "#E67E22")

        self.frame_grafica = ctk.CTkFrame(self, fg_color="#173831", corner_radius=15, height=200); self.frame_grafica.pack(fill="x", padx=40, pady=5)
        self.scroll_reporte = ctk.CTkScrollableFrame(self, fg_color="#0A2A2B", height=200); self.scroll_reporte.pack(pady=10, padx=40, fill="both", expand=True)

        self.generar_reporte()

    def crear_tarjeta(self, t, v, c):
        card = ctk.CTkFrame(self.frame_cards, fg_color="#173831", corner_radius=15); card.pack(side="left", padx=10, expand=True, fill="both")
        ctk.CTkLabel(card, text=t, font=("Roboto", 11)).pack(pady=(5,0))
        lbl = ctk.CTkLabel(card, text=v, font=("Roboto", 20, "bold"), text_color=c); lbl.pack(pady=10)
        return lbl

    def generar_reporte(self):
        for w in self.scroll_reporte.winfo_children(): w.destroy()
        ini, fin = self.ent_inicio.get().strip(), self.ent_fin.get().strip()
        
        try:
            conn = conectar_bd()
            query_v = """SELECT V.ID_Venta, V.Fecha, V.Total, GROUP_CONCAT(P.Nombre, ', ') as Productos
                         FROM Ventas V
                         JOIN Detalle_Ventas DV ON V.ID_Venta = DV.ID_Venta
                         JOIN Productos P ON DV.ID_Producto = P.ID_Producto
                         WHERE V.Fecha BETWEEN ? AND ? GROUP BY V.ID_Venta"""
            df_v = pd.read_sql_query(query_v, conn, params=(ini, fin))
            
            query_f = """SELECT d.Cantidad, p.Precio_Costo FROM Detalle_Ventas d 
                         JOIN Ventas v ON d.ID_Venta = v.ID_Venta 
                         JOIN Productos p ON d.ID_Producto = p.ID_Producto WHERE v.Fecha BETWEEN ? AND ?"""
            df_f = pd.read_sql_query(query_f, conn, params=(ini, fin)); conn.close()

            if df_v.empty: return

            total_v = df_v['Total'].sum()
            total_c = (df_f['Cantidad'] * df_f['Precio_Costo']).sum()
            
            self.card_ventas.configure(text=f"$ {total_v:,.2f}")
            self.card_costos.configure(text=f"$ {total_c:,.2f}")
            self.card_ganancia.configure(text=f"$ {(total_v - total_c):,.2f}")

            for _, v in df_v.iterrows():
                f = ctk.CTkFrame(self.scroll_reporte, fg_color="#173831")
                f.pack(fill="x", pady=2, padx=5)
                ctk.CTkLabel(f, text=f"ID: {v['ID_Venta']} | {v['Productos']} | ${v['Total']:.2f}").pack(side="left", padx=10)
            
            self.dibujar_grafica(df_v)
        except: pass

    def dibujar_grafica(self, df):
        for w in self.frame_grafica.winfo_children(): w.destroy()
        if df.empty: return
        fig = Figure(figsize=(5, 2), facecolor="#173831")
        ax = fig.add_subplot(111); ax.set_facecolor("#173831")
        resumen = df.groupby('Fecha')['Total'].sum()
        ax.plot(resumen.index, resumen.values, color="#4ADE80", marker='o')
        ax.tick_params(colors="white", labelsize=7)
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafica); canvas.draw(); canvas.get_tk_widget().pack(fill="both", expand=True)

    def exportar_a_excel(self):
        fecha_hoy = datetime.now().strftime('%Y-%m-%d')
        nombre_sugerido = f"Reporte_Ventas_{fecha_hoy}.xlsx"
        
        try:
            conn = conectar_bd()
            # Traemos los datos
            df = pd.read_sql_query("SELECT * FROM Ventas WHERE Fecha BETWEEN ? AND ?", 
                                   conn, params=(self.ent_inicio.get(), self.ent_fin.get()))
            conn.close()

            if df.empty:
                messagebox.showwarning("Atención", "No hay datos en el rango seleccionado")
                return

            ruta = filedialog.asksaveasfilename(defaultextension=".xlsx", 
                                               initialfile=nombre_sugerido, 
                                               filetypes=[("Excel", "*.xlsx")])
            
            if ruta:
                # --- AQUÍ EMPIEZA LA MAGIA ---
                # Usamos xlsxwriter como motor para poder dar formato
                with pd.ExcelWriter(ruta, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Ventas_Nexus')
                    
                    workbook  = writer.book
                    worksheet = writer.sheets['Ventas_Nexus']

                    # Creamos el formato de dinero (USD $ #,##0.00)
                    formato_moneda = workbook.add_format({
                        'num_format': '$#,##0.00',
                        'align': 'center'
                    })

                    # Formato para el encabezado (opcional, para que combine con tus azules de la imagen 3)
                    formato_header = workbook.add_format({
                        'bold': True,
                        'bg_color': '#1B263B', # El azul de tu sidebar
                        'font_color': 'white',
                        'border': 1
                    })

                    # Aplicamos el formato de moneda a la columna 'Total'
                    # Suponiendo que 'Total' es la columna D (índice 2)
                    # Ajustamos el ancho a 15 para que no salgan los "###"
                    worksheet.set_column('D:D', 15, formato_moneda)
                    
                    # (Opcional) Aplicamos formato al encabezado para que se vea pro
                    for col_num, value in enumerate(df.columns.values):
                        worksheet.write(0, col_num, value, formato_header)

                messagebox.showinfo("Éxito", "Excel generado con formato profesional")
        except Exception as e: 
            messagebox.showerror("Error", f"No se pudo generar el Excel: {e}")