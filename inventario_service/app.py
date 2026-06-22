from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import requests  # Importación añadida para comunicación entre servicios

app = Flask(__name__)
CORS(app)

SERVICE_PORT = 5002
SERVICE_NAME = "Inventario"
DATABASE_PATH = "../database/inventario.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "success", "message": f"{SERVICE_NAME} OK en puerto {SERVICE_PORT}"}), 200

@app.route('/api/inventario/baja', methods=['POST'])
def registrar_baja():
    try:
        data = request.json
        # 1. Aquí Alan programa el UPDATE para restar stock en inventario.db
        
        # 2. Ejemplo de uso de 'requests': Consultar el nombre del producto al puerto 5003
        producto_id = data.get("producto_id")
        producto_url = f'http://127.0.0.1:5003/api/productos/{producto_id}'
        respuesta_producto = requests.get(producto_url)
        
        nombre_producto = "Producto Desconocido"
        if respuesta_producto.status_code == 200:
            nombre_producto = respuesta_producto.json().get("data", {}).get("nombre", "")

        return jsonify({"status": "success", "data": f"Baja registrada para {nombre_producto}"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=SERVICE_PORT)