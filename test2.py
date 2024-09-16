import re
import cantools
import json

# Define the pattern to obtain a match in the log
pattern = r'(can0\s+)(\d+)\s+\[(\d)\]\s+([A-F0-9\s]+)'

# Cargar el archivo .dbc
db = cantools.database.load_file("./TER.dbc")

# Open Log File
with open("RUN0.log", 'r') as file:
    log = file.read()

# Compile the regex pattern
regex = re.compile(pattern)

# Crear un diccionario para almacenar los resultados decodificados
log_dic = {}

# Capturar las coincidencias usando `re.finditer`
for match in regex.finditer(log):
    msg = {
        "bus": match.group(1),
        "id": int(match.group(2), 16),
        "DLC": int(match.group(3)),
        "data": bytearray.fromhex(match.group(4))  # Convertir de hexadecimales a bytes
    }
    
    # Decodificar el mensaje
    decoded_message = db.decode_message(msg["id"], msg["data"])
    decoded_message_str = json.dumps(decoded_message)
    
    # Expresión para capturar el nombre de la variable y su valor
    pattern2 = r"'([A-Za-z_]+)':\s*(-?\d+(?:\.\d+)?(?:e-?\d+)?)"
    regex2 = re.compile(pattern2)
    
    # Capturar coincidencias en el mensaje decodificado
    for match2 in regex2.finditer(decoded_message_str):
        variable = match2.group(1)  # Coger nombre de variable
        valor = float(match2.group(2))  # Captura el valor y lo convierte a float
        log_dic[variable] = valor  # Asignar el valor al diccionario

# Imprimir el diccionario resultante
print(log_dic)