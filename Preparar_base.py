import sqlite3

def conectar_bd():
    conn = sqlite3.connect("inventario_rick.db")
    return conn

def crear_tablas():
    conn = conectar_bd()
    cursor = conn.cursor()
    # Tabla de Usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Usuarios (
        ID_Usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        Nombre TEXT NOT NULL,
        Usuario TEXT UNIQUE NOT NULL,
        Password TEXT NOT NULL,
        Rol TEXT NOT NULL
    )""")
    # Tabla de Productos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Productos (
        ID_Producto INTEGER PRIMARY KEY AUTOINCREMENT,
        Nombre TEXT NOT NULL,
        Stock INTEGER DEFAULT 0,
        Precio REAL DEFAULT 0.0
    )""")
    # Tabla de Pedidos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Pedidos (
        ID_Pedido INTEGER PRIMARY KEY AUTOINCREMENT,
        Nombre_Entidad TEXT,
        Producto TEXT,
        Cantidad INTEGER,
        Tipo TEXT,
        Estado TEXT DEFAULT 'Pendiente'
    )""")
    # Tabla de Ventas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Ventas (
        ID_Venta INTEGER PRIMARY KEY AUTOINCREMENT,
        Cliente TEXT,
        Fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        Total REAL
    )""")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    crear_tablas()