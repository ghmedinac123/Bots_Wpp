import os
import subprocess
import requests
import json
import base64
import wave
import sys

API_KEY = "AIzaSyBysP4CQ_2dkZIKYWPkq1wxx5-etGK1ri0"

# Verifica que se haya proporcionado un argumento para el archivo de audio
if len(sys.argv) < 2:
    print("Error: se requiere la ruta del archivo de audio como argumento.")
    sys.exit(1)

# Ruta del archivo de audio recibida como argumento
audio_file_path = sys.argv[1]
wav_file_path = audio_file_path.replace(".ogg", ".wav")

# Verificar si el archivo OGG existe
if not os.path.exists(audio_file_path):
    print(json.dumps({"error": f"El archivo {audio_file_path} no existe."}))
    sys.exit(1)

# Usar ffmpeg para convertir OGG a WAV
try:
    ffmpeg_command = f"ffmpeg -i {audio_file_path} {wav_file_path}"
    result = subprocess.run(ffmpeg_command, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(json.dumps({"error": f"Error en ffmpeg: {result.stderr}"}))
        sys.exit(1)
except Exception as e:
    print(json.dumps({"error": f"Ocurrió un error inesperado: {e}"}))
    sys.exit(1)

# Obtener la tasa de muestreo del archivo WAV
try:
    with wave.open(wav_file_path, 'rb') as wav_file:
        sample_rate_hertz = wav_file.getframerate()
except wave.Error as e:
    print(json.dumps({"error": f"Error al abrir el archivo WAV: {e}"}))
    sys.exit(1)

# Leer el archivo de audio y convertirlo a base64
try:
    with open(wav_file_path, "rb") as audio_file:
        audio_content = base64.b64encode(audio_file.read()).decode('utf-8')
except FileNotFoundError as e:
    print(json.dumps({"error": f"Error al leer el archivo WAV: {e}"}))
    sys.exit(1)

# Configuración de la solicitud
request_url = f"https://speech.googleapis.com/v1p1beta1/speech:recognize?key={API_KEY}"
headers = {
    "Content-Type": "application/json"
}
data = {
    "config": {
        "encoding": "LINEAR16",
        "sample_rate_hertz": sample_rate_hertz,
        "language_code": "es-ES",
        "enableAutomaticPunctuation": True
    },
    "audio": {
        "content": audio_content
    }
}

# Enviar la solicitud a la API de Google Speech-to-Text
response = requests.post(request_url, headers=headers, data=json.dumps(data))

# Procesar la respuesta
response_data = response.json()

if "results" in response_data:
    transcripts = []
    for result in response_data["results"]:
        for alternative in result["alternatives"]:
            transcripts.append(alternative["transcript"])
    print(json.dumps({"transcript": " ".join(transcripts)}))
else:
    print(json.dumps({"error": "No se encontró ninguna transcripción en la respuesta.", "response": response_data}))

# Eliminar archivos temporales
try:
    os.remove(audio_file_path)
    os.remove(wav_file_path)
except FileNotFoundError as e:
    print(json.dumps({"error": f"Error al eliminar archivos temporales: {e}"}))
