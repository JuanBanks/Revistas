import os
import json
import pandas as pd

# Ruta del escritorio
desktop_path = r"D:\USUARIO\Desktop"

# Crear una carpeta llamada "Revistas" en el escritorio si no existe
folder_path = os.path.join(desktop_path, "Revistas")
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

# Función para normalizar los nombres de las revistas (eliminar espacios en blanco y convertir a minúsculas)
def normalizar_nombre(nombre):
    if nombre is None:
        return ""  # Si el nombre es None, devolver una cadena vacía
    return nombre.strip().lower()

# Cargar el archivo JSON de revistas Publindex desde la carpeta "Revistas"
with open(os.path.join(folder_path, 'revistas_publindex.json'), 'r', encoding='utf-8') as f:
    revistas_publindex = json.load(f)

# Cargar el archivo JSON de journal rank internacional desde la carpeta "Revistas"
with open(os.path.join(folder_path, 'journal_rank_internacional_con_open_access.json'), 'r', encoding='utf-8') as f:
    journal_rank = json.load(f)

# Crear un diccionario a partir de journal_rank donde la clave es el Title y el valor es la información del journal
journal_rank_dict = {}
for journal in journal_rank:
    titulo_journal = normalizar_nombre(journal.get('Title', ''))
    if titulo_journal:
        journal_rank_dict[titulo_journal] = journal

# Combinar los datos de revistas_publindex con los de journal_rank
for revista in revistas_publindex:
    titulo_publindex = normalizar_nombre(revista.get('NombreRevista', ''))
    
    journal_info = journal_rank_dict.get(titulo_publindex)

    # Si se encontró información en journal_rank
    if journal_info:
        # Rellenar los campos faltantes en la revista de Publindex con los datos del journal
        revista['Rank'] = journal_info.get('Rank', 'No tiene rank')
        revista['Sourceid'] = journal_info.get('Sourceid', 'No tiene Sourceid')
        revista['SJR'] = journal_info.get('SJR', 'No tiene SJR')
        revista['SJR Best Quartile'] = journal_info.get('SJR Best Quartile', 'No tiene SJR Best Quartile')
        revista['H index'] = journal_info.get('H index', 'No tiene H index')
        revista['Total Docs. (2023)'] = journal_info.get('Total Docs. (2023)', 'No tiene Total Docs. (2023)')
        revista['Total Docs. (3years)'] = journal_info.get('Total Docs. (3years)', 'No tiene Total Docs. (3years)')
        revista['Country'] = journal_info.get('Country', 'No tiene Country')
        revista['Publisher'] = journal_info.get('Publisher', 'Sin editorial')
        revista['Coverage'] = journal_info.get('Coverage', 'No tiene Coverage')
        revista['Categories'] = journal_info.get('Categories', 'No tiene Categories')
        revista['Open Access'] = journal_info.get('open access', 'No es Open Access')
        
        # Si el campo "Area" en Publindex está vacío o dice "No tiene área", rellenarlo con el valor de journal_info
        if revista.get('Area', 'No tiene área') == 'No tiene área' and journal_info.get('Areas', None):
            revista['Area'] = journal_info['Areas']
    else:
        # Si no se encuentra en journal_rank, rellenar los campos con "No tiene"
        revista['Rank'] = 'No tiene rank'
        revista['Sourceid'] = 'No tiene Sourceid'
        revista['SJR'] = 'No tiene SJR'
        revista['SJR Best Quartile'] = 'No tiene SJR Best Quartile'
        revista['H index'] = 'No tiene H index'
        revista['Total Docs. (2023)'] = 'No tiene Total Docs. (2023)'
        revista['Total Docs. (3years)'] = 'No tiene Total Docs. (3years)'
        revista['Country'] = 'No tiene Country'
        revista['Publisher'] = 'Sin editorial'
        revista['Coverage'] = 'No tiene Coverage'
        revista['Categories'] = 'No tiene Categories'
        revista['Open Access'] = 'No es Open Access'

    # Convertir la lista de instituciones a una cadena separada por comas
    if isinstance(revista.get('Instituciones'), list):
        revista['Instituciones'] = ', '.join(revista['Instituciones'])

# Convertir la lista de revistas en un DataFrame
df = pd.DataFrame(revistas_publindex)

# Guardar el DataFrame en un archivo JSON en la carpeta "Revistas"
output_file = os.path.join(folder_path, 'revistas.json')
df.to_json(output_file, orient='records', indent=4, force_ascii=False)

print(f"Archivo JSON combinado generado exitosamente con pandas: {output_file}")
