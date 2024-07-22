import requests
import json
from geopy.distance import geodesic
import pandas as pd

print("Iniciando el script...")

# API key de Google Maps
API_KEY = 'AIzaSyBRlPWGEbAQ0cZa-myo6PQPpMMWovKBDA4'

# Cargar los datos de usuarios con coordenadas
try:
    df = pd.read_csv('usuarios_con_coordenadas.csv')
    print("Datos cargados exitosamente")
except FileNotFoundError:
    print("Error: 'usuarios_con_coordenadas.csv' no encontrado.")
    exit()
except Exception as e:
    print(f"Error al cargar los datos: {e}")
    exit()

print(f"Cargadas {len(df)} coordenadas")

# Función para generar un círculo en Google Maps
def generar_circulo(lat, lng, radio):
    circulo = {
        "center": {
            "lat": lat,
            "lng": lng
        },
        "radius": radio
    }
    return circulo

# Generar círculos con diferentes radios
try:
    print("Generando círculos...")
    datos_mapa = []
    for index, row in df.iterrows():
        lat = row['latitude']
        lng = row['longitude']
        direccion = row['direccion_principal']
        
        # Asignar radio basado en la dirección
        if direccion.startswith('Vereda'):
            radio = 300
        else:
            radio = 150
        
        datos_mapa.append(generar_circulo(lat, lng, radio))
    
    print(f"Generados {len(datos_mapa)} círculos")

    # Guardar los datos del mapa en un archivo JSON
    with open('map_data.json', 'w') as f:
        json.dump(datos_mapa, f)
    print("Datos del mapa guardados exitosamente")

except Exception as e:
    print(f"Error durante la generación de datos del mapa: {e}")

print("Script completado exitosamente")
