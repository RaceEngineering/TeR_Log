import re
import csv

# Expresión regular proporcionada
pattern = r'(can0\s+)(\d+)\s+\[(\d)\]\s+([A-F0-9\s]+)'

# Abrir archivo de log para lectura
with open('RUN0.log', 'r') as logfile:
    log_data = logfile.readlines()

# Lista para almacenar las filas que serán escritas en el archivo CSV
rows = []

# Procesar cada línea en el archivo de log
for line in log_data:
    # Buscar coincidencias con la expresión regular
    match = re.search(pattern, line)
    if match:
        # Extraer los grupos capturados
        groups = match.groups()
        # Limpiar los datos capturados (remover espacios adicionales en el grupo de datos)
        timestamp = groups[1]
        dlc = groups[2]
        data = groups[3].strip()
        # Agregar la fila a la lista de filas
        rows.append([timestamp, dlc, data])

# Escribir los datos en un archivo CSV
with open('RUN0.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    # Escribir la cabecera
    csvwriter.writerow(['Timestamp', 'DLC', 'Data'])
    # Escribir las filas
    csvwriter.writerows(rows)

print("Datos extraídos y guardados en RUN0.csv")
