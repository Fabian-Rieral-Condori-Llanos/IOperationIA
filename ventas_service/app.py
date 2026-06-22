from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import requests  # Importación añadida para comunicación entre servicios

app = Flask(__name__)
# Habilitar CORS para permitir peticiones desde el frontend de la SPA
CORS(app)

# CONFIGURACIÓN DEL ARQUITECTO: 
# Cambiar esto según el servicio:
# Ventas=5001, Inventario=5002, Productos=5003, Clientes=5004, Notificaciones=5005
SERVICE_PORT = 5001 
SERVICE_NAME = "Ventas"
DATABASE_PATH = "../database/ventas.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "success", "message": f"{SERVICE_NAME} OK en puerto {SERVICE_PORT}"}), 200

@app.route('/api/ventas', methods=['POST'])
def registrar_venta():
    try:
        data = request.json
        # 1. Aquí Marcelo programará el INSERT en ventas.db
        
        # 2. Ejemplo de uso de 'requests': Publicar evento de Venta Realizada
        evento = {
            "evento": "VENTA_CONFIRMADA",
            "origen": "ventas_service",
            "payload": {"cliente_uid": data.get("cliente_uid"), "total": data.get("total")}
        }
        
        # Llamada HTTP al microservicio de Notificaciones (Broker en el puerto 5005)
        broker_url = 'http://127.0.0.1:5005/api/eventos/publicar'
        respuesta = requests.post(broker_url, json=evento)
        
        if respuesta.status_code == 201:
            return jsonify({"status": "success", "data": "Venta registrada y evento publicado"}), 201
        else:
            return jsonify({"status": "warning", "data": "Venta registrada, pero falló la notificación"}), 207
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=SERVICE_PORT)