from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import requests  # Importado por si se requiere comunicación saliente en el futuro

app = Flask(__name__)
CORS(app)

SERVICE_PORT = 5003
SERVICE_NAME = "Productos"
DATABASE_PATH = "../database/inventario.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "success", "message": f"{SERVICE_NAME} OK en puerto {SERVICE_PORT}"}), 200

@app.route('/api/productos/<int:id>', methods=['GET'])
def obtener_producto(id):
    try:
        # 1. Aquí Celeste programará el SELECT en la tabla de productos
        # Mock de respuesta para que Alan pueda probar su requests.get()
        mock_producto = {
            "id": id,
            "nombre": "Leche Pil 980cc",
            "categoria": "Lácteos"
        }
        return jsonify({"status": "success", "data": mock_producto}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=SERVICE_PORT)