import os
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configurar la API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("No API key found. Please set the GEMINI_API_KEY environment variable.")

genai.configure(api_key=api_key)

# Configuración del modelo
generation_config = {
    "temperature": 0.1,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

system_instruction = """
Eres un bot asistente de la empresa de Internet Fututel este texto son las posibles preguntas y respuestas la pregunta la hace el usuario y en base a este texto vas a responder en español siempre busca la pregunta que llega algo similar y responde con dicha respuesta si no encuentras algo similar responde que no fuiste entrenado para responder este tipo de preguntas
NO reenvies la pregunta solo envia la respuesta y dile al usuario que si tiene otra pregunta y para ello que escriba 'Menu' opcion 4
Por favor lee una a una cada pregunta y asociala con la pregunta que hace el usuario estas son tus instrucciones y lo que debes responder si no hay algo aquí dentro del contexto de lo que pregunta el usuario respondele que no estás entrenado para responder estas preguntas

## Preguntas y Respuestas para Solicitar el Servicio de Fututel Internet 
<...tu texto completo aquí...>
"""

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')

    print(f"Mensaje recibido: {message}")

    combined_prompt = f"{system_instruction}\n\nPregunta: {message}\nRespuesta:"

    try:
        response = genai.generate_text(
            model="models/gemini-1.5-pro",
            prompt=combined_prompt,
            temperature=generation_config["temperature"],
            top_p=generation_config["top_p"],
            top_k=generation_config["top_k"],
            max_output_tokens=generation_config["max_output_tokens"]
        )
        reply = response.generations[0].text.strip()
        return jsonify({"reply": reply})
    except Exception as e:
        print(f"Error al generar respuesta: {e}")
        return jsonify({"reply": "Lo siento, hubo un error procesando tu solicitud."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6002, debug=True)
