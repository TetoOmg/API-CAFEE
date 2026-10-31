from flask import Flask, request, jsonify
from flask_cors import CORS

# Inicialización de la aplicación
app = Flask(__name__)

# Habilitar CORS para permitir peticiones desde GitHub Pages
CORS(app)

# Definición de la ruta (endpoint) que recibe la petición HTTP POST del carrito
@app.route('/api/checkout', methods=['POST'])
def procesar_pago():
    # Extraer los datos enviados desde el HTML en formato JSON
    datos_recibidos = request.get_json()
    
    if not datos_recibidos:
        return jsonify({"error": "No se recibieron datos de la orden"}), 400
    
    # Extraer variables específicas
    carrito = datos_recibidos.get('carrito', [])
    total = datos_recibidos.get('total', 0)
    usuario = datos_recibidos.get('usuario', "Cliente Anónimo")
    
    # Aquí se procesa la información (ej. guardar en base de datos)
    print(f"--- NUEVA ORDEN RECIBIDA ---")
    print(f"Cliente: {usuario}")
    print(f"Total a cobrar: ${total} MXN")
    print("Artículos:")
    for articulo in carrito:
        print(f" - {articulo['cantidad']}x {articulo['nombre']} (${articulo['precio']})")
    print("----------------------------")
    
    # El mesero (HTTP) devuelve la respuesta al Front-end
    respuesta = {
        "estado": "exito",
        "mensaje": f"Orden de {usuario} procesada correctamente por ${total} MXN."
    }
    return jsonify(respuesta), 200

# Arranque del servidor
if __name__ == '__main__':
    # El puerto 5000 es el predeterminado de Flask
    app.run(debug=True, host='0.0.0.0', port=5000)