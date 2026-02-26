import sqlite3
import os
import sys

def conectar_bd():
    # Esta línea detecta si estamos ejecutando el código o el .exe
    if getattr(sys, 'frozen', False):
        # Si es el .exe, busca en la carpeta del ejecutable
        ruta_base = os.path.dirname(sys.executable)
    else:
        # Si es código normal, busca en la carpeta del script
        ruta_base = os.path.dirname(os.path.abspath(__file__))
    
    ruta_db = os.path.join(ruta_base, "inventario.db")
    
    try:
        conexion = sqlite3.connect(ruta_db)
        return conexion
    except Exception as e:
        print(f"Error conectando a la base: {e}")
        return None