import requests
import pandas as pd
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ruta del escritorio
desktop_path = r"D:\USUARIO\Desktop"

# Crear una carpeta llamada "Revistas" en el escritorio si no existe
folder_path = os.path.join(desktop_path, "Revistas")
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

# URL de la API externa para obtener todas las revistas homologadas
url = "https://scienti.minciencias.gov.co/publindex/api/publico/revistasHomologadas"
payload = {}

# Realizamos la solicitud POST para obtener todas las revistas homologadas
print(f"Enviando solicitud a la API para obtener todas las revistas homologadas...")

try:
    response = requests.post(url, json=payload, timeout=30)
    
    # Verificar si la respuesta es vacía o tiene un formato no válido
    if response.status_code == 200 and response.content:
        try:
            data = response.json()  # Intentar decodificar la respuesta a JSON
        except requests.exceptions.JSONDecodeError as e:
            print("Error al decodificar el JSON de la respuesta:", e)
            print("Contenido de la respuesta:", response.text)  # Mostrar contenido
            exit()
    else:
        print(f"Error: Respuesta inválida o vacía. Código de estado: {response.status_code}")
        exit()

except requests.exceptions.RequestException as e:
    print(f"Error en la solicitud: {e}")
    exit()

# Verificamos si la solicitud fue exitosa y si hay datos válidos
if data:
    print(f"Datos recibidos, procesando...")

    # Crear DataFrame desde el JSON
    df = pd.DataFrame(data)

    # Obtener los Ids de las revistas
    if 'id' in df.columns:
        id_revistas = df['id'].tolist()

    if not id_revistas:
        print("No se encontraron IDs de revistas.")
        exit()

    # URL base para obtener detalles de cada revista por su ID
    base_url = "https://scienti.minciencias.gov.co/publindex/api/publico/revistasHomologadas/"
    start_time = time.time()

    # Listas para almacenar los resultados
    basic_info_list = []  # Para "revistas_homologadas.json"
    ids_homologadas = []  # Para consultar clasificaciones completas más tarde
    full_details_by_id = []  # Para "clasificacion_revistas_vigencia_2024.json"
    max_threads = 50  # Ajustable según capacidad de red y servidor

    print("Iniciando la obtención de detalles de las revistas...")

    # Usamos requests.Session para mantener una conexión persistente
    session = requests.Session()

    # Función para obtener detalles de una revista con reintentos
    def get_details(id_revista):
        url = f"{base_url}{id_revista}"
        retries = 3
        for attempt in range(retries):
            try:
                print(f"Obteniendo detalles para ID {id_revista} (Intento {attempt + 1})...")
                response = session.get(url, timeout=30)  # Aumentamos el timeout a 30 segundos
                
                # Verificar si la respuesta tiene contenido
                if response.status_code == 200 and response.content:
                    return response.json()
                else:
                    print(f"Error: Respuesta inválida para ID {id_revista}. Código de estado: {response.status_code}")
                    return None
            except requests.exceptions.RequestException as e:
                print(f"Error al obtener detalles para ID {id_revista}: {e}")
                if attempt < retries - 1:
                    time.sleep(2)  # Retraso antes del próximo intento
                else:
                    return None

    # Usar ThreadPoolExecutor para realizar solicitudes en paralelo
    with ThreadPoolExecutor(max_threads) as executor:
        future_to_id = {executor.submit(get_details, id_revista): id_revista for id_revista in id_revistas}

        for future in as_completed(future_to_id):
            id_revista = future_to_id[future]
            try:
                result = future.result()
                if result is not None:
                    # Verificar si el resultado es una lista o un diccionario
                    if isinstance(result, dict):
                        # Si es un diccionario, procedemos a verificar la vigencia
                        vigencia = result.get('vigencia', "")
                        if "Ene 2024" in vigencia or "Jun 2024" in vigencia:
                            # Guardar los campos solicitados para "revistas_homologadas.json"
                            basic_info = {
                                "id": id_revista,  # Asegurarnos de usar el ID correcto aquí
                                "nombreRevista": result.get('nombreRevista', ""),
                                "calificacion": result.get('calificacion', ""),
                                "vigencia": result.get('vigencia', ""),
                                "sires": result.get('sires', ""),
                                "issns": result.get('issns', "")
                            }
                            # Eliminar las columnas con valores nulos
                            basic_info = {k: v for k, v in basic_info.items() if v}

                            basic_info_list.append(basic_info)

                            # Guardar los IDs que cumplen la condición para luego usarlos en la clasificación
                            ids_homologadas.append(id_revista)

                    elif isinstance(result, list):
                        # Si es una lista, iteramos sobre los elementos de la lista
                        for item in result:
                            vigencia = item.get('vigencia', "")
                            if "Ene 2024" in vigencia or "Jun 2024" in vigencia:
                                # Guardar los campos solicitados para "revistas_homologadas.json"
                                basic_info = {
                                    "id": id_revista,
                                    "nombreRevista": item.get('nombreRevista', ""),
                                    "calificacion": item.get('calificacion', ""),
                                    "vigencia": item.get('vigencia', ""),
                                    "sires": item.get('sires', ""),
                                    "issns": item.get('issns', "")
                                }
                                # Eliminar las columnas con valores nulos
                                basic_info = {k: v for k, v in basic_info.items() if v}

                                basic_info_list.append(basic_info)

                                # Guardar los IDs que cumplen la condición para luego usarlos en la clasificación
                                ids_homologadas.append(id_revista)
            except Exception as e:
                print(f"Error al procesar el resultado para ID {id_revista}: {e}")

    # Crear DataFrame con los detalles básicos para "revistas_homologadas.json"
    basic_info_df = pd.DataFrame(basic_info_list)

    # Guardar los detalles básicos en el archivo JSON "revistas_homologadas.json" en la carpeta "Revistas"
    if not basic_info_df.empty:
        output_file_basic = os.path.join(folder_path, "revistas_homologadas.json")
        basic_info_df.to_json(output_file_basic, orient='records', indent=4, force_ascii=False)  # Guardar como lista de objetos
        print(f"Archivo JSON con detalles básicos generado exitosamente: {output_file_basic}")
    else:
        print("No se encontraron revistas con vigencia Ene 2024 - Jun 2024.")

    # Segunda etapa: Obtener **todos los detalles completos** para los IDs de revistas homologadas
    print("Iniciando la obtención de clasificaciones completas...")

    def get_full_classifications(id_revista):
        url = f"{base_url}{id_revista}"
        retries = 3
        for attempt in range(retries):
            try:
                print(f"Obteniendo clasificaciones para ID {id_revista} (Intento {attempt + 1})...")
                response = session.get(url, timeout=30)  # Aumentamos el timeout a 30 segundos
                
                if response.status_code == 200 and response.content:
                    return response.json()
                else:
                    print(f"Error: Respuesta inválida para ID {id_revista}. Código de estado: {response.status_code}")
                    return None
            except requests.exceptions.RequestException as e:
                print(f"Error al obtener clasificaciones para ID {id_revista}: {e}")
                if attempt < retries - 1:
                    time.sleep(2)  # Retraso antes del próximo intento
                else:
                    return None

    # Usar ThreadPoolExecutor para las consultas de clasificaciones completas
    with ThreadPoolExecutor(max_threads) as executor:
        future_to_id = {executor.submit(get_full_classifications, id_revista): id_revista for id_revista in ids_homologadas}

        for future in as_completed(future_to_id):
            id_revista = future_to_id[future]
            try:
                result = future.result()
                if result is not None:
                    # Asegurarnos de incluir el ID en la respuesta de clasificaciones
                    if isinstance(result, list):
                        for item in result:
                            item['id'] = id_revista  # Añadir el ID a cada registro
                            full_details_by_id.append(item)
                    else:
                        result['id'] = id_revista  # Añadir el ID al registro si no es una lista
                        full_details_by_id.append(result)
            except Exception as e:
                print(f"Error al procesar las clasificaciones para ID {id_revista}: {e}")

    # Crear DataFrame con los detalles completos para "clasificacion_revistas_vigencia_2024.json"
    full_details_df = pd.DataFrame(full_details_by_id)

    # Guardar los detalles completos en el archivo JSON "clasificacion_revistas_vigencia_2024.json" en la carpeta "Revistas"
    if not full_details_df.empty:
        output_file_full = os.path.join(folder_path, "clasificacion_revistas_vigencia_2024.json")
        full_details_df.to_json(output_file_full, orient='records', indent=4, force_ascii=False)
        print(f"Archivo JSON con clasificaciones generado exitosamente: {output_file_full}")
    else:
        print("No se encontraron clasificaciones completas para los IDs homologados.")

    # Finalizar el temporizador
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Tiempo total de ejecución: {elapsed_time:.2f} segundos")

else:
    print("No se encontraron revistas.")
