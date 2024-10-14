import json
import pandas as pd
import os

# Ruta del escritorio
desktop_path = r"D:\USUARIO\Desktop"

# Crear una carpeta llamada "Revistas" en el escritorio si no existe
folder_path = os.path.join(desktop_path, "Revistas")
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

# Cargar el primer JSON (Revistas Nacionales) desde la carpeta "Revistas"
with open(os.path.join(folder_path, 'RevistasNacionales.json'), 'r', encoding='utf-8') as f:
    revistas_nacionales = json.load(f)

# Cargar el segundo JSON (Revistas Homologadas) desde la carpeta "Revistas"
with open(os.path.join(folder_path, 'revistas_homologadas.json'), 'r', encoding='utf-8') as f:
    revistas_homologadas = json.load(f)

# Convertir ISSNs a un formato uniforme (sin guiones, espacios, etc.), manejando valores None
def normalizar_issns(issn):
    if issn is None:
        return ""  # Si el ISSN es None, devolver una cadena vacía
    return issn.replace("-", "").replace(" ", "").lower()

# Función para combinar la información de las revistas y eliminar campos duplicados o innecesarios
def combinar_revistas(rev_nac, rev_hom):
    combinadas = []
    issn_usados = set()  # Para evitar agregar duplicados

    # Combinar datos de nacionales con homologadas
    for rev_nacional in rev_nac:
        issns_nacional = set(normalizar_issns(rev_nacional.get("ISSNS", "")).split(","))
        nombre_nacional = rev_nacional.get("txtNombre", "No tiene título")
        
        # Buscar coincidencia en revistas homologadas por ISSNs
        revista_comb = None
        for rev_homologada in rev_hom:
            issns_homologada = set(normalizar_issns(rev_homologada.get("issns", "")).split(","))
            if issns_nacional & issns_homologada:  # Si hay algún ISSN en común
                issn_usados.update(issns_homologada)  # Marcar los ISSNs como usados
                revista_comb = {
                    "ID_REVISTA": rev_nacional.get("ID_REVISTA", rev_homologada.get("id", "No tiene ID")),
                    "NombreRevista": rev_nacional.get("txtNombre", rev_homologada.get("nombreRevista", "No tiene título")),
                    "Direccion": rev_nacional.get("txtDireccion", "No tiene dirección"),
                    "Telefono": rev_nacional.get("txtTelefono", "No tiene teléfono"),
                    "Email": rev_nacional.get("txtEmail", "No tiene email"),
                    "PaginaWeb": rev_nacional.get("txtPaginaWeb", "No tiene página web"),
                    "Instituciones": rev_nacional.get("instituciones", ["No tiene instituciones"]),
                    "Clasificacion": rev_nacional.get("Clasificacion", rev_homologada.get("calificacion", "No tiene clasificación")),
                    "Area": rev_nacional.get("AREA", "No tiene área"),
                    "ISSNS": rev_nacional.get("ISSNS", rev_homologada.get("issns", "No tiene ISSN")),
                    "Vigencia": rev_homologada.get("vigencia", "No tiene vigencia"),
                    "Sires": rev_homologada.get("sires", "No tiene sires")
                }
                break
        
        # Si no se encontró coincidencia, agregar la revista solo con los datos nacionales
        if not revista_comb:
            revista_comb = {
                "ID_REVISTA": rev_nacional.get("ID_REVISTA", "No tiene ID"),
                "NombreRevista": rev_nacional.get("txtNombre", "No tiene título"),
                "Direccion": rev_nacional.get("txtDireccion", "No tiene dirección"),
                "Telefono": rev_nacional.get("txtTelefono", "No tiene teléfono"),
                "Email": rev_nacional.get("txtEmail", "No tiene email"),
                "PaginaWeb": rev_nacional.get("txtPaginaWeb", "No tiene página web"),
                "Instituciones": rev_nacional.get("instituciones", ["No tiene instituciones"]),
                "Clasificacion": rev_nacional.get("Clasificacion", "No tiene clasificación"),
                "Area": rev_nacional.get("AREA", "No tiene área"),
                "ISSNS": rev_nacional.get("ISSNS", "No tiene ISSN"),
                "Vigencia": "No tiene vigencia",
                "Sires": "No tiene sires"
            }
        
        # Agregar la revista combinada a la lista
        combinadas.append(revista_comb)

    # Ahora agregamos las revistas homologadas que no estaban en las nacionales
    for rev_homologada in rev_hom:
        issns_homologada = set(normalizar_issns(rev_homologada.get("issns", "")).split(","))
        if not issns_homologada & issn_usados:  # Si estos ISSNs no se usaron en la combinación
            revista_comb = {
                "ID_REVISTA": rev_homologada.get("id", "No tiene ID"),
                "NombreRevista": rev_homologada.get("nombreRevista", "No tiene título"),
                "Direccion": "No tiene dirección",
                "Telefono": "No tiene teléfono",
                "Email": "No tiene email",
                "PaginaWeb": "No tiene página web",
                "Instituciones": ["No tiene instituciones"],
                "Clasificacion": rev_homologada.get("calificacion", "No tiene clasificación"),
                "Area": "No tiene área",
                "ISSNS": rev_homologada.get("issns", "No tiene ISSN"),
                "Vigencia": rev_homologada.get("vigencia", "No tiene vigencia"),
                "Sires": rev_homologada.get("sires", "No tiene sires")
            }
            combinadas.append(revista_comb)

    return combinadas

# Combinar los datos
revistas_combinadas = combinar_revistas(revistas_nacionales, revistas_homologadas)

# Convertir las revistas combinadas en un DataFrame
df_revistas_combinadas = pd.DataFrame(revistas_combinadas)

# Mostrar las primeras filas del DataFrame para verificar que los datos se han cargado correctamente
print(df_revistas_combinadas.head())

# Guardar el DataFrame en un archivo JSON en la carpeta "Revistas"
output_file = os.path.join(folder_path, 'revistas_publindex.json')
df_revistas_combinadas.to_json(output_file, orient='records', indent=4, force_ascii=False)

print(f"Archivo JSON combinado generado exitosamente: {output_file}")
