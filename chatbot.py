import os
import json
import requests
from flask import Flask, request, jsonify
from google.auth import default
from google.auth.transport.requests import Request
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener las variables de entorno
gemini_api_key = os.getenv("GEMINI_API_KEY")
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not gemini_api_key:
    raise EnvironmentError("La variable de entorno GEMINI_API_KEY no está configurada correctamente.")
if not credentials_path:
    raise EnvironmentError("La variable de entorno GOOGLE_APPLICATION_CREDENTIALS no está configurada correctamente.")

print(f"Using credentials from: {credentials_path}")

# Inicializar la aplicación Flask
app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get('text', '')

    print(f"Received request: {data}")

    # Leer el archivo de instrucciones
    with open('/home/FututelBots/newBots2/base-baileys-mysql/mensajes/preguntas_respuestas.txt', 'r', encoding='utf-8') as file:
        system_instruction_text = file.read()

    # Autenticación y obtención del token de acceso
    credentials, _ = default()
    credentials.refresh(Request())
    token = credentials.token

    API_ENDPOINT = "us-central1-aiplatform.googleapis.com"
    PROJECT_ID = "gen-lang-client-0249358186"
    LOCATION_ID = "us-central1"
    MODEL_ID = "gemini-1.5-pro-001"

    url = f"https://{API_ENDPOINT}/v1/projects/{PROJECT_ID}/locations/{LOCATION_ID}/publishers/google/models/{MODEL_ID}:streamGenerateContent"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": user_input
                    },
                ]
            },
        ],
        "systemInstruction": {
            "parts": [
                {
                    "text": system_instruction_text
                },
            ]
        },
        "generationConfig": {
            "maxOutputTokens": 8192,
            "temperature": 1,
            "topP": 0.95,
        },
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ],
    }

    print(f"Sending request to Gemini API: {json.dumps(payload, indent=2)}")

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        response_data = response.json()
        print(f"Response from Gemini API: {json.dumps(response_data, indent=2)}")
        
        # Procesar y enviar la respuesta directamente al usuario
        if isinstance(response_data, list):
            full_response_text = ''
            for candidate_set in response_data:
                candidates = candidate_set.get('candidates', [])
                for candidate in candidates:
                    for part in candidate['content']['parts']:
                        full_response_text += part['text']

            print(f"Message to be returned to user: {full_response_text}")
            return jsonify({"text": full_response_text})
        else:
            print("Unexpected response format:", response_data)
            return jsonify({"error": "Unexpected response format"}), 500
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return jsonify({"error": response.text}), response.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6002)
