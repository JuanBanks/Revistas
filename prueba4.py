import requests
import pandas as pd
import os

# Ruta del escritorio (modifica según el sistema operativo)
desktop_path = r"D:\USUARIO\Desktop"

# Crear una carpeta llamada "Revistas" en el escritorio si no existe
folder_path = os.path.join(desktop_path, "Revistas")
if not os.path.exists(folder_path):
    os.makedirs(folder_path)




# URLs de las distintas categorías
urls = {
    "A1": "https://scienti.minciencias.gov.co/publindex/api/publico/revistasPublindex/categorias/A1",
    "A2": "https://scienti.minciencias.gov.co/publindex/api/publico/revistasPublindex/categorias/A2",
    "B": "https://scienti.minciencias.gov.co/publindex/api/publico/revistasPublindex/categorias/B",
    "C": "https://scienti.minciencias.gov.co/publindex/api/publico/revistasPublindex/categorias/C"
}

# URL para obtener las revistas con AREA e ISSNS
url_nacional = "https://scienti.minciencias.gov.co/publindex/api/publico/revistasPublindex"

# Lista para almacenar los DataFrames de cada categoría
dataframes = []

# Columnas que queremos eliminar
columns_to_exclude = ["txtOrientacionEditorial", "txtInstruccionesAutores", "articulos", "clasificaciones", "issns"]

# Iteramos sobre cada URL y hacemos la solicitud GET para cada categoría
for clasificacion, url in urls.items():
    print(f"Enviando solicitud a la API para obtener las revistas de la categoría {clasificacion}...")

    try:
        # Realizamos la solicitud GET con un timeout de 10 segundos
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Verificar si hubo algún error
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud para la categoría {clasificacion}: {e}")
        continue

    # Verificamos si la solicitud fue exitosa
    if response.status_code == 200:
        # Obtenemos los datos en formato JSON
        data = response.json()

        # Verificamos si se recibieron datos
        if data:
            print(f"Datos recibidos para la categoría {clasificacion}, procesando...")

            # Crear DataFrame desde el JSON
            df = pd.DataFrame(data)

            # Agregamos la columna 'Clasificacion' con la categoría correspondiente
            df['Clasificacion'] = clasificacion

            # Eliminamos las columnas que no queremos incluir en el resultado final
            df = df.drop(columns=columns_to_exclude, errors='ignore')

            # Añadimos el DataFrame a la lista de resultados
            dataframes.append(df)
        else:
            print(f"No se encontraron revistas para la categoría {clasificacion}.")
    else:
        print(f"Error en la solicitud: {response.status_code} para la categoría {clasificacion}")

# Unimos todos los DataFrames en uno solo
if dataframes:
    combined_df = pd.concat(dataframes, ignore_index=True)

    # Renombrar la columna 'id' a 'ID_REVISTA' en el DataFrame combinado
    if 'id' in combined_df.columns:
        combined_df = combined_df.rename(columns={'id': 'ID_REVISTA'})

    # Realizamos la solicitud POST para obtener todas las revistas nacionales
    print(f"Enviando solicitud a la API para obtener todas las revistas nacionales...")

    try:
        # Realizamos la solicitud POST con un timeout de 10 segundos
        response_nacional = requests.post(url_nacional, json={}, timeout=10)
        response_nacional.raise_for_status()  # Verificar si hubo algún error en la solicitud

        # Verificar el contenido de la respuesta
        print("Contenido de la respuesta:", response_nacional.text)  # Mostrar lo que está devolviendo la API

        # Intentamos convertir a JSON
        try:
            data_nacional = response_nacional.json()
        except requests.exceptions.JSONDecodeError:
            print("Error: La respuesta no es un JSON válido.")
            exit()

    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud: {e}")
        exit()

    # Verificamos si se recibieron datos
    if data_nacional:
        print(f"Datos nacionales recibidos, procesando...")

        # Crear DataFrame desde el JSON
        df_nacional = pd.DataFrame(data_nacional)

        # Seleccionamos solo las columnas 'ID_REVISTA', 'AREA', 'ISSNS' si existen
        df_nacional = df_nacional[['ID_REVISTA', 'AREA', 'ISSNS']]

        # Hacemos el merge (combinación) entre el DataFrame combinado y el DataFrame nacional basado en 'ID_REVISTA'
        combined_df = pd.merge(combined_df, df_nacional, on='ID_REVISTA', how='left')

        # Guardar en un archivo JSON en la carpeta "Revistas"
        output_file = os.path.join(folder_path, "RevistasNacionales.json")
        combined_df.to_json(output_file, orient='records', indent=4, force_ascii=False)

        print(f"Archivo JSON generado exitosamente: {output_file}")
    else:
        print("No se encontraron revistas nacionales.")
else:
    print("No se encontraron datos en ninguna de las categorías.")
