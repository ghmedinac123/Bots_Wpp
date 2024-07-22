#!/bin/bash

# Variables
API_KEY="AIzaSyBysP4CQ_2dkZIKYWPkq1wxx5-etGK1ri0"
INPUT_MP3="input.mp3"
OUTPUT_WAV="output.wav"
BASE64_TXT="audio_base64.txt"
REQUEST_JSON="request.json"

# Convertir MP3 a WAV
ffmpeg -i "$INPUT_MP3" -ar 16000 -ac 1 "$OUTPUT_WAV"

# Codificar WAV en base64
base64 "$OUTPUT_WAV" > "$BASE64_TXT"

# Crear archivo JSON
echo '{
  "config": {
    "encoding": "LINEAR16",
    "sampleRateHertz": 16000,
    "languageCode": "es-ES"
  },
  "audio": {
    "content": "'$(cat $BASE64_TXT)'"
  }
}' > "$REQUEST_JSON"

# Enviar solicitud curl
curl -X POST \
  -H "Content-Type: application/json" \
  --data @"$REQUEST_JSON" \
  "https://speech.googleapis.com/v1/speech:recognize?key=$API_KEY"
