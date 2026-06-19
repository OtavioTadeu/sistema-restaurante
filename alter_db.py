import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'restaurante.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE pedido ADD COLUMN forma_pagamento VARCHAR(50)")
    print("Added forma_pagamento")
except Exception as e:
    print(e)

try:
    cursor.execute("ALTER TABLE pedido ADD COLUMN troco_para VARCHAR(50)")
    print("Added troco_para")
except Exception as e:
    print(e)

conn.commit()
conn.close()
