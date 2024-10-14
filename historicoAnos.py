import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os

# Ruta del escritorio
desktop_path = r"D:\USUARIO\Desktop"

# Crear una carpeta llamada "Revistas" en el escritorio si no existe
folder_path = os.path.join(desktop_path, "Revistas")
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

# Leer el archivo JSON que contiene los IDs de las revistas desde la carpeta "Revistas"
json_input_path = os.path.join(folder_path, 'RevistasNacionales.json')
with open(json_input_path, 'r', encoding='utf-8') as f:
    ids_df = pd.read_json(f)

# Listas para almacenar los artículos y clasificaciones
all_articles_data = []
all_classifications_data = []

# Usar requests.Session para mantener una conexión persistente
session = requests.Session()

# Función para manejar cada solicitud de manera segura con reintentos
def fetch_data_from_api(revista_id):
    url = f"https://scienti.minciencias.gov.co/publindex/api/publico/revistasPublindex/{revista_id}?staArticulo=true"
    
    retries = 3
    for attempt in range(retries):
        try:
            response = session.get(url, timeout=10)  # Timeout reducido para evitar largas demoras
            response.raise_for_status()  # Verificar si hubo errores en la solicitud
            data = response.json()
            return revista_id, data
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(2)  # Retraso antes del próximo intento
            else:
                print(f"Error persistente al hacer la solicitud para ID {revista_id}: {e}")
                return revista_id, None
        except ValueError:
            print(f"Error al parsear JSON para ID {revista_id}")
            return revista_id, None

# Función para procesar los datos recibidos
def process_data(revista_id, data):
    # Extraer clasificaciones si están disponibles
    if data and "clasificaciones" in data and data["clasificaciones"]:
        for clasificacion in data["clasificaciones"]:
            all_classifications_data.append({
                "ID_REVISTA": revista_id,
                "clasificacion": clasificacion
            })
    
    # Extraer artículos si están disponibles
    if data and "articulos" in data and data["articulos"]:
        for articulo in data["articulos"]:
            all_articles_data.append({
                "ID_REVISTA": revista_id,
                "anoPublicacion": articulo.get("anoPublicacion", "No disponible"),
                "id": articulo.get("id", "No disponible"),
                "txtTituloArticulo": articulo.get("txtTituloArticulo", "No disponible")
            })

# Determinar el número óptimo de hilos
def determine_optimal_threads():
    return min(50, max(5, len(ids_df) // 10))

# Usar ThreadPoolExecutor para hacer las solicitudes en paralelo
num_workers = determine_optimal_threads()
print(f"Usando {num_workers} hilos para procesamiento.")
start_time = time.time()

with ThreadPoolExecutor(max_workers=num_workers) as executor:
    future_to_id = {executor.submit(fetch_data_from_api, revista_id): revista_id for revista_id in ids_df['ID_REVISTA']}
    
    for count, future in enumerate(as_completed(future_to_id), 1):
        revista_id = future_to_id[future]
        try:
            revista_id, data = future.result()
            if data:  # Solo procesar si hay datos
                process_data(revista_id, data)
            elapsed_time = time.time() - start_time
            print(f"[{count}/{len(ids_df)}] Procesado ID {revista_id}. Tiempo transcurrido: {elapsed_time:.2f} segundos")
        except Exception as exc:
            print(f"Error al procesar los datos para ID {revista_id}: {exc}")

# Guardar resultados en la carpeta "Revistas"
if all_articles_data:
    articles_df = pd.DataFrame(all_articles_data)
    articles_output_path = os.path.join(folder_path, 'articles.json')
    articles_df.to_json(articles_output_path, orient='records', indent=4, force_ascii=False)
    print(f"Datos de artículos guardados en '{articles_output_path}'.")
else:
    print("No se encontraron datos de artículos.")

if all_classifications_data:
    classifications_df = pd.DataFrame(all_classifications_data)
    classifications_output_path = os.path.join(folder_path, 'classifications.json')
    classifications_df.to_json(classifications_output_path, orient='records', indent=4, force_ascii=False)
    print(f"Datos de clasificaciones guardados en '{classifications_output_path}'.")
else:
    print("No se encontraron datos de clasificaciones.")
