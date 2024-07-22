import pymysql
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from fuzzywuzzy import process, fuzz

# Descargar recursos necesarios para nltk
import nltk
nltk.download('punkt')
nltk.download('stopwords')

# Configuración de la base de datos
MYSQL_DB_HOST = 'localhost'
MYSQL_DB_USER = 'root'
MYSQL_DB_PASSWORD = 'GBBGH4R53A8FGLS'
MYSQL_DB_NAME = 'bots'
MYSQL_DB_PORT = 3306

# Conectar a la base de datos
connection = pymysql.connect(
    host=MYSQL_DB_HOST,
    user=MYSQL_DB_USER,
    password=MYSQL_DB_PASSWORD,
    database=MYSQL_DB_NAME,
    port=MYSQL_DB_PORT
)

# Definir palabras clave relacionadas con internet
keywords = ['soporte', 'factura', 'ventas', 'planes', 'servicios', 'internet', 'conexión']

def contains_keywords(message, keywords):
    words = word_tokenize(message.lower())
    return any(keyword in words for keyword in keywords)

try:
    # Obtener las preguntas (Tipo=usuario)
    query_usuario = "SELECT Mensajes FROM Chat_WhatsApp_Ventas WHERE Tipo='usuario'"
    df_usuario = pd.read_sql(query_usuario, connection)

    # Filtrar preguntas que contengan palabras clave
    df_usuario['Relevante'] = df_usuario['Mensajes'].apply(lambda x: contains_keywords(x, keywords))
    df_usuario_relevante = df_usuario[df_usuario['Relevante'] == True]

    # Obtener las respuestas (Tipo=local)
    query_local = "SELECT Mensajes FROM Chat_WhatsApp_Ventas WHERE Tipo='local'"
    df_local = pd.read_sql(query_local, connection)

    # Inicializar listas para almacenar preguntas y respuestas únicas
    preguntas_unicas = []
    respuestas_unicas = []

    # Encontrar pares de preguntas y respuestas
    pares = []
    for pregunta in df_usuario_relevante['Mensajes']:
        if pregunta not in preguntas_unicas:
            preguntas_unicas.append(pregunta)
            respuesta_match = process.extractOne(pregunta, df_local['Mensajes'], scorer=fuzz.token_sort_ratio)
            if respuesta_match:
                respuesta = respuesta_match[0]
                if respuesta not in respuestas_unicas:
                    respuestas_unicas.append(respuesta)
                    pares.append((pregunta, respuesta))

    # Generar el DataFrame con las preguntas y respuestas
    df_chat = pd.DataFrame(pares, columns=['Preguntas', 'Respuestas'])

    # Guardar el DataFrame en un archivo CSV
    df_chat.to_csv('conversaciones_chat.csv', index=False)

    print("Archivo 'conversaciones_chat.csv' generado exitosamente.")

finally:
    # Cerrar la conexión a la base de datos
    connection.close()
