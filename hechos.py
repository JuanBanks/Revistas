import pandas as pd
import os

# Directorio donde tienes los archivos de datos de los diferentes años
path = 'D:/USUARIO/Downloads/DatosRevistas/DatosRevistas/Historico todas las revistas SCIMAGO'

# Lista para almacenar todos los DataFrames
dataframes = []

# Año inicial
year = 1999

# Iterar sobre cada archivo CSV en el directorio
for file_name in os.listdir(path):
    if file_name.endswith('.csv'):
        try:
            # Leer el archivo CSV
            df = pd.read_csv(os.path.join(path, file_name), on_bad_lines='skip', delimiter=';', dtype=str)
            
            # Buscar la columna 'Total Docs.' correspondiente al año actual
            total_docs_col = None
            for col in df.columns:
                if col.startswith(f'Total Docs.') and str(year) in col:
                    total_docs_col = col
                    break
            
            # Verificar si la columna fue encontrada
            if not total_docs_col:
                print(f"No se encontró la columna 'Total Docs.' para el año {year} en el archivo {file_name}")
                continue
            
            # Filtrar las columnas 'Sourceid' y 'Total Docs.'
            df_filtered = df[['Sourceid', total_docs_col]].copy()
            df_filtered.rename(columns={total_docs_col: 'Total Docs'}, inplace=True)
            
            # Agregar una nueva columna 'Año' con el valor del año actual
            df_filtered['Año'] = year
            
            # Agregar el DataFrame filtrado a la lista
            dataframes.append(df_filtered)
        except (pd.errors.ParserError, IndexError) as e:
            print(f"Error al procesar el archivo {file_name}: {e}")
        
        # Incrementar el año para el siguiente archivo
        year += 1

# Verificar si hay DataFrames para concatenar
if dataframes:
    # Concatenar todos los DataFrames en uno solo
    tabla_unida = pd.concat(dataframes, ignore_index=True)

    # Guardar la tabla unida en un archivo CSV
    tabla_unida.to_csv('D:/USUARIO/Desktop/tabla_unida_filtered.csv', index=False)

    print("Tabla de hechos unida creada con éxito!")
else:
    print("No se encontraron datos para concatenar.")
