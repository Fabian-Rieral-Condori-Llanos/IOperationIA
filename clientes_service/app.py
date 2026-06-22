from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import requests  # Importación añadida para comunicación entre servicios

app = Flask(__name__)
CORS(app)

SERVICE_PORT = 5004
SERVICE_NAME = "Clientes"
DATABASE_PATH = "../database/ventas.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "success", "message": f"{SERVICE_NAME} OK en puerto {SERVICE_PORT}"}), 200

@app.route('/api/clientes', methods=['POST'])
def registrar_cliente():
    try:
        data = request.json
        # 1. Aquí Ronaldo programará el INSERT del cliente
        
        # 2. Ejemplo con 'requests': Publicar evento de Cliente Creado
        evento = {
            "evento": "CLIENTE_CREADO",
            "origen": "clientes_service",
            "payload": {"nombre": data.get("nombre"), "correo": data.get("correo")}
        }
        
        requests.post('http://127.0.0.1:5005/api/eventos/publicar', json=evento)
        
        return jsonify({"status": "success", "data": "Cliente creado exitosamente"}), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=SERVICE_PORT)