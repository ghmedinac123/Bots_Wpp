import os
from pydub import AudioSegment
import requests
import json
import base64
import wave

API_KEY = "AIzaSyBysP4CQ_2dkZIKYWPkq1wxx5-etGK1ri0"

# Ruta del archivo de audio
audio_file_path = "/home/FututelBots/newBots2/base-baileys-mysql/input.mp3"
wav_file_path = "/home/FututelBots/newBots2/base-baileys-mysql/input.wav"

# Convertir MP3 a WAV
audio = AudioSegment.from_mp3(audio_file_path)
audio.export(wav_file_path, format="wav")

# Obtener la tasa de muestreo del archivo WAV
with wave.open(wav_file_path, 'rb') as wav_file:
    sample_rate_hertz = wav_file.getframerate()

# Leer el archivo de audio y convertirlo a base64
with open(wav_file_path, "rb") as audio_file:
    audio_content = base64.b64encode(audio_file.read()).decode('utf-8')

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
    for result in response_data["results"]:
        for alternative in result["alternatives"]:
            print(json.dumps({"transcript": alternative["transcript"]}))
else:
    print(json.dumps({"error": "No se encontró ninguna transcripción en la respuesta.", "response": response_data}))
