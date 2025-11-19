import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("=== Estructura de la tabla inventory_movements ===")
cursor.execute("PRAGMA table_info(inventory_movements)")
columns = cursor.fetchall()

for col in columns:
    print(f"  {col[1]} ({col[2]}) - NotNull: {col[3]} - Default: {col[4]}")

conn.close()
