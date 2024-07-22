from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
import traceback
from rich.logging import RichHandler
from rich.console import Console

app = Flask(__name__)
CORS(app)

API_KEY = "AIzaSyBysP4CQ_2dkZIKYWPkq1wxx5-etGK1ri0"  # Reemplaza esto con tu clave API
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}"
PROMPT_FILE_PATH = "/home/FututelBots/newBots2/base-baileys-mysql/mensajes/preguntas_respuestas.txt"

# Configurar logging con Rich
console = Console()
logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])
logger = logging.getLogger("rich")

def read_prompt_file():
    try:
        with open(PROMPT_FILE_PATH, 'r') as file:
            return file.read()
    except Exception as e:
        logger.error("❌ Error al leer el archivo de prompt: {}".format(e))
        logger.error("🔍 Stack trace: {}".format(traceback.format_exc()))
        return ""

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')

    logger.info("📥 Mensaje recibido: {}".format(message))

    prompt = read_prompt_file()
    if not prompt:
        return jsonify({"reply": "Lo siento, no se pudo leer el archivo de prompt."})

    try:
        headers = {
            'Content-Type': 'application/json',
        }
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"text": message}
                    ]
                }
            ]
        }
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        if 'candidates' in result and len(result['candidates']) > 0:
            reply = result['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            reply = "Lo siento, no pude generar una respuesta adecuada."
    except requests.exceptions.HTTPError as e:
        logger.error("⚠️ Error de HTTP: {}".format(e))
        reply = "Lo siento, hubo un error de comunicación con el servicio de AI."
    except Exception as e:
        logger.error("❌ Error al generar respuesta: {}".format(e))
        logger.error("🔍 Stack trace: {}".format(traceback.format_exc()))
        reply = "Lo siento, hubo un error procesando tu solicitud."

    logger.info("💬 Respuesta generada: {}".format(reply))
    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
