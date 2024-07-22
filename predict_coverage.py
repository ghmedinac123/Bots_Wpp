from flask import Flask, request, jsonify
import requests
import re
import json
import tensorflow as tf
import pickle
from sklearn.preprocessing import StandardScaler
from geopy.distance import geodesic
import logging

# Configurar el registro
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Para evitar escapes Unicode

# Configuración de Google Maps API Key
GOOGLE_MAPS_API_KEY = 'AIzaSyBRlPWGEbAQ0cZa-myo6PQPpMMWovKBDA4'

# Cargar el modelo y el escalador
logger.info("Cargando el modelo y el escalador...")
with open('scaler.pickle', 'rb') as handle:
    scaler = pickle.load(handle)
model = tf.keras.models.load_model('coverage_model')

# Cargar los datos del mapa
try:
    logger.info("Cargando los datos del mapa...")
    with open('map_data.json', 'r') as f:
        map_data = json.load(f)
    logger.info("✅ Datos del mapa cargados exitosamente")
except FileNotFoundError:
    logger.error("❌ Error: 'map_data.json' no encontrado.")
    exit()
except Exception as e:
    logger.error(f"❌ Error al cargar los datos del mapa: {e}")
    exit()

# Función para convertir dirección en coordenadas
def get_coordinates(address):
    logger.info(f"Convirtiendo dirección a coordenadas: {address}")
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {
        'address': address,
        'key': GOOGLE_MAPS_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json()['results']
        if results:
            location = results[0]['geometry']['location']
            lat, lng = location['lat'], location['lng']
            logger.info(f"Coordenadas obtenidas: {lat}, {lng}")
            return lat, lng
        logger.warning("No se pudieron obtener coordenadas para la dirección proporcionada")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en la conexión con la API de Google Maps: {e}")
    return None, None

# Función para validar si una entrada es una coordenada
def is_coordinate(input_str):
    logger.info(f"Validando si la entrada es una coordenada: {input_str}")
    pattern = re.compile(r'^-?\d+(\.\d+)?$')
    parts = input_str.split(',')
    if len(parts) == 2 and pattern.match(parts[0].strip()) and pattern.match(parts[1].strip()):
        logger.info("La entrada es una coordenada válida")
        return True
    logger.warning("La entrada no es una coordenada válida")
    return False

# Función para predecir la cobertura basado en la red neuronal y verificar si está dentro de algún círculo de cobertura
def predict_coverage(lat, lng):
    logger.info(f"Prediciendo cobertura para las coordenadas: {lat}, {lng}")
    coords = scaler.transform([[lat, lng]])
    prediction = model.predict(coords)
    logger.info(f"Resultado de la predicción: {prediction[0][0]}")
    
    if prediction[0][0] > 0.5:
        for circle in map_data:
            center = (circle['center']['lat'], circle['center']['lng'])
            radius = circle['radius']
            distance = geodesic((lat, lng), center).meters
            if distance <= radius:
                logger.info(f"Las coordenadas están dentro de la cobertura (distancia: {distance} metros)")
                return True
    logger.info("Las coordenadas no están dentro de la cobertura")
    return False

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    logger.info(f"Datos recibidos: {data}")
    if 'address' in data:
        address = data['address']
        coordinates = get_coordinates(address)
        if coordinates:
            lat, lng = coordinates
            has_coverage = predict_coverage(lat, lng)
            result = {
                'coverage': 'Sí' if has_coverage else 'No',
                'coordinates': {
                    'latitude': lat,
                    'longitude': lng
                }
            }
            logger.info(f"Respuesta de cobertura: {result}")
            return jsonify(result)
        else:
            logger.error("No se pudieron convertir las coordenadas")
            return jsonify({'error': 'No se pudieron convertir las coordenadas'}), 400
    elif 'coordinates' in data:
        coordinates = data['coordinates']
        if is_coordinate(coordinates):
            lat, lng = map(float, coordinates.split(','))
            has_coverage = predict_coverage(lat, lng)
            result = {
                'coverage': 'Sí' if has_coverage else 'No',
                'coordinates': {
                    'latitude': lat,
                    'longitude': lng
                }
            }
            logger.info(f"Respuesta de cobertura: {result}")
            return jsonify(result)
        else:
            logger.error("Formato de coordenadas inválido")
            return jsonify({'error': 'Formato de coordenadas inválido'}), 400
    else:
        logger.error("Entrada no válida")
        return jsonify({'error': 'Entrada no válida'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)
