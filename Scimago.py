import os
import pandas as pd
import requests
import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

# Ruta del escritorio
desktop_path = r"D:\USUARIO\Desktop"

# Crear una carpeta llamada "Revistas" en el escritorio si no existe
folder_path = os.path.join(desktop_path, "Revistas")
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

# URL para descargar el archivo CSV
url = "https://www.scimagojr.com/journalrank.php?out=xls"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
}

# URL base para consultar detalles de Sourceid
base_url = "https://www.scimagojr.com/journalsearch.php?q={}&tip=sid&clean=0"

# Función para obtener la página con backoff exponencial
def get_page(session, url, retries=3, wait=2):
    for i in range(retries):
        try:
            response = session.get(url, headers=headers, timeout=2)
            if response.status_code == 200:
                return response
            elif response.status_code == 503:
                print(f"Servicio no disponible para {url}. Reintentando en {wait} segundos... (Intento {i+1} de {retries})")
                time.sleep(wait)
        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud: {e}. Reintentando en {wait} segundos... (Intento {i+1} de {retries})")
            time.sleep(wait * (2 ** i))  # Backoff exponencial
    return None

# Función para procesar un solo Sourceid
def process_source_id(session, source_id):
    url = base_url.format(source_id)
    response = get_page(session, url)
    
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        
        if table:
            rows = table.find_all('tr')
            table_data = []
            for row in rows[1:]:  # Saltar el encabezado
                cols = [col.text.strip() for col in row.find_all(['td', 'th'])]
                cols.append(source_id)  # Agregar Sourceid a la fila
                table_data.append(cols)
            
            if table_data and len(table_data[0]) > 2:
                table_df = pd.DataFrame(table_data)
                table_df = table_df.iloc[:, [0, 1, 2, -1]]  # Seleccionar columnas relevantes
                table_df.columns = ['Category', 'Year', 'Quartile', 'Sourceid']
                return table_df
        else:
            print(f"No se encontró ninguna tabla para el ID {source_id}.")
    else:
        print(f"No se pudo obtener la página para el ID {source_id}.")
    return None

# Función para descargar el archivo CSV
def download_csv(url, headers):
    print("Iniciando la descarga del archivo CSV...")
    start_time = time.time()

    # Descargar el archivo CSV con las cabeceras
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Lanzar error si el estado no es 200
        file_path = os.path.join(folder_path, 'journal_internacional_CO.csv')  # Guardar en la carpeta "Revistas"
        with open(file_path, 'wb') as file:
            file.write(response.content)
        
        download_time = time.time() - start_time
        print(f"Archivo CSV descargado y guardado como 'journal_internacional_CO.csv' en {download_time:.2f} segundos.")
        return file_path  # Devolver la ruta del archivo descargado
    except requests.exceptions.RequestException as e:
        print(f"Error al descargar el archivo CSV: {e}")
        return None

# Función para leer el archivo CSV
def read_csv(file_path):
    try:
        with open(file_path, 'r') as file:
            dialect = csv.Sniffer().sniff(file.read(1024))
            file.seek(0)
            ids_df = pd.read_csv(file_path, delimiter=dialect.delimiter)
            return ids_df
    except Exception as e:
        print(f"Error al leer el archivo CSV: {e}")
        return None

# Función para determinar el número óptimo de hilos basado en la carga y el sistema
def determine_optimal_threads(total_ids):
    cpu_cores = 5  # Ajustar según el servidor o la máquina
    base_threads = cpu_cores * 10
    return min(total_ids, base_threads)

# Función principal optimizada con progreso de hilos
def main():
    file_path = download_csv(url, headers)
    if file_path:
        ids_df = read_csv(file_path)

        if ids_df is not None and 'Sourceid' in ids_df.columns:
            all_tables = []
            total_ids = len(ids_df)
            num_workers = determine_optimal_threads(total_ids)
            print(f"Usando {num_workers} hilos para procesamiento.")

            success_count = 0
            failure_count = 0
            completed_count = 0

            start_time_total = time.time()  # Tiempo de inicio total

            # Usamos requests.Session con contexto para asegurarnos de que se cierre correctamente
            with requests.Session() as session:
                # Procesar todos los Sourceid directamente sin dividir en chunks
                with ThreadPoolExecutor(max_workers=num_workers) as executor:
                    futures = {executor.submit(process_source_id, session, source_id): source_id for source_id in ids_df['Sourceid']}
                    total_tasks = len(futures)
                    for future in as_completed(futures):
                        source_id = futures[future]
                        try:
                            table_df = future.result()
                            if table_df is not None:
                                all_tables.append(table_df)
                                success_count += 1
                            else:
                                failure_count += 1
                                print(f"Fracaso en el procesamiento del ID {source_id}")
                        except Exception as e:
                            print(f"Error al procesar el ID {source_id}: {e}")
                            failure_count += 1
                        completed_count += 1
                        print(f"Progreso: {completed_count}/{total_tasks} tareas completadas.")

            elapsed_time_total = time.time() - start_time_total
            print(f"Tiempo total de ejecución: {elapsed_time_total:.2f} segundos. Éxitos: {success_count}, Fracasos: {failure_count}")

            if all_tables:
                combined_df = pd.concat(all_tables, ignore_index=True)
                
                # Guardar como DataFrame en la carpeta "Revistas"
                output_file = os.path.join(folder_path, 'Quartiles.json')
                combined_df.to_json(output_file, orient='records', force_ascii=False, indent=4)
                print(f"Todas las tablas combinadas y guardadas como JSON en: {output_file}")
        else:
            print("No se pudo leer el archivo CSV correctamente o falta 'Sourceid'.")
    else:
        print("No se pudo descargar el archivo CSV.")

# Ejecutar la función principal
main()
