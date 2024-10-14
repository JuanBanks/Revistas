import os
import pandas as pd
import json

# Ruta del escritorio
desktop_path = r"D:\USUARIO\Desktop"

# Crear una carpeta llamada "Revistas" en el escritorio si no existe
folder_path = os.path.join(desktop_path, "Revistas")
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

# Cargar el archivo CSV (journal_internacional_CO.csv) desde la carpeta "Revistas"
csv_file = os.path.join(folder_path, 'journal_internacional_CO.csv')
df = pd.read_csv(csv_file, delimiter=';')

# Asegúrate de que el archivo se cargue correctamente mostrando las primeras filas
print("Columnas del CSV:", df.columns)
print(df.head())

# Cargar el archivo JSON (resultados_homologadas.json) desde la carpeta "Revistas"
json_file = os.path.join(folder_path, 'resultados_homologadas.json')
with open(json_file, 'r', encoding='utf-8') as f:
    homologated_data = json.load(f)

# Crear un diccionario del JSON donde la clave sea el título (en minúsculas y sin espacios extra) y el valor el estado
homologated_dict = {item['titulo'].strip().lower(): item['estado'] for item in homologated_data}

# Verifica que el CSV tenga la columna correcta para los títulos (ajusta 'Title' según el nombre correcto)
if 'Title' in df.columns:
    title_column = 'Title'
elif 'title' in df.columns:
    title_column = 'title'
else:
    raise KeyError("No se encontró la columna de título en el CSV")

# Normalizar los títulos del CSV en minúsculas y eliminar espacios para facilitar la comparación
df['normalized_title'] = df[title_column].str.strip().str.lower()

# Crear la nueva columna 'open access' basándose en el diccionario homologated_dict
df['open access'] = df['normalized_title'].apply(
    lambda x: 'Sí' if homologated_dict.get(x, 'No es Open Access') == 'Open Access' else 'No'
)

# Eliminar la columna temporal 'normalized_title'
df.drop(columns=['normalized_title'], inplace=True)

# Convertir el DataFrame modificado a JSON y guardarlo en la carpeta "Revistas"
output_json_file = os.path.join(folder_path, 'journal_rank_internacional_con_open_access.json')
df.to_json(output_json_file, orient='records', force_ascii=False, indent=4)

print(f"Nuevo archivo JSON guardado como {output_json_file}")
