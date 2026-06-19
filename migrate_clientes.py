import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'restaurante.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cliente (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telefone VARCHAR(20) UNIQUE NOT NULL,
        senha_hash VARCHAR(200) NOT NULL,
        nome VARCHAR(100) NOT NULL,
        endereco_padrao VARCHAR(200),
        preferencia_entrega VARCHAR(20) DEFAULT 'RETIRADA'
    )
    """)
    print("Table 'cliente' created or already exists.")
except Exception as e:
    print("Error creating table:", e)

try:
    cursor.execute("ALTER TABLE pedido ADD COLUMN cliente_id INTEGER REFERENCES cliente(id)")
    print("Added cliente_id to pedido.")
except Exception as e:
    print("Error altering pedido (might already exist):", e)

conn.commit()
conn.close()
