import re
import cantools
import csv
from collections import defaultdict

# Patron regex para encontrar matches
pattern = r'(can0\s+)(\d+)\s+\[(\d)\]\s+([A-F0-9\s]+)'

# Cargar el archivo .dbc
db = cantools.database.load_file("./TER.dbc")

# Abrir en modo lectura el log
with open("RUN0.log", 'r') as file:
    log = file.read()

# Compilar regex
regex = re.compile(pattern)

# Dictionario de mensajes decodificados
grouped_decoded = defaultdict(list)

# Hacer los matches:
for match in regex.finditer(log):
    msg = {
        "data": bytearray.fromhex(match.group(4)),
        "id": int(match.group(2), 16)
    }
    
    # Decodificar con el TER.dbc
    log_decode = db.decode_message(msg["id"], msg["data"])
    
    # Meter todos los values agrupados en cada key
    for key, value in log_decode.items():
        if isinstance(value, (int, float)):
            grouped_decoded[key].append(value)

# Escribir el csv
with open('decoded_log.csv', mode='w', newline='') as csv_file:
    writer = csv.writer(csv_file)

    #Escribir los grupos decodificados en el CSV
    for key, values in grouped_decoded.items():
        writer.writerow([key, values])

print("Guardado y decodificado el log en decoded_log.csv")
