import tensorflow as tf
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pickle
import json

print("Starting the script...")

# Cargar los datos del mapa
try:
    with open('map_data.json', 'r') as f:
        map_data = json.load(f)
    print("Map data loaded successfully")
except FileNotFoundError:
    print("Error: 'map_data.json' not found.")
    exit()
except Exception as e:
    print(f"Error loading map data: {e}")
    exit()

# Convertir los datos del mapa a un DataFrame
expanded_points = [(circle['center']['lat'], circle['center']['lng'], circle['radius']) for circle in map_data]
expanded_df = pd.DataFrame(expanded_points, columns=['latitude', 'longitude', 'radius'])
expanded_df['coverage'] = 1  # Asumir cobertura en estos puntos

print("Preparing data for training...")

# Preparación de datos
X = expanded_df[['latitude', 'longitude']].values
y = expanded_df['coverage'].values

# Generar puntos negativos (sin cobertura) para el entrenamiento
negatives = []
for _ in range(len(expanded_df) * 5):  # Generar más puntos negativos para balancear
    lat = np.random.uniform(X[:, 0].min() - 0.1, X[:, 0].max() + 0.1)
    lng = np.random.uniform(X[:, 1].min() - 0.1, X[:, 1].max() + 0.1)
    negatives.append((lat, lng, 0))

negatives_df = pd.DataFrame(negatives, columns=['latitude', 'longitude', 'coverage'])
full_df = pd.concat([expanded_df, negatives_df])

# División de datos en entrenamiento y prueba
X = full_df[['latitude', 'longitude']].values
y = full_df['coverage'].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Estandarización de los datos
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

print("Data standardized")

# Definición del modelo
model = tf.keras.models.Sequential([
    tf.keras.layers.Dense(256, activation='relu', input_shape=(X_train.shape[1],)),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(32, activation='relu'),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(1, activation='sigmoid')
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
print("Model compiled successfully")

model.fit(X_train, y_train, epochs=100, batch_size=32, validation_data=(X_test, y_test))
print("Model training completed")

# Guardar el modelo y el escalador
model.save('coverage_model')
with open('scaler.pickle', 'wb') as handle:
    pickle.dump(scaler, handle)

print("Model and scaler saved successfully")
