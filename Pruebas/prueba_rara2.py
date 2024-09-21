import re
import csv
import cantools

# Expresión regular proporcionada
pattern = r'(can0\s+)(\d+)\s+\[(\d)\]\s+([A-F0-9\s]+)'

# Cargar la base de datos DBC
db = cantools.database.load_file('./TER.dbc')

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
        dlc = int(match.group(3))
        data= bytearray.fromhex(match.group(4)) 

        # Decodificar el mensaje usando la base de datos DBC
        try:
            message = db.decode_message(dlc, data)
            decoded_data = str(message)  # Convertir el mensaje a string
        except Exception as e:
            decoded_data = f"Error decodificando: {e}"

        # Agregar la fila a la lista de filas con DLC y datos decodificados
        rows.append([dlc, decoded_data])

# Escribir los datos en un archivo CSV
with open('RUN0.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    # Escribir la cabecera
    csvwriter.writerow(['DLC', 'Decoded Data'])
    # Escribir las filas
    csvwriter.writerows(rows)

print("Datos extraídos y guardados en RUN0.csv")
